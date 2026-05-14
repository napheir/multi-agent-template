"""multi-agent-bootstrap CLI entry point.

Subcommands:

    multi-agent-bootstrap new <project_name> [options]
        Cookiecutter-render the template + run bootstrap script + run
        governance-core install. Output directory: <install_root>/<project_name>/

        Options:
            --agents=NAMES           Comma-separated (default: core,data)
            --ritual-phrase=PHRASE   First-line ritual (default: Acknowledged)
            --install-root=DIR       Output parent dir (default: ~/workshop-claude)
            --core-agent-name=NAME   Governance agent (default: core)
            --no-bootstrap           Skip running bootstrap script (template render only)

    multi-agent-bootstrap version
        Print version.

Implementation notes:
- Resolves cookiecutter template path from the multi-agent-template repo
  root (where pyproject.toml lives). Falls back to env var
  MULTI_AGENT_TEMPLATE_DIR if running outside the source tree.
- Calls cookiecutter Python API directly (not subprocess) for cleaner error
  handling and to pass --no-input for unattended use.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def _find_template_root() -> Path:
    """Locate the cookiecutter template root directory."""
    env_dir = os.environ.get("MULTI_AGENT_TEMPLATE_DIR")
    if env_dir:
        p = Path(env_dir).resolve()
        if (p / "cookiecutter.json").is_file():
            return p
    # If installed via `pip install -e`, the package lives at <repo>/mab/
    # so the template root is its parent.
    here = Path(__file__).resolve()
    candidate = here.parent.parent
    if (candidate / "cookiecutter.json").is_file():
        return candidate
    raise FileNotFoundError(
        "Cannot locate multi-agent-template root. "
        "Set MULTI_AGENT_TEMPLATE_DIR env var or pip install -e the repo."
    )


def cmd_new(args: argparse.Namespace) -> int:
    try:
        from cookiecutter.main import cookiecutter
    except ImportError:
        print(
            "[multi-agent-bootstrap] cookiecutter not installed.\n"
            "  pip install cookiecutter",
            file=sys.stderr,
        )
        return 1

    template_root = _find_template_root()
    install_root = Path(os.path.expanduser(args.install_root)).resolve()
    install_root.mkdir(parents=True, exist_ok=True)

    extra = {
        "project_name": args.project_name,
        "agents": args.agents,
        "ritual_phrase": args.ritual_phrase,
        "install_root": str(install_root),
        "core_agent_name": args.core_agent_name,
    }
    print(f"[mab] Rendering cookiecutter to {install_root}/{args.project_name}/")
    project_dir = cookiecutter(
        template=str(template_root),
        no_input=True,
        extra_context=extra,
        output_dir=str(install_root),
        overwrite_if_exists=args.force,
    )
    project_dir = Path(project_dir)
    print(f"[mab] Rendered: {project_dir}")

    if args.no_bootstrap:
        print("[mab] --no-bootstrap given; skipping bootstrap script + governance-core install.")
        return 0

    # Bootstrap directly via Python (avoid PowerShell native JSON quoting issues
    # on Windows; the historic bootstrap.{ps1,sh} scripts are kept for power
    # users but are not invoked by the standard `new` flow). Steps:
    #   1. git init in project_dir if not already a repo
    #   2. Build config_overrides JSON in Python
    #   3. Call `governance-core install --config-overrides <JSON>` via subprocess.run
    #   4. git add + commit (initial)
    import json as _json
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init", "-b", "master"], cwd=project_dir, check=True,
                       capture_output=True)
        print("[mab] git init")

    agents_list = [a.strip() for a in args.agents.split(",") if a.strip()]
    agents_cfg = []
    for a in agents_list:
        branch = "master" if a == args.core_agent_name else f"feature/{a}"
        agents_cfg.append({"name": a, "branch": branch, "clone_dir": f"agent-{a}"})

    install_root = Path(args.install_root).expanduser().resolve()
    overrides = {
        "project_name": args.project_name,
        "install_root": str(install_root),
        "shared_state_root": str(install_root / "shared_state" / args.project_name),
        "ritual_phrase": args.ritual_phrase,
        "core_agent_name": args.core_agent_name,
        "agents": agents_cfg,
    }
    overrides_json = _json.dumps(overrides, ensure_ascii=False)
    print(f"[mab] Calling governance-core install ...")
    r = subprocess.run(
        ["governance-core", "install",
         "--project-root", str(project_dir),
         "--config-overrides", overrides_json,
         "--force"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        print(f"[mab] governance-core install failed (rc={r.returncode})", file=sys.stderr)
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        return r.returncode
    print("[mab] governance-core install OK")

    # Initial commit if anything changed
    st = subprocess.run(["git", "status", "--porcelain"], cwd=project_dir,
                        capture_output=True, text=True)
    if st.stdout.strip():
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-m",
                        f"chore: bootstrap {args.project_name} via multi-agent-template + governance-core"],
                       cwd=project_dir, check=True, capture_output=True)
        print("[mab] Initial commit created")

    print(f"[mab] Done.")
    print(f"[mab] Verify with: governance-core doctor --project-root {project_dir}")
    print(f"[mab] Open in Claude Code: cd {project_dir}/agent-{args.core_agent_name} && claude")
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    from mab import __version__
    print(f"multi-agent-bootstrap {__version__}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="multi-agent-bootstrap")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_new = sub.add_parser("new", help="Create a new multi-agent project")
    p_new.add_argument("project_name", help="Name of the new project")
    p_new.add_argument("--agents", default="core,data",
                       help="Comma-separated agent list (default: core,data)")
    p_new.add_argument("--ritual-phrase", default="Acknowledged",
                       help="First-line session ritual phrase (default: Acknowledged)")
    p_new.add_argument("--install-root", default="~/workshop-claude",
                       help="Output parent directory (default: ~/workshop-claude)")
    p_new.add_argument("--core-agent-name", default="core",
                       help="Governance agent name (default: core)")
    p_new.add_argument("--no-bootstrap", action="store_true",
                       help="Skip bootstrap script + governance-core install")
    p_new.add_argument("--force", action="store_true",
                       help="Overwrite if project_name already exists in install_root")
    p_new.set_defaults(func=cmd_new)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=cmd_version)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

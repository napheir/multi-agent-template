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

    # Run the bootstrap script (PowerShell on Windows, bash elsewhere)
    if platform.system() == "Windows":
        script = template_root / "scripts" / "bootstrap.ps1"
        cmd = ["powershell", "-NoProfile", "-File", str(script),
               "-ProjectRoot", str(project_dir),
               "-Agents", args.agents,
               "-RitualPhrase", args.ritual_phrase]
    else:
        script = template_root / "scripts" / "bootstrap.sh"
        cmd = ["bash", str(script), str(project_dir), args.agents, args.ritual_phrase]
    print(f"[mab] Running: {' '.join(cmd)}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"[mab] bootstrap script returned {r.returncode}", file=sys.stderr)
        return r.returncode

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

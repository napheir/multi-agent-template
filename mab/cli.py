"""multi-agent-bootstrap CLI entry point.

Subcommands:

    multi-agent-bootstrap new <project_name> [options]
        Bootstrap a complete multi-agent Claude Code project: render the
        cookiecutter skeleton, install governance-core, then expand into N
        independent git clones (one per agent, each on its own branch) plus
        a shared_state directory.

        Options:
            --agents=NAMES           Comma-separated (default: core,data)
            --ritual-phrase=PHRASE   First-line ritual (default: Acknowledged)
            --install-root=DIR       Output parent dir (default: ~/workshop-claude)
            --core-agent-name=NAME   Governance agent (default: core)
            --no-clones              Single-directory project only (0.1.0 behavior)
            --no-bootstrap           Render template only; skip install + clones
            --force                  Overwrite if project dir already exists

    multi-agent-bootstrap version
        Print version.

N-clone layout (P-0061):

    <install-root>/<project>/
      agent-<core>/      (master branch)
      agent-<biz-1>/     (feature/<biz-1> branch)
      ...
    <install-root>/<project>/shared_state/
      proposals/_id_ledger.json
      knowledge/
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


def _find_template_root() -> Path:
    """Locate the cookiecutter template root directory."""
    env_dir = os.environ.get("MULTI_AGENT_TEMPLATE_DIR")
    if env_dir:
        p = Path(env_dir).resolve()
        if (p / "cookiecutter.json").is_file():
            return p
    here = Path(__file__).resolve()
    candidate = here.parent.parent
    if (candidate / "cookiecutter.json").is_file():
        return candidate
    raise FileNotFoundError(
        "Cannot locate multi-agent-template root. "
        "Set MULTI_AGENT_TEMPLATE_DIR env var or pip install -e the repo."
    )


def _rmtree_force(path: Path) -> None:
    """Remove a directory tree, handling Windows read-only git pack files."""
    if not path.exists():
        return
    def on_rm_error(func, p, exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onerror=on_rm_error)


def _build_agents_cfg(agents_csv: str, core_agent_name: str) -> list[dict]:
    """Parse --agents into the config.json agents[] structure."""
    agents = [a.strip() for a in agents_csv.split(",") if a.strip()]
    cfg = []
    for a in agents:
        branch = "master" if a == core_agent_name else f"feature/{a}"
        cfg.append({"name": a, "branch": branch, "clone_dir": f"agent-{a}"})
    return cfg


def _render_to_staging(template_root: Path, staging_parent: Path, args) -> Path:
    """cookiecutter-render the skeleton into a staging directory.

    Returns the staging project directory (the rendered project root).
    """
    from cookiecutter.main import cookiecutter

    install_root = Path(os.path.expanduser(args.install_root)).resolve()
    extra = {
        "project_name": args.project_name,
        "agents": args.agents,
        "ritual_phrase": args.ritual_phrase,
        "install_root": str(install_root),
        "core_agent_name": args.core_agent_name,
    }
    rendered = cookiecutter(
        template=str(template_root),
        no_input=True,
        extra_context=extra,
        output_dir=str(staging_parent),
        overwrite_if_exists=True,
    )
    return Path(rendered)


def _install_governance_core(project_dir: Path, args) -> int:
    """Run `governance-core install` against project_dir. Returns exit code."""
    install_root = Path(os.path.expanduser(args.install_root)).resolve()
    agents_cfg = _build_agents_cfg(args.agents, args.core_agent_name)
    overrides = {
        "project_name": args.project_name,
        "install_root": str(install_root),
        "shared_state_root": str(install_root / args.project_name / "shared_state"),
        "ritual_phrase": args.ritual_phrase,
        "core_agent_name": args.core_agent_name,
        "agents": agents_cfg,
    }
    r = subprocess.run(
        ["governance-core", "install",
         "--project-root", str(project_dir),
         "--config-overrides", json.dumps(overrides, ensure_ascii=False),
         "--force"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        print(f"[mab] governance-core install failed (rc={r.returncode})", file=sys.stderr)
        if r.stderr:
            print(r.stderr, file=sys.stderr)
    return r.returncode


def _git(args_list: list[str], cwd: Path, check: bool = True):
    return subprocess.run(["git", *args_list], cwd=cwd, check=check,
                          capture_output=True, text=True)


def _clone_agents(staging: Path, project_dir: Path, args) -> list[Path]:
    """git clone the staging repo once per agent into project_dir/agent-<name>/.

    Each clone: checkout its branch + enable merge.ours driver + drop origin
    remote (staging is deleted afterward).

    Returns list of created clone paths.
    """
    agents_cfg = _build_agents_cfg(args.agents, args.core_agent_name)
    project_dir.mkdir(parents=True, exist_ok=True)
    clones = []
    for a in agents_cfg:
        clone_path = project_dir / a["clone_dir"]
        if clone_path.exists():
            if args.force:
                _rmtree_force(clone_path)
            else:
                print(f"[mab] {clone_path} exists (use --force to overwrite)", file=sys.stderr)
                continue
        _git(["clone", str(staging), str(clone_path)], cwd=project_dir)
        # Branch checkout (core stays on master)
        if a["branch"] != "master":
            _git(["checkout", "-b", a["branch"]], cwd=clone_path)
        # Enable per-branch agent.md merge=ours driver (.gitattributes inherited)
        _git(["config", "merge.ours.driver", "true"], cwd=clone_path)
        # staging is throwaway -- drop the origin remote pointing at it
        _git(["remote", "remove", "origin"], cwd=clone_path, check=False)
        print(f"[mab]   cloned agent-{a['name']} on branch {a['branch']}")
        clones.append(clone_path)
    return clones


def _init_shared_state(args) -> Path:
    """Create <project>/shared_state/ with proposals/_id_ledger.json seed."""
    install_root = Path(os.path.expanduser(args.install_root)).resolve()
    ss = install_root / args.project_name / "shared_state"
    (ss / "proposals").mkdir(parents=True, exist_ok=True)
    (ss / "knowledge").mkdir(parents=True, exist_ok=True)
    ledger = ss / "proposals" / "_id_ledger.json"
    if not ledger.exists():
        ledger.write_text(
            json.dumps({"version": "1.0.0", "next_id": 1, "entries": []}, indent=2),
            encoding="utf-8",
        )
    return ss


def cmd_new(args: argparse.Namespace) -> int:
    try:
        import cookiecutter  # noqa: F401
    except ImportError:
        print("[multi-agent-bootstrap] cookiecutter not installed.\n"
              "  pip install cookiecutter", file=sys.stderr)
        return 1

    template_root = _find_template_root()
    install_root = Path(os.path.expanduser(args.install_root)).resolve()
    install_root.mkdir(parents=True, exist_ok=True)
    project_dir = install_root / args.project_name

    if project_dir.exists() and not args.force:
        print(f"[mab] {project_dir} already exists (use --force to overwrite)", file=sys.stderr)
        return 1

    # --- Step 1: render to a staging directory ---
    staging_parent = Path(tempfile.mkdtemp(prefix="mab-stage-"))
    try:
        print(f"[mab] Rendering cookiecutter skeleton ...")
        staging = _render_to_staging(template_root, staging_parent, args)
        print(f"[mab] Rendered staging: {staging}")

        if args.no_bootstrap:
            # Just move the rendered skeleton to the final location, no install/clones.
            if project_dir.exists():
                _rmtree_force(project_dir)
            shutil.move(str(staging), str(project_dir))
            print(f"[mab] --no-bootstrap: skeleton at {project_dir} (no install, no clones)")
            return 0

        # --- Step 2: governance-core install in staging ---
        print(f"[mab] Running governance-core install in staging ...")
        rc = _install_governance_core(staging, args)
        if rc != 0:
            return rc
        print(f"[mab] governance-core install OK")

        # --- Step 3: git init + initial commit in staging ---
        if not (staging / ".git").exists():
            _git(["init", "-b", "master"], cwd=staging)
        _git(["add", "-A"], cwd=staging)
        _git(["commit", "-m",
              f"chore: bootstrap {args.project_name} via multi-agent-template + governance-core"],
             cwd=staging)
        print(f"[mab] Staging repo committed")

        # --- single-dir fallback (--no-clones) ---
        if args.no_clones:
            if project_dir.exists():
                _rmtree_force(project_dir)
            shutil.move(str(staging), str(project_dir))
            staging = None  # moved; nothing to clean
            print(f"[mab] --no-clones: single-directory project at {project_dir}")
            _init_shared_state(args)
            print(f"[mab] Done. Verify: governance-core doctor --project-root {project_dir}")
            return 0

        # --- Step 4: clone N agents ---
        print(f"[mab] Cloning agents ...")
        clones = _clone_agents(staging, project_dir, args)
        if not clones:
            print("[mab] No clones created", file=sys.stderr)
            return 1

        # --- Step 5: shared_state init ---
        ss = _init_shared_state(args)
        print(f"[mab] shared_state initialized: {ss}")

    finally:
        # --- Step 6: delete staging ---
        if staging_parent.exists():
            _rmtree_force(staging_parent)

    # --- Step 7: next-step hints ---
    core_clone = project_dir / f"agent-{args.core_agent_name}"
    print(f"[mab] Done. Created {len(clones)} agent clones under {project_dir}")
    print(f"[mab] Verify: governance-core doctor --project-root {core_clone}")
    print(f"[mab] Open in Claude Code: cd {core_clone} && claude")
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
    p_new.add_argument("--no-clones", action="store_true",
                       help="Single-directory project only (skip N-clone expansion)")
    p_new.add_argument("--no-bootstrap", action="store_true",
                       help="Render template only; skip governance-core install + clones")
    p_new.add_argument("--force", action="store_true",
                       help="Overwrite if project dir already exists")
    p_new.set_defaults(func=cmd_new)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=cmd_version)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

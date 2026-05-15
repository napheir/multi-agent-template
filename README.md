# multi-agent-template

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Cookiecutter template + bootstrap CLI for new multi-agent Claude Code projects.**

Generates a fresh multi-agent project pre-wired with the
[governance-core](https://github.com/napheir/governance-core) package —
safety hooks, proposal workflow, wrap-up discipline, constitution iteration,
cross-clone sync.

## One-line bootstrap

```bash
# One-time setup (per machine)
pip install cookiecutter
pip install governance-core
pip install multi-agent-bootstrap

# Bootstrap a new project
multi-agent-bootstrap new my-project \
    --agents core,data \
    --ritual-phrase "Acknowledged"

# Open in Claude Code
cd ~/workshop-claude/my-project/agent-core
claude
```

Output:

```
~/workshop-claude/my-project/
├── agent-core/                 (master branch; governance role)
│   ├── .claude/                (50+ hooks/skills/commands/agents)
│   ├── .governance/            (config.json + 17 clauses + keywords)
│   ├── CLAUDE.md               (project constitution — business clauses
│                                inherit governance clauses)
│   ├── constitution/           (total.md + per-agent agent.md)
│   ├── contracts/              (proposal/knowledge schemas)
│   ├── knowledge/              (governance docs + your project docs)
│   ├── tools/                  (31 generic governance tools)
│   └── agent_rules/            (scope allow/deny)
├── agent-data/                 (feature/data branch)
├── shared_state/               (per-project; outside all clones)
│   └── proposals/              (cross-clone shared runtime state)
└── ...
```

See [docs/getting-started.md](docs/getting-started.md) for the complete
walkthrough.

## CLI reference

```
multi-agent-bootstrap new <project_name> [options]

Options:
    --agents=NAMES            Comma-separated agent list (default: core,data)
    --ritual-phrase=PHRASE    First-line session ritual (default: Acknowledged)
    --install-root=DIR        Output parent dir (default: ~/workshop-claude)
    --core-agent-name=NAME    Governance agent name (default: core)
    --no-bootstrap            Skip bootstrap script + governance-core install
    --force                   Overwrite if project_name already exists
```

## How it works

1. **cookiecutter render**: The `{{cookiecutter.project_name}}/` directory
   contains a skeleton with `{{ cookiecutter.* }}` placeholders. `mab/cli.py`
   calls cookiecutter's Python API to substitute your inputs.
2. **bootstrap script**: After rendering, `mab/cli.py` runs `git init` in
   the new project + calls `governance-core install` (directly via Python
   subprocess; avoids historical PowerShell JSON quoting issues).
3. **governance-core install**: Renders 17 constitution clauses with your
   ritual phrase substituted, copies 14 hooks + 7 commands + 22 skills + 2
   agents to `.claude/`, writes 31 tools, sets up `.gitattributes`
   `merge=ours` for per-branch `constitution/agent.md` isolation.
4. **Initial commit**: `mab/cli.py` does `git add -A` + commits.

Result: a complete multi-agent governance scaffold in ~5 seconds.

## Customization

After bootstrap, your project's `.governance/config.json` controls:

- `project_name`, `install_root`, `shared_state_root`, `claude_dir`
- `core_agent_name`, `core_branches`, `ritual_phrase`
- `agents[]` with name/branch/clone_dir per agent
- `upstream_branch`, `constitution_layout`

To add a new business agent later, edit `agents[]` + run
`governance-core upgrade --project-root .` to refresh.

## Project status

**v0.1.0-alpha** (2026-05). API may break between minor versions.

## License

MIT — see [LICENSE](LICENSE).

## Related

- [governance-core](https://github.com/napheir/governance-core) — the
  governance package this template installs

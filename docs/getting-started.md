# Getting Started — multi-agent-template + governance-core

This guide bootstraps a new multi-agent Claude Code project in under 5 minutes.

## Prerequisites

- Python 3.11+ (`python --version` confirms)
- Git
- (Optional) `uv` / `uvx` for one-shot CLI invocation
- A Claude Code installation (`claude --version` confirms)

## Path layout

This template assumes all your multi-agent projects live under one root:

```
~/workshop-claude/                          (Windows: C:\Users\<username>\workshop-claude\)
  ├── governance-core/                      (cloned once, shared across all projects)
  ├── multi-agent-template/                 (cloned once, source of bootstrap CLI)
  ├── shared_state/                         (auto-created; cross-clone runtime state)
  └── <my-project>/                         (your projects, one dir each)
      ├── agent-core/                       (master branch; governance role)
      ├── agent-<business>/                 (one per agent in cookiecutter list)
      └── ...
```

## One-time setup (per machine)

```pwsh
# 1. Create workshop directory
mkdir -p ~/workshop-claude
cd ~/workshop-claude

# 2. Clone both source repos (URLs TBD — Phase 3 doesn't yet publish to GitHub)
git clone <governance-core-url> governance-core
git clone <multi-agent-template-url> multi-agent-template

# 3. Install governance-core pip package (editable, so upgrades work)
pip install -e ./governance-core

# 4. Install multi-agent-bootstrap CLI from template (editable)
pip install -e ./multi-agent-template

# 5. Verify
governance-core version          # -> governance-core 0.1.0a0
multi-agent-bootstrap version    # -> multi-agent-bootstrap 0.1.0a0
```

## Create a new project (per project, one-shot)

```pwsh
multi-agent-bootstrap new my-new-project \
    --agents core,data \
    --ritual-phrase "收到" \
    --install-root ~/workshop-claude
```

What happens:

1. **Cookiecutter renders** the skeleton to
   `~/workshop-claude/my-new-project/` with `project_name`, agents,
   ritual phrase, install root substituted into all template files.
2. **bootstrap.{ps1,sh}** runs in the new directory:
   - `git init` if not already a repo
   - Calls `governance-core install --project-root <project>` which:
     - Writes `.governance/config.json` with your overrides
     - Copies hooks/skills/commands/agents/contracts/tools from
       governance-core package to project's `.claude/` + `tools/` etc.
     - Renders 17 clauses to `.governance/clauses/`
     - Configures `.gitattributes` `merge=ours` for per-branch
       `constitution/agent.md`
   - Initial git commit on master branch
3. **Output paths** displayed: where to `cd` + `claude` to start.

## Verify the project

```pwsh
cd ~/workshop-claude/my-new-project
governance-core doctor --project-root .
# Expected: [doctor] OK: project=my-new-project ritual_phrase=收到 agents=2 hooks=N clauses=17
```

## Upgrade governance-core later

Generic clauses, hooks, skills evolve. To pull upstream improvements:

```pwsh
cd ~/workshop-claude/governance-core
git pull
pip install -e . --upgrade

# Then in each project that uses it
cd ~/workshop-claude/my-new-project
governance-core upgrade --project-root .
# Preserves .governance/config.json (your project's settings) but refreshes
# clauses + hooks/skills.
```

## Cross-machine portability

This setup is portable across machines because:

- Paths use `~/workshop-claude/` (Windows resolves to `C:\Users\<username>\workshop-claude\`)
- All config goes into `.governance/config.json` (per-project; not hardcoded)
- `governance-core` is pip-installable; no system-wide assumptions
- The bootstrap CLI accepts `--install-root` override if you prefer a
  different root

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `cookiecutter not installed` | base Python missing cookiecutter | `pip install cookiecutter` |
| `governance-core: command not found` | not on PATH | reinstall: `pip install -e ./governance-core` |
| `bootstrap script exits 2 (not implemented)` | Using stale Phase 1.1 scripts | clone latest `multi-agent-template` |
| `boundary-guard BLOCKED` in Claude session | session started outside project root | open a NEW Claude session from `~/workshop-claude/<project>/agent-core/` |

## Phase 3 status

This guide is the Phase 3 (P-0059) deliverable. As of 2026-05-14:

- ✅ governance-core 0.1.0a0 — pip-installable, full CLI
  (install / upgrade / doctor / render-clauses / version)
- ✅ multi-agent-template — cookiecutter render + bootstrap scripts
- ✅ multi-agent-bootstrap 0.1.0a0 CLI — `new <project>` subcommand
- ⏳ PyPI publication (currently editable-install only)
- ⏳ GitHub repo URLs (currently local-only)

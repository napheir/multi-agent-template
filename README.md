# multi-agent-template

Cookiecutter template for bootstrapping a new multi-agent Claude Code project
with governance pre-installed.

**Status**: 0.1.0-alpha (P-0059 Phase 1 in-progress, not yet bootstrappable).

## What this generates

```
~/workshop-claude/<project_name>/
  ├── agent-core/         (master, governance-core injected via pip)
  ├── agent-<business>/   (one per agent in cookiecutter agents list)
  ├── .governance/        (config.json + clauses/, installed by governance-core)
  └── ...
~/workshop-claude/shared_state/<project_name>/
  └── proposals/ knowledge/ ... (cross-clone shared runtime state, not in any git)
```

The default agents list is `[core, data]` — business agents like `rules` /
`trade` / `research` are **not** preset to avoid polluting new project
namespaces. Add via `--agents core,data,foo,bar` at bootstrap time.

## Usage (Phase 3 will provide)

```pwsh
multi-agent-bootstrap new my-new-project
  # ? project_name: my-new-project
  # ? agents: [core, data]
  # ? ritual_phrase: 收到
  # ? install_root: ~/workshop-claude
```

## Companion package

This template + `governance-core` pip package form a two-piece distribution:

- Template: project skeleton (this repo)
- Package: governance implementation layer (`governance-core` pip)

The template's `cookiecutter.json` is intentionally **not** version-pinned to
`governance-core` — downstream projects `pip install --upgrade` independently.

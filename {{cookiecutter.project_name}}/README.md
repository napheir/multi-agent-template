# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

Bootstrapped via [multi-agent-template](https://github.com/...) on
2026-05-14 (bootstrap date — replace if needed).

## Agent topology

Agents: `{{ cookiecutter.agents }}`

Each agent has its own clone under `{{ cookiecutter.install_root }}/{{ cookiecutter.project_name }}/agent-<name>/`,
working on its own branch. Shared runtime state lives outside any clone at
`{{ cookiecutter.install_root }}/shared_state/{{ cookiecutter.project_name }}/`.

## Quickstart

```pwsh
cd {{ cookiecutter.install_root }}/{{ cookiecutter.project_name }}/agent-{{ cookiecutter.core_agent_name }}
claude
```

## Governance

This project inherits the generic governance clauses from `governance-core`
(see `.governance/clauses/`). Project-specific (business) clauses live in
`CLAUDE.md` at the top of each clone.

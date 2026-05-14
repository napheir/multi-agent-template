# {{ cookiecutter.project_name }} Constitution

> First-line ritual: **{{ cookiecutter.ritual_phrase }}**.
> Project agents: {{ cookiecutter.agents }}.

## Inheritance

This project inherits the generic governance clauses from `governance-core`
(installed via `pip install governance-core` + `governance-core install`).
Generic clauses are rendered into `.governance/clauses/art_*.md` and are the
authoritative source for all governance rules (proposal flow, scope enforcement,
hook safety, constitution iteration, wrap-up discipline, memory staleness,
etc.).

This file (`CLAUDE.md`) contains only the **project-specific (business)**
clauses below. When generic and business clauses conflict, generic wins.

---

## Project-specific Clauses

<!-- Add business-specific clauses below. See `.governance/clauses/` for the
     generic clause numbering scheme; project clauses should use letters
     (Art.A, Art.B, ...) or start from Art.100 to avoid collision. -->

### Art.A: Project Architecture

<Describe the project's domain and data flow here.>

### Art.B: Project-specific Constraints

<Add any project-only rules that don't generalize.>

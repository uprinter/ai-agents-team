# Codex agent-team port

Codex automatically discovers the nine project-scoped custom agents in
`agents/` when this repository is the active project. No absolute
`config_file` entries or global `~/.codex/config.toml` changes are required.
Multi-agent support and `agents.enabled` are on by default; a user who has
explicitly disabled agents must re-enable them before using the coordinator.

Each standalone TOML file defines the three required Codex fields: `name`,
`description`, and `developer_instructions`. Role-specific model,
reasoning-effort, and sandbox settings are included in the same file.

## Source and generation

`.claude/agents/*.md` is the source of truth for role prompts.
`.codex/sync-agents.py` adds concise Codex discovery metadata, the Codex
runtime vocabulary note, and the coordinator's Codex-specific operating mode.
Do not edit generated TOML files directly.

After changing a source agent or Codex profile metadata, run:

```sh
.codex/sync-agents.py
.codex/sync-agents.py --check
```

`--check` validates the freshly rendered TOML and required fields, then
byte-compares that output with the generated files. It also checks
source/profile coverage, rejects unexpected generated files, and fails on
drift.

## Permissions

`code-reviewer` is read-only. Roles whose contracts require authoring specs,
plans, process records, code, infrastructure, research artifacts, or draft
batches use `workspace-write`. A spawned agent still operates within the
parent session's live sandbox and approval policy; these project profiles do
not grant access outside it.

The Claude `skills:` frontmatter is not copied. Codex discovers the same
repository skills from `.agents/skills/`, including supported symlinked skill
folders.

## GitLab access

Before any GitLab API or authenticated Git transport operation, load and follow
`gitlab-access` from `.agents/skills/gitlab-access/SKILL.md`. Claude preloads
the same skill, and generated OpenCode agents load it with their other declared
skills. Codex loads its conditional runtime reference only when Codex-specific
permission or keyring handling is needed.

## Model mapping

| Claude model | Codex mapping |
| --- | --- |
| `opus` | `gpt-5.6-sol` at the role's configured effort |
| `sonnet` | `gpt-5.6-sol` at the role's configured effort |

Open Codex in this repository and ask it to spawn a named agent, or ask for
`team-lead-coordinator` when the work needs multi-role delivery coordination.

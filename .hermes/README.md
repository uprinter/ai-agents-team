# Hermes agent-team port

Hermes has no project-scoped agent files; its unit of "agent" is a profile
(own `SOUL.md`, config, memory, sessions). Each `.claude/agents/<name>.md`
becomes a profile distribution in `profiles/<name>/`: a `distribution.yaml`
manifest and a `SOUL.md` holding the agent prompt verbatim, behind a short
Hermes vocabulary map and a "load these skills" block.

## Source and generation

`.claude/agents/*.md` is the source of truth. Do not edit generated files.
After changing a source agent, run:

```sh
.hermes/sync-agents.py
.hermes/sync-agents.py --check
```

`--check` fails on stale, missing, or unexpected generated files.

## Skills

No port needed. Hermes loads `.agents/skills/` of a git root listed in
`skills.trusted_project_dirs`, so run once from this repository:

```sh
hermes skills trust
```

## Using an agent

```sh
hermes profile install .hermes/profiles/code-reviewer
hermes -p code-reviewer chat        # from inside this repository
```

Install ships only `SOUL.md` and the manifest (`distribution_owned`); model,
provider, toolsets, memory and credentials stay the user's. `hermes profile
update` refreshes `SOUL.md` without touching them.

## Limits

- `delegate_task` runs a named profile only through the `advanced-delegation`
  plugin: set `delegation.backend: profile_routes` and list each profile under
  `delegation.backends.profile_routes`. A listed profile lends its credentials
  and terminal policy to the delegating agent, so list only profiles you trust.
  Without that route, a coordinator delegates with "Act as `<agent-name>`: read
  its `SOUL.md` first" in the goal; the vocabulary map in each `SOUL.md` says so.
- No shared task list, mailbox, or Agent Teams: the one-shot fallback applies.
- The source tool allowlist and model are not mapped, so read-only roles such
  as `code-reviewer` are not sandboxed by the port; restrict toolsets in the
  profile's own config if needed.
- Hermes truncates context files at 20K characters on small context windows;
  the larger agent prompts need a window big enough for the dynamic cap, or
  `context_file_max_chars` set in the profile config.

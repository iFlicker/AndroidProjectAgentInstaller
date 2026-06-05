---
name: AndroidProjectAgentsInstaller
description: Install the ProjectAgents Android AI guidance template into a target Android repository, merge safely with existing AGENTS/CLAUDE/ProjectAgents docs, perform a first-pass project review to fill placeholders from real modules, flavors, resource prefixes, and build structure, and then remind the user to close the skill so it does not keep getting auto-invoked by semantic matching. Use when Codex needs to bootstrap or refresh shared agent guidance in an Android project without clobbering existing documentation.
---

# Android Project Agents Installer

Install the seed docs first, then finish the project review before claiming the onboarding is complete.

## Workflow

1. Treat the user's current Android repo as the target unless they provided another path.
2. Run:

```bash
python3 /absolute/path/to/AndroidProjectAgentsInstaller/scripts/install_project_agents.py --project-root /path/to/android/project
```

3. Read `ProjectAgents/references/project-agents-onboarding-review.md`.
4. Resolve every follow-up item the script leaves behind:
   - review every `TODO(` item against the real project structure
   - merge every `.incoming.md` file into the existing docs or explicitly decide to keep the existing file
   - verify shell module, main module, common module, flavors, sourceSets, resource prefixes, service/router layer, and high-risk modules
5. Fold confirmed stable facts back into `ProjectAgents/ProjectAgents.md` and the relevant `ProjectAgents/references/*.md` files.
6. Leave `ProjectAgents/CHANGELOG.md` updated with the onboarding work.
7. Prompt the user to close or disable this skill after installation. Explain that leaving it enabled may cause accidental auto-invocation in later semantic skill-matching flows.

## Compatibility Rules

- Never replace an existing `AGENTS.md` or `CLAUDE.md` wholesale. The installer only appends a managed pointer block when those files already exist.
- If an existing `ProjectAgents/*.md` file still contains template placeholders, let the installer fill it in place.
- If an existing `ProjectAgents/*.md` file already contains custom content, keep it untouched and use the generated `.incoming.md` file as the merge candidate.
- Do not delete user-authored docs unless the user explicitly asks for cleanup.

## Review Focus

Confirm these areas manually when the script confidence is not high enough:

- main app module, app shell module, common/shared module, UI component module
- flavors, product variants, brand packages, `src/*` sourceSet overrides
- service contracts, routers, service discovery, event bus or message bus
- history-heavy modules, AAR/source switching, loader modules, generated-code boundaries
- module-local `AGENTS.md` / `CLAUDE.md` files that should be referenced in the shared guidance
- resource naming prefixes, common extension files, utility files, and base page classes

## Resources

- `assets/template/`: the seed ProjectAgents docs copied into target repos
- `scripts/install_project_agents.py`: installer, compatibility handler, and first-pass review generator

# Gemini CLI Prompt: Bilingual Documentation Clone

Use this prompt in `gemini-cli` when you want to create or synchronize Czech documentation clones for Markdown docs in this repository.

```text
Act as a bilingual documentation migration assistant for this repository.

Goal:
Every documentation file must have a Czech clone alongside the primary file.

Naming convention:
- README.md -> README.cz.md
- MANUAL.md -> MANUAL.cz.md
- API_DOCUMENTATION.md -> API_DOCUMENTATION.cz.md
- ARCHITECTURE.md -> ARCHITECTURE.cz.md
- etc.

Rules:
1. Keep the original primary file unchanged.
2. For every selected documentation file, create a Czech counterpart in the same directory with the `.cz.md` suffix before `.md`.
3. Preserve:
   - markdown structure
   - headings hierarchy
   - code blocks
   - links
   - tables
   - filenames and paths inside code examples unless translation is clearly needed
4. Translate human-readable prose into natural Czech.
5. Keep technical identifiers, API names, env vars, commands, ports, endpoints, model names, filenames, and product names unchanged.
6. Do not translate:
   - code
   - shell commands
   - JSON keys
   - YAML keys
   - URLs
   - environment variables
   - tool names
7. If a document is already mixed Czech/English, normalize it into clean Czech while preserving technical meaning.
8. Use consistent terminology:
   - deployment = nasazeni
   - troubleshooting = reseni problemu
   - architecture = architektura
   - operations = provoz
   - monitoring = monitoring
   - security = bezpecnost
   - archive = archiv
9. Keep tone professional and technical, not marketing.
10. If a sentence is ambiguous, prefer literal technical accuracy over stylistic freedom.

Workflow:
1. Scan the repository for documentation files (`*.md`) under root and `docs/`.
2. Ignore:
   - `node_modules`
   - `.git`
   - generated caches
3. For each documentation file that does not already have a Czech clone, create one.
4. If a Czech clone already exists, compare it with the source and update it to match the current English source structure and content.
5. At the end, print:
   - which files were cloned
   - which files were updated
   - which files were skipped
   - any files that need human review

Important:
This is a translation-and-sync task, not a rewrite. Keep content aligned 1:1 with the source document unless a small Czech wording adjustment is needed for clarity.
```

## Optional Scope Add-on

Append this when you want Gemini to stay only in docs:

```text
Scope only:
- /docs
- /README.md
Do not touch application code.
```

# Cursor — deutsch-prepositions-fa rule

`cursor/deutsch-prepositions-fa.mdc` is the Cursor version of this skill. It carries
the same contract in condensed form: never guess a preposition or a case (look it up
with the tool), apply the Wechsel Wo/Wohin rule, use time prepositions and da-compounds
correctly, and check learner sentences conservatively.

## Install — Cursor

Copy `cursor/deutsch-prepositions-fa.mdc` into your project's `.cursor/rules/`
directory (create it if needed). Cursor applies it automatically. The
rule points at the engine script — copy the whole
`skills/deutsch-prepositions-fa/` directory into your project, or install the
engine where the rule's commands can find it.

## Install — Windsurf

Copy `cursor/deutsch-prepositions-fa.mdc` to `.windsurf/rules/deutsch-prepositions-fa.mdc`
in your project. Windsurf loads `.mdc` rules from that directory. Copy
`skills/deutsch-prepositions-fa/` alongside it so the script paths resolve.

## Install — Cline / Continue

Cline and Continue use plain Markdown rules:

- **Cline:** copy the contents of `cursor/deutsch-prepositions-fa.mdc` (without the
  frontmatter block) into `.clinerules/deutsch-prepositions-fa.md`, and copy
  `skills/deutsch-prepositions-fa/` into your project.
- **Continue:** copy the same Markdown body into
  `.continue/rules/deutsch-prepositions-fa.md`, and copy `skills/deutsch-prepositions-fa/`
  into your project.

In both cases the rule's commands assume the engine lives at
`skills/deutsch-prepositions-fa/scripts/prepositions.py` relative to the project
root — keep that layout.

## What it covers

- The no-guessing contract (look up the verb's preposition, not from memory).
- The 9 Wechsel prepositions (Wo? → Dativ, Wohin? → Akkusativ) and the
  correct articles.
- Time prepositions (am/im/um), nach vs zu, da-compounds, contractions.
- Conservative sentence checking (DPR-01..DPR-06) — and the "no finding ≠ correct"
  rule.
- Quiz drills and Anki export (92 verb cards + 18 Wechsel + time + da-compound cards).
- The limits (A1–B1 list is not a dictionary; reference, not a teacher).

The full skill with references and the MCP server lives in
`skills/deutsch-prepositions-fa/` and `mcp-server/`.

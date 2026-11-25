# deutsch-prepositions-fa — German prepositions for Persian speakers

A deterministic **Agent Skill** for the part of German grammar that
Persian speakers trip over daily: prepositions. After
[`deutsch-fa`](https://github.com/mohammad-abbasi-sh/deutsch-fa)
(der/die/das + 4 cases),
[`deutsch-verbs-fa`](https://github.com/mohammad-abbasi-sh/deutsch-verbs-fa)
(conjugation) and
[`deutsch-word-order-fa`](https://github.com/mohammad-abbasi-sh/deutsch-word-order-fa)
(word order), this is the fourth pillar — *warten auf* vs *warten für*,
*nach Berlin* vs *zu Berlin*, *am Montag* vs *in Montag*, and the nine
Wechsel prepositions that change case with Wo/Wohin.

Persian has one word, «در» / «به», where German has a whole system: every
preposition governs a case, nine of them switch case by Wo/Wohin, verbs
each demand their own preposition, and time runs on `am`/`im`/`um` by a
fixed rule. `deutsch-prepositions-fa` makes every choice
**deterministic**: a zero-dependency Python engine plus a hand-checked
A1–B1 table (38 prepositions, 92 verb+preposition entries with Persian
glosses), with every explanation in Persian.

No model calls. No downloads. No API keys. Python 3.8+ standard library
only.

## The problem

```
Learner writes:   Ich warte für dich.    /  Ich fahre zu Berlin.
Agent (guessing): looks fine ✓           ← wrong twice, and now the
                                           learner memorizes both errors

With deutsch-prepositions-fa:
$ python3 scripts/prepositions.py check "Ich warte für dich."
✗ [DPR-01] «warten» با «auf» + Akk می‌آید، نه «für».
  درستش: Ich warte auf dich.

$ python3 scripts/prepositions.py check "Ich fahre zu Berlin."
✗ [DPR-02] شهر و کشور بدون حرف تعریف با «nach» می‌آید، نه «zu».
  درستش: Ich fahre nach Berlin.
```

Before/after, from the engine:

| Before (guessed) | After (deutsch-prepositions-fa) |
|---|---|
| *Ich warte für dich* | *Ich warte **auf** dich* — warten takes auf + Akk |
| *Ich fahre zu Berlin* | *Ich fahre **nach** Berlin* — bare city → nach |
| *Ich gehe nach dem Arzt* | *Ich gehe **zum** Arzt* — person/place → zu |
| *Ich komme in Montag* | *Ich komme **am** Montag* — weekdays → am |
| *Der Kurs beginnt am 8 Uhr* | *Der Kurs beginnt **um** 8 Uhr* — clock time → um |
| *Ich stelle das Buch auf dem Tisch* | *Ich stelle das Buch auf **den** Tisch* — Wohin → Akk |
| *Er sitzt in das Zimmer* | *Er sitzt **im** Zimmer* — Wo → Dat |
| *Ich denke an es* | *Ich denke **daran*** — thing → da-compound |
| *Ich warte dich* | *Ich warte **auf** dich* — missing preposition |

## What's inside

```
skills/deutsch-prepositions-fa/
  SKILL.md                     the agent skill (the contract)
  scripts/prepositions.py      the engine — lookup, prep, wechsel, check, fix, quiz, anki
  data/prepositions.json       38 prepositions + 92 verb+preposition entries (hand-checked)
  references/
    preposition-tables.md      the four case groups, Wechsel, contractions, da-/wo-
    persian-traps.md           Persian-interference errors (nach/zu, seit/vor, auf/über)
cursor/deutsch-prepositions-fa.mdc  the Cursor rule (same contract, condensed)
mcp-server/                    MCP server (stdio) exposing 7 tools
tests/                         89 tests, all passing (stdlib unittest)
dist/deutsch-prepositions-fa-skill.zip  ready-to-upload Claude.ai skill bundle
```

Commands:

```bash
python3 scripts/prepositions.py lookup warten
python3 scripts/prepositions.py lookup "sich freuen"   # auf / über / für — three meanings
python3 scripts/prepositions.py prep auf
python3 scripts/prepositions.py wechsel in wohin        # → Akkusativ, den/die/das
python3 scripts/prepositions.py contract im              # im = in + dem
python3 scripts/prepositions.py da an                   # an + es → daran
python3 scripts/prepositions.py check "Ich warte für dich."
python3 scripts/prepositions.py fix "Ich stelle das Buch auf dem Tisch."
python3 scripts/prepositions.py quiz --n 5 --level A1 --seed 42
python3 scripts/prepositions.py anki --kind verbs --out cards.tsv   # 92 cards
python3 scripts/prepositions.py anki --kind wechsel --out wechsel.tsv
python3 scripts/prepositions.py list --group wechsel
```

## Install

**Claude Code** — copy `skills/deutsch-prepositions-fa/` into your project's
skills directory (or `~/.claude/skills/` for global use). The skill's
`SKILL.md` frontmatter makes it discoverable; the script path in the
commands is relative to the skill directory.

**Claude.ai** — upload `dist/deutsch-prepositions-fa-skill.zip` as a skill (the
zip contains `SKILL.md`, the script, the data and the references).

**Cursor** — copy `cursor/deutsch-prepositions-fa.mdc` to `.cursor/rules/` and
`skills/deutsch-prepositions-fa/` into your project. Windsurf / Cline /
Continue: see `cursor/README.md`.

**Any MCP client** — point your client at the stdio server:

```json
{
  "mcpServers": {
    "deutsch-prepositions-fa": {
      "command": "python3",
      "args": ["/path/to/mcp-server/deutsch_prepositions_mcp_server.py"]
    }
  }
}
```

Tools: `lookup_verb`, `preposition`, `wechsel`, `check_sentence`, `quiz`,
`anki_export`, `list_prepositions`.

## Why not just another app?

Preposition guides (Transparent Language, Taalhammer, Fluent in 3 Months)
and practice games (Deutschland-Preposition, de-preposition-dice-toss) are
*reference works for learners* — this is a *tool for agents*:
deterministic, scriptable, CI-friendly, with JSON output, a sentence
checker with six error classes (DPR-01..DPR-06), quizzes, Anki export and
an MCP interface, so a tutor agent, a content pipeline or a classroom bot
can look up, check and drill without guessing. The 92-entry dataset is
original and hand-checked, with Persian glosses and the
Persian-interference traps (nach/zu, seit/vor, auf/über, da-compounds)
that English-language guides never cover.

## Honest limits

- The list is A1–B1 core vocabulary (v1.0.0) — not a dictionary for
  verbs outside it; unknown verbs get a labelled *not in the list*,
  not an answer.
- The sentence checker is deliberately conservative: simple
  present-tense sentences only. A place adverbial (`Ich warte in dem
  Bus`), a time phrase (`am Montag`) and an ambiguous verb (`hängen`,
  position and motion) are left alone rather than guessed.
  No finding ≠ correct.
- `sich freuen auf` (future) vs `über` (present) needs time context
  the checker does not have — both are accepted; the distinction is
  documented in `references/persian-traps.md`.
- Article-case errors inside a correct prepositional phrase
  (`über dem Lehrer`) belong to declension, not to this checker.
- A deterministic reference, not a teacher: no judgment on style or
  naturalness.

## Roadmap

- Grow the verb list toward 150 (B2), community contributions welcome
  (schema in `SKILL.md` — verify every combination against a dictionary).
- Genitive-preposition usage in `check` (writen-German `wegen` + Gen).
- Subordinate-clause and Perfekt coverage for `check`.
- Spaced-repetition scheduling for `quiz`.

## License

MIT — see LICENSE.

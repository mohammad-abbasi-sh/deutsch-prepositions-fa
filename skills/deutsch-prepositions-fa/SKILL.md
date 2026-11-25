---
name: deutsch-prepositions-fa
description: German prepositions for Persian speakers — look up which preposition (and case) a verb takes, apply the Wechsel Wo/Wohin rule, use time prepositions and da-compounds correctly, and check a learner's German sentence for preposition errors, with a deterministic zero-dependency tool. Use when writing or correcting German for Persian-speaking learners, when an agent must not guess a preposition or a case, or when building German-learning features. Never guess a preposition — look it up.
---

# German prepositions for Persian speakers — look it up, never guess it

Persian has one word, «در» / «به», where German has a whole system:
every preposition governs a case, nine of them switch case by Wo/Wohin,
verbs each demand their own preposition (`warten auf`, `sich freuen
über/auf/für` — three different meanings), and time runs on `am`/`im`/`um`
by a fixed rule. Agents answering from memory get these wrong constantly
— `Ich warte für dich`, `zu Berlin`, `in Montag` — and a wrong form
memorized once is hard to unlearn. This skill makes prepositions
**deterministic**: a zero-dependency engine plus a hand-checked A1–B1
table (38 prepositions, 92 verb+preposition entries, Persian glosses),
with every explanation in Persian.

## The contract

1. **Never guess a preposition.** When German text is on the table, run
   the bundled tool (pure stdlib, no downloads, no API):

   ```bash
   python3 scripts/prepositions.py lookup warten [--json]
   python3 scripts/prepositions.py prep auf [--json]
   python3 scripts/prepositions.py wechsel in wohin [--json]
   ```

   `lookup` prints every preposition a verb takes, with the case, the
   sense when one verb takes two (`denken an` = think of, `denken über`
   = think about), and an example sentence. `prep` prints the case a
   preposition governs, its verbs, its da-/wo- compounds and its
   contractions. `wechsel` answers Wo? (Dativ) vs Wohin? (Akkusativ)
   for the 9 two-way prepositions, with the correct articles.
   Exit codes: `0` = found · `1` = not in the list · `2` = usage error.

2. **Check learner sentences conservatively.** The checker only flags
   what it can decide — six error classes, each with an ID:

   ```bash
   python3 scripts/prepositions.py check "Ich warte für dich" [--json]
   # → [DPR-01] «warten» با «auf» + Akk می‌آید، نه «für».
   #   درستش: Ich warte auf dich.
   ```

   | ID | What it catches | Example |
   |---|---|---|
   | DPR-01 | wrong preposition after a verb | `warten für` → `auf` |
   | DPR-02 | nach/zu with destinations | `zu Berlin` → `nach Berlin`, `nach dem Arzt` → `zum Arzt` |
   | DPR-03 | wrong time preposition | `in Montag` → `am Montag`, `am 8 Uhr` → `um 8 Uhr` |
   | DPR-04 | wrong Wechsel case | `stellen auf dem Tisch` → `auf den Tisch` |
   | DPR-05 | pronoun instead of a da-compound | `denke an es` → `daran` |
   | DPR-06 | missing preposition after a verb | `Ich warte dich` → `Ich warte auf dich` |

   `fix` applies the corrections and re-checks (`fix` stops at an
   ambiguous fix and lists the options instead of guessing).
   Exit codes: `0` = no findings · `1` = findings · `2` = usage error.
   **No finding is not a proof of correctness** — say that when
   reporting. The checker is deliberately conservative: a place
   adverbial (`Ich warte in dem Bus`), a time phrase (`am Montag`) and
   an ambiguous verb (`hängen`, position and motion) are left alone
   rather than guessed; article-case errors inside a correct
   prepositional phrase (`über dem Lehrer`) belong to declension, not
   to this checker.

3. **Drill and export.** `quiz [--n 5] [--level A1] [--seed N]
   [--answers a,b,c]` runs an interactive drill (seeded sets are
   reproducible); `anki [--level A1] [--kind verbs|wechsel|time|da]
   [--out cards.tsv]` exports the lists as Anki-importable TSV.

## Know the limits — and say them

- The curated list is A1–B1 core vocabulary (92 verb+preposition
  entries, v1.0.0). It does not replace a dictionary for verbs outside
  it — `sich freuen für dich` (happy *for* you) is in the list because
  it is correct; many rarer combinations are not.
- The sentence checker handles simple present-tense sentences
  (pronoun + verb + prepositional phrase). Complex sentences are left
  alone rather than guessed.
- `sich freuen auf` (future) vs `über` (present) needs time context
  the checker does not have — it accepts both, and the distinction is
  in `references/persian-traps.md`.
- Genitive prepositions (`wegen`, `trotz`, `während`) are in the tables
  with examples; in spoken German `wegen`/`trotz` often take Dativ —
  the tool notes that, it does not flag it.
- This is a deterministic reference, not a teacher: it cannot judge
  style, word choice or whether a sentence sounds natural.

## Layout

- `scripts/prepositions.py` — the engine (lookup, checker, quiz, Anki
  export). Loads `data/prepositions.json` relative to itself.
- `data/prepositions.json` — the hand-checked tables. Contributions
  welcome: keep the schema (`verb`, `prep`, `case` ∈ akk/dat/wechsel/
  gen, `fa`, `level` ∈ A1/A2/B1, `ex`, `ex_fa`, optional `sense`,
  `sep`, `forms`, `needs_prep`, `lookup_only`) and verify every
  combination against a dictionary before adding.
- `references/preposition-tables.md` — the four case groups, the 9
  Wechsel prepositions with Wo/Wohin, contractions and da-/wo-
  compounds.
- `references/persian-traps.md` — the Persian-interference errors:
  one Persian word for many German prepositions, `nach` vs `zu`,
  `seit` vs `vor`, and the auf/über future distinction.

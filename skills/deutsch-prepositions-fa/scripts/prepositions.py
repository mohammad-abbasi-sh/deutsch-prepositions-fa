#!/usr/bin/env python3
"""deutsch-prepositions-fa — German prepositions for Persian speakers.

Zero-dependency (Python stdlib only). A hand-checked A1-B1 table of
German prepositions (38: Akkusativ / Dativ / Wechsel / Genitiv) and
92 verb+preposition entries with Persian glosses; a deterministic
sentence checker for the six error classes Persian speakers make most
often; quizzes and Anki export.

Error classes (DPR-01..DPR-06):
  DPR-01  wrong preposition after a verb (warten *für* dich -> auf dich)
  DPR-02  nach/zu with destinations (zu Berlin -> nach Berlin;
          nach dem Arzt -> zum Arzt)
  DPR-03  wrong time preposition (in Montag -> am Montag;
          um Mai -> im Mai; am 8 Uhr -> um 8 Uhr)
  DPR-04  wrong Wechsel case (stellen auf dem Tisch -> auf den Tisch;
          liegt auf den Tisch -> auf dem Tisch)
  DPR-05  pronoun instead of a da-compound (denke an es -> daran)
  DPR-06  missing preposition after a verb (Ich warte dich ->
          Ich warte auf dich)

Usage:
  prepositions.py lookup <verb> [--json]
  prepositions.py prep <preposition> [--json]
  prepositions.py wechsel <preposition> <wo|wohin> [--json]
  prepositions.py contract [form] [--json]
  prepositions.py da <preposition> [--json]
  prepositions.py check "<sentence>" [--json]
  prepositions.py fix "<sentence>" [--json]
  prepositions.py quiz [--level A1|A2|B1] [--n N] [--seed N] [--answers a,b,c]
  prepositions.py anki [--level ...] [--kind verbs|wechsel|time|da] [--out file.tsv]
  prepositions.py list [--level ...] [--group akk|dat|wechsel|gen|verbs]

Exit codes: 0 = ok / no findings · 1 = not found / findings ·
2 = usage error.
"""
import json
import os
import random
import re
import sys

CASE_FA = {"akk": "Akkusativ (مفعولی)", "dat": "Dativ (مفعول غیرمستقیم)",
           "wechsel": "Wechsel (دو حالتی)", "gen": "Genitiv (اضافه)"}
CASE_SHORT = {"akk": "Akk", "dat": "Dat", "gen": "Gen"}

REFLEXIVE = {"mich", "dich", "sich", "uns", "euch", "mir", "dir"}
ARTICLES = {"der", "die", "das", "den", "dem", "einen", "einem",
            "einer", "ein", "eine"}
PRONOUN_OBJ = {"mich", "dich", "ihn", "sie", "uns", "euch",
               "mir", "dir", "ihm", "ihr", "ihnen"}  # "es" excluded on purpose
PRONOUN_CASE = {
    ("mir", "akk"): "mich", ("dir", "akk"): "dich",
    ("ihm", "akk"): "ihn", ("ihr", "akk"): "sie",
    ("ihnen", "akk"): "sie",
    ("mich", "dat"): "mir", ("dich", "dat"): "dir",
    ("ihn", "dat"): "ihm", ("sie", "dat"): "ihr",
}
CONTRACTED = {
    "am": ("an", "dem"), "im": ("in", "dem"), "beim": ("bei", "dem"),
    "vom": ("von", "dem"), "zum": ("zu", "dem"), "zur": ("zu", "der"),
    "ans": ("an", "das"), "ins": ("in", "das"), "aufs": ("auf", "das"),
    "durchs": ("durch", "das"), "fürs": ("für", "das"), "ums": ("um", "das"),
}
TIME_RE = re.compile(r"^\d{1,2}([:.]\d{2})?$")


def _data_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", "prepositions.json")


def load_data():
    with open(_data_path(), encoding="utf-8") as f:
        return json.load(f)


DATA = load_data()
PREPS = {p["prep"]: p for p in DATA["prepositions"]}
PREP_NAMES = set(PREPS)
WECHSEL = {p["prep"] for p in DATA["prepositions"] if p["case"] == "wechsel"}
VERB_PREPS = DATA["verb_prepositions"]
NOUNS = DATA["nouns"]
PLURALS = {v[1]: k for k, v in NOUNS.items()}
CONTRACTIONS = DATA["contractions"]
DA = DATA["da_compounds"]
DA_PREPS = set(DA.values())
WO = DATA["wo_compounds"]
CITIES = set(DATA["cities"])
DESTINATIONS = set(DATA["destinations"])
WEEKDAYS = set(DATA["weekdays"])
MONTHS = set(DATA["months"])
SEASONS = set(DATA["seasons"])


# ---------------------------------------------------------------- form helpers

def _stem(inf):
    if inf.endswith(("eln", "ern")):
        return inf[:-1]
    return inf[:-2]


def _needs_e(s):
    """True when a -e- must be inserted before -st/-t (wartest, arbeitet)."""
    if not s:
        return False
    if s[-1] in ("d", "t"):
        return True
    if s[-1] in ("m", "n") and len(s) >= 2:
        prev = s[-2]
        if prev in "aeiouäöü" or prev in ("l", "r", "m", "n"):
            return False
        if prev == "h" and (len(s) < 3 or s[-3] in "aeiouäöü"):
            return False
        return True
    return False


def _s_stem(s):
    return s[-1:] in ("s", "ß", "x", "z")


def praesens_forms(inf):
    """Regular weak Präsens forms ich/du/er/wir/ihr/sie."""
    s = _stem(inf)
    du = (s + "t") if _s_stem(s) else (s + "est" if _needs_e(s) else s + "st")
    er = (s + "t") if _s_stem(s) else (s + "et" if _needs_e(s) else s + "t")
    ihr = (s + "t") if _s_stem(s) else (s + "et" if _needs_e(s) else s + "t")
    return [s + "e", du, er, s + "en", ihr, s + "en"]


def base_inf(entry):
    """Infinitive without 'sich ' and without a separable prefix."""
    v = entry["verb"]
    if v.startswith("sich "):
        v = v[5:]
    sep = entry.get("sep")
    if sep and v.startswith(sep):
        v = v[len(sep):]
    return v


def entry_forms(entry):
    if entry.get("forms"):
        return list(entry["forms"])
    return praesens_forms(base_inf(entry))


def _build_form_index():
    """Map every known surface form -> list of verb entries."""
    idx = {}
    for e in VERB_PREPS:
        if e.get("lookup_only"):
            continue
        for f in entry_forms(e):
            idx.setdefault(f, []).append(e)
        # infinitive itself (Ich will warten) and base infinitive
        idx.setdefault(e["verb"], []).append(e)
        idx.setdefault(base_inf(e), []).append(e)
    return idx


FORM_INDEX = None


def form_index():
    global FORM_INDEX
    if FORM_INDEX is None:
        FORM_INDEX = _build_form_index()
    return FORM_INDEX


def _build_pos_motion():
    """Map surface form -> {'pos': bool, 'motion': bool}."""
    idx = {}
    for group, key in ((DATA["position_verbs"], "pos"),
                       (DATA["motion_verbs"], "motion")):
        for v in group:
            forms = v.get("forms") or praesens_forms(v["inf"])
            for f in forms:
                idx.setdefault(f, {})[key] = True
            idx.setdefault(v["inf"], {})[key] = True
    return idx


POS_MOTION = None


def pos_motion():
    global POS_MOTION
    if POS_MOTION is None:
        POS_MOTION = _build_pos_motion()
    return POS_MOTION


MOTION_INFS = {v["inf"] for v in DATA["motion_verbs"]}


def motion_forms():
    out = set()
    for v in DATA["motion_verbs"]:
        out.update(v.get("forms") or praesens_forms(v["inf"]))
        out.add(v["inf"])
    return out


MOTION_FORMS = None


def motion_form_set():
    global MOTION_FORMS
    if MOTION_FORMS is None:
        MOTION_FORMS = motion_forms()
    return MOTION_FORMS


# ---------------------------------------------------------------- article logic

def noun_lookup(tok):
    """(gender, number) for a noun token, or (None, None)."""
    if tok in NOUNS:
        return NOUNS[tok][0], "sg"
    if tok in PLURALS:
        return NOUNS[PLURALS[tok]][0], "pl"
    # Dative plural adds -n: Zimmern, Tischen, Stühlen
    if tok.endswith("n") and tok[:-1] in PLURALS:
        return NOUNS[PLURALS[tok[:-1]]][0], "pl"
    if tok.endswith("n") and tok[:-1] in NOUNS and NOUNS[tok[:-1]][1] == tok[:-1]:
        return NOUNS[tok[:-1]][0], "pl"
    return None, None


def article_case(article, noun=None):
    """The case an article after a preposition must have, or None."""
    if article in ("dem", "einem"):
        return "dat"
    if article == "einen":
        return "akk"
    if article == "einer":
        return "dat"
    if article == "das":
        return "akk"
    if article == "die":
        return "akk"
    if article == "den":
        if noun is None:
            return None
        gender, number = noun_lookup(noun)
        if gender == "m" and number == "sg":
            return "akk"
        if number == "pl":
            return "dat"
        return None
    if article == "der":
        if noun is None:
            return None
        gender, number = noun_lookup(noun)
        if gender == "f" and number == "sg":
            return "dat"
        return None
    return None


def correct_article(gender, number, case):
    if number == "pl":
        return "den" if case == "dat" else "die"
    return {("m", "akk"): "den", ("m", "dat"): "dem",
            ("f", "akk"): "die", ("f", "dat"): "der",
            ("n", "akk"): "das", ("n", "dat"): "dem"}[(gender, case)]


def contract(prep, article):
    """Contract prep + article when German does (in + dem -> im)."""
    for short, (p, a) in CONTRACTIONS.items():
        if p == prep and a == article:
            return short
    return None


# ---------------------------------------------------------------- lookups

def lookup_verb(name):
    """All entries for a verb ('warten', 'sich freuen', 'freuen')."""
    name = name.strip()
    out = []
    for e in VERB_PREPS:
        if e["verb"] == name or e["verb"] == "sich " + name:
            out.append(e)
        elif base_inf(e) == name and not e.get("lookup_only"):
            out.append(e)
    # de-duplicate, keep data order
    seen = set()
    uniq = []
    for e in out:
        key = (e["verb"], e["prep"])
        if key not in seen:
            seen.add(key)
            uniq.append(e)
    return uniq


def suggest_verb(name):
    cands = [e["verb"] for e in VERB_PREPS
             if e["verb"].startswith(name[:3]) or name[:3] in e["verb"]]
    return sorted(set(cands))[:5]


def verb_entries_for_form(form):
    out = []
    seen = set()
    for e in form_index().get(form.lower(), []):
        key = (e["verb"], e["prep"])
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


# ---------------------------------------------------------------- print helpers

def _print_verb_entries(entries, as_json=False):
    if as_json:
        out_entries = []
        for e in entries:
            d = {k: e[k] for k in
                 ("verb", "prep", "case", "fa", "level", "ex", "ex_fa")
                 if k in e}
            if "sense" in e:
                d["sense"] = e["sense"]
            out_entries.append(d)
        print(json.dumps({"verb": entries[0]["verb"],
                          "entries": out_entries},
                         ensure_ascii=False, indent=2))
        return
    verb = entries[0]["verb"]
    print("%s — %s" % (verb, entries[0]["fa"]))
    for e in entries:
        sense = " (%s)" % e["sense"] if "sense" in e else ""
        print("  %s + %s%s  — سطح %s" % (e["prep"], CASE_FA[e["case"]],
                                          sense, e["level"]))
        print("    مثال: %s — %s" % (e["ex"], e["ex_fa"]))
    if len(entries) > 1:
        print("  نکته: این فعل با چند حرف اضافه می‌آید — معنی با حرف اضافه عوض می‌شود.")


def _show_prep(p, as_json=False):
    if as_json:
        print(json.dumps(p, ensure_ascii=False, indent=2))
        return
    print("%s — %s — %s" % (p["prep"], CASE_FA[p["case"]], p["fa"]))
    print("  مثال: %s — %s" % (p["ex"], p["ex_fa"]))
    users = [e for e in VERB_PREPS if e["prep"] == p["prep"]]
    if users:
        print("  فعل‌هایی که با آن می‌آیند: %s"
              % ", ".join(sorted({e["verb"] for e in users})))
    if p["case"] == "wechsel":
        print("  Wo? (کجا؟، ثابت) → Dativ · Wohin? (به کجا؟، حرکت) → Akkusativ")
    if p["prep"] in DA_PREPS:
        da = [k for k, v in DA.items() if v == p["prep"]][0]
        wo = [k for k, v in WO.items() if v == p["prep"]][0]
        print("  da-ترکیب: %s · wo-ترکیب: %s" % (da, wo))
    for short, (pp, a) in CONTRACTIONS.items():
        if pp == p["prep"]:
            print("  ادغام: %s + %s = %s" % (pp, a, short))

# ---------------------------------------------------------------- sentence checking

def tokenize(sentence):
    """Split on whitespace, strip sentence punctuation from each token."""
    toks = []
    for raw in sentence.strip().split():
        toks.append(raw.strip(".,!?;:\"«»()"))
    return [t for t in toks if t]


def _is_object_like(tok, next_tok=None):
    """True when a token after a verb looks like a direct object
    (article, noun, object pronoun, or adjective + noun)."""
    low = tok.lower()
    if low in ARTICLES:
        return True
    if low in PRONOUN_OBJ:
        return True
    if tok[:1].isupper():
        return True
    if next_tok and next_tok[:1].isupper() and re.match(r"^[a-zäöü]+(e|es|en|em|er)$", low):
        return True
    return False


def _adjust_following(toks, idx, case):
    """Fix the article/pronoun right after token idx to match `case`."""
    if idx + 1 >= len(toks):
        return
    nxt = toks[idx + 1]
    low = nxt.lower()
    if low in ARTICLES:
        noun = toks[idx + 2] if idx + 2 < len(toks) else None
        gender, number = noun_lookup(noun) if noun else (None, None)
        if gender:
            toks[idx + 1] = correct_article(gender, number, case)
        elif low == "dem" and case == "akk":
            toks[idx + 1] = "den"
        elif low == "den" and case == "dat":
            toks[idx + 1] = "dem"
        elif low == "einem" and case == "akk":
            toks[idx + 1] = "einen"
        elif low == "einen" and case == "dat":
            toks[idx + 1] = "einem"
        elif low == "einer" and case == "akk":
            toks[idx + 1] = "eine"
        elif low == "das" and case == "dat":
            toks[idx + 1] = "dem"
    elif low in PRONOUN_CASE and (low, case) in PRONOUN_CASE:
        toks[idx + 1] = PRONOUN_CASE[(low, case)]


def _join(toks, sentence):
    out = " ".join(toks)
    if sentence.strip().endswith((".", "!", "?")):
        out += sentence.strip()[-1]
    return out


def _find_verb(toks):
    """(index, entries) of the first known verb form in the tokens.

    A separable verb only counts when its prefix is in the sentence
    ('hängt' alone is hängen, not abhängen — 'Es hängt von dir ab').
    """
    for i, t in enumerate(toks):
        entries = verb_entries_for_form(t)
        if not entries:
            continue
        kept = []
        for e in entries:
            sep = e.get("sep")
            if not sep or e["verb"] == t.lower():
                kept.append(e)
            elif sep in [x.lower() for x in toks[i + 1:]]:
                kept.append(e)
        if kept:
            return i, kept
    return None, []


def _prep_after_verb(toks, vi, is_refl):
    """Index of the first preposition after the verb, or None.

    A reflexive pronoun between verb and preposition is skipped, but
    only for reflexive verbs — after 'warten', 'dich' is the object,
    not a reflexive pronoun.
    """
    j = vi + 1
    if is_refl:
        while j < len(toks) and toks[j].lower() in REFLEXIVE:
            j += 1
    if j < len(toks) and toks[j].lower() in PREP_NAMES:
        return j
    if j < len(toks) and toks[j].lower() in CONTRACTED:
        return j
    return None


def _is_time_prep(toks, pi):
    """True when the preposition at pi starts a time phrase
    (am Montag, im Mai, um 8 Uhr) — not the verb's argument."""
    if pi + 1 >= len(toks):
        return False
    nxt = toks[pi + 1]
    if nxt in WEEKDAYS or nxt in MONTHS or nxt in SEASONS:
        return True
    if TIME_RE.match(nxt) and pi + 2 < len(toks) and toks[pi + 2] == "Uhr":
        return True
    return False


LOCATIVE_PREPS = {"an", "auf", "hinter", "in", "neben", "über", "unter",
                  "vor", "zwischen", "aus", "bei", "von", "zu", "nach"}


def _is_adverbial(toks, pi):
    """True when the prep phrase at pi looks like a place adverbial
    (locative preposition + article + known place noun), e.g.
    'Ich warte in dem Bus' — not the verb's argument."""
    prep = toks[pi].lower()
    if prep in CONTRACTED:
        prep = CONTRACTED[prep][0]
    if prep not in LOCATIVE_PREPS:
        return False
    if toks[pi].lower() in CONTRACTED:
        # contracted article + noun: 'im Büro', 'am Tisch'
        if pi + 1 < len(toks) and noun_lookup(toks[pi + 1])[0]:
            return True
        return False
    if pi + 2 >= len(toks):
        return False
    if toks[pi + 1].lower() not in ARTICLES:
        return False
    for k in range(pi + 2, min(pi + 5, len(toks))):
        if noun_lookup(toks[k])[0]:
            return True
    return False


def check_sentence(sentence):
    """Check one German sentence. Returns a list of finding dicts."""
    toks = tokenize(sentence)
    if len(toks) < 2:
        return [{"error": "usage",
                 "message": "جمله باید دست‌کم دو کلمه داشته باشد."}]
    findings = []

    # ---- DPR-01 / DPR-05 / DPR-06: verb + preposition
    vi, entries = _find_verb(toks)
    pi = None
    verb_prep_ok = False
    if entries:
        is_refl = entries[0]["verb"].startswith("sich ")
        pi = _prep_after_verb(toks, vi, is_refl)
        if pi is not None and not _is_time_prep(toks, pi):
            prep = toks[pi].lower()
            if prep in CONTRACTED:
                prep, _art = CONTRACTED[prep]
            good = [e for e in entries if e["prep"] == prep]
            if good:
                verb_prep_ok = True
            if not good and _is_adverbial(toks, pi):
                # "Ich warte in dem Bus" — the prep phrase is a place
                # adverbial, not the verb's argument. Do not flag it.
                pass
            elif not good:
                want_prep = entries[0]["prep"]
                want_case = entries[0]["case"]
                fixed = list(toks)
                fixed[pi] = want_prep
                _adjust_following(fixed, pi, want_case)
                alts = ", ".join("«%s» + %s" % (e["prep"], CASE_SHORT[e["case"]])
                                 for e in entries)
                findings.append({
                    "rule": "DPR-01",
                    "error": "preposition",
                    "got": sentence,
                    "want": _join(fixed, sentence),
                    "message": "«%s» با %s می‌آید، نه «%s»."
                               % (entries[0]["verb"], alts, toks[pi])})
            else:
                # DPR-05: prep + es -> da-compound
                if pi + 1 < len(toks) and toks[pi + 1].lower() == "es" \
                        and prep in DA_PREPS:
                    da = [k for k, v in DA.items() if v == prep][0]
                    fixed = list(toks)
                    fixed[pi:pi + 2] = [da]
                    findings.append({
                        "rule": "DPR-05",
                        "error": "da-compound",
                        "got": sentence,
                        "want": _join(fixed, sentence),
                        "message": "بعد از «%s» برای چیز (نه شخص) ضمیر «es» نمی‌آید؛ "
                                   "ترکیب da- می‌خواهد: «%s»."
                                   % (prep, da)})
        else:
            # DPR-06: object without any preposition
            need = [e for e in entries if e.get("needs_prep")]
            if need:
                j = vi + 1
                reflexive_seen = False
                if is_refl:
                    while j < len(toks) and toks[j].lower() in REFLEXIVE:
                        reflexive_seen = True
                        j += 1
                if (not is_refl or reflexive_seen) and j < len(toks):
                    nxt = toks[j + 1] if j + 1 < len(toks) else None
                    if _is_object_like(toks[j], nxt):
                        if len(need) == 1:
                            e = need[0]
                            fixed = list(toks)
                            fixed.insert(j, e["prep"])
                            _adjust_following(fixed, j, e["case"])
                            findings.append({
                                "rule": "DPR-06",
                                "error": "missing-preposition",
                                "got": sentence,
                                "want": _join(fixed, sentence),
                                "message": "«%s» بدون حرف اضافه نمی‌آید؛ «%s» + %s می‌خواهد."
                                           % (e["verb"], e["prep"],
                                              CASE_FA[e["case"]])})
                        else:
                            alts = " یا ".join(
                                "«%s» + %s" % (e["prep"], CASE_FA[e["case"]])
                                for e in need)
                            findings.append({
                                "rule": "DPR-06",
                                "error": "missing-preposition",
                                "got": sentence,
                                "message": "«%s» بدون حرف اضافه نمی‌آید؛ یکی از این‌ها را می‌خواهد: %s."
                                           % (need[0]["verb"], alts)})

    # ---- DPR-02: nach/zu with destinations
    if not findings:
        for i, t in enumerate(toks):
            low = t.lower()
            if low == "zu" and i + 1 < len(toks) and toks[i + 1] in CITIES:
                fixed = list(toks)
                fixed[i] = "nach"
                findings.append({
                    "rule": "DPR-02", "error": "nach-zu",
                    "got": sentence, "want": _join(fixed, sentence),
                    "message": "شهر و کشور بدون حرف تعریف با «nach» می‌آید، نه «zu»: "
                               "nach %s." % toks[i + 1]})
                break
            if low == "nach" and i + 2 < len(toks) \
                    and toks[i + 1].lower() in ("dem", "der") \
                    and toks[i + 2] in DESTINATIONS:
                if any(x.lower() in motion_form_set() for x in toks):
                    fixed = list(toks)
                    art = "zum" if toks[i + 1].lower() == "dem" else "zur"
                    fixed[i:i + 2] = [art]
                    findings.append({
                        "rule": "DPR-02", "error": "nach-zu",
                        "got": sentence, "want": _join(fixed, sentence),
                        "message": "رفتن پیش «%s» با «%s» است، نه «nach dem/der»: "
                                   "«nach» برای شهر/کشور بدون حرف تعریف و برای زمان است."
                                   % (toks[i + 2], art)})
                    break

    # ---- DPR-03: time prepositions
    if not findings:
        for i, t in enumerate(toks):
            low = t.lower()
            if low in ("in", "im", "um") and i + 1 < len(toks) \
                    and toks[i + 1] in WEEKDAYS:
                fixed = list(toks)
                fixed[i] = "am"
                findings.append({
                    "rule": "DPR-03", "error": "time",
                    "got": sentence, "want": _join(fixed, sentence),
                    "message": "روزهای هفته با «am» می‌آیند: am %s."
                               % toks[i + 1]})
                break
            if low in ("in", "um") and i + 1 < len(toks) \
                    and toks[i + 1] in MONTHS:
                fixed = list(toks)
                fixed[i] = "im"
                findings.append({
                    "rule": "DPR-03", "error": "time",
                    "got": sentence, "want": _join(fixed, sentence),
                    "message": "ماه‌ها با «im» می‌آیند: im %s." % toks[i + 1]})
                break
            if low == "am" and i + 1 < len(toks) \
                    and toks[i + 1] in SEASONS:
                fixed = list(toks)
                fixed[i] = "im"
                findings.append({
                    "rule": "DPR-03", "error": "time",
                    "got": sentence, "want": _join(fixed, sentence),
                    "message": "فصل‌ها با «im» می‌آیند: im %s." % toks[i + 1]})
                break
            if low in ("am", "in") and i + 2 < len(toks) \
                    and TIME_RE.match(toks[i + 1]) \
                    and toks[i + 2] == "Uhr":
                fixed = list(toks)
                fixed[i] = "um"
                findings.append({
                    "rule": "DPR-03", "error": "time",
                    "got": sentence, "want": _join(fixed, sentence),
                    "message": "ساعت با «um» می‌آید: um %s Uhr."
                               % toks[i + 1]})
                break

    # ---- DPR-04: Wechsel case (Wo/Wohin)
    if not findings:
        pm = pos_motion()
        expected = None
        for t in toks:
            flags = pm.get(t.lower(), {})
            if flags.get("pos") and flags.get("motion"):
                expected = None
                break
            if flags.get("motion"):
                expected = "akk"
            elif flags.get("pos"):
                expected = "dat"
        if expected:
            for i, t in enumerate(toks):
                # A preposition that is the verb's own argument
                # ('warten auf den Bus') is governed by the verb, not
                # by Wo/Wohin — the Wechsel rule does not apply to it.
                if verb_prep_ok and i == pi:
                    continue
                # A time phrase ('am Montag', 'im Mai') is not a place.
                if _is_time_prep(toks, i):
                    continue
                low = t.lower()
                prep, art = None, None
                if low in WECHSEL and i + 1 < len(toks):
                    prep, art = low, toks[i + 1]
                    art_i = i + 1
                elif low in CONTRACTED and CONTRACTED[low][0] in WECHSEL:
                    prep, art = CONTRACTED[low]
                    art_i = i
                if prep is None:
                    continue
                # noun: scan up to 3 tokens ahead for a known noun
                noun = None
                for k in range(art_i + 1, min(art_i + 4, len(toks))):
                    if noun_lookup(toks[k])[0]:
                        noun = toks[k]
                        break
                actual = article_case(art.lower(), noun)
                if actual is None or actual == expected:
                    continue
                fixed = list(toks)
                if low in CONTRACTED:
                    # replace the contraction with prep + correct article
                    gender, number = noun_lookup(noun) if noun else (None, None)
                    if gender:
                        new_art = correct_article(gender, number, expected)
                    elif expected == "akk" and art in ("dem", "einem"):
                        new_art = {"dem": "den", "einem": "einen"}[art]
                    elif expected == "dat" and art == "das":
                        new_art = "dem"
                    else:
                        continue
                    fixed[i:i + 1] = [prep, new_art]
                else:
                    gender, number = noun_lookup(noun) if noun else (None, None)
                    if gender:
                        new_art = correct_article(gender, number, expected)
                    elif expected == "akk" and art.lower() in ("dem", "einem"):
                        new_art = {"dem": "den", "einem": "einen"}[art.lower()]
                    elif expected == "akk" and art.lower() == "einer":
                        new_art = "eine"
                    elif expected == "dat" and art.lower() == "das":
                        new_art = "dem"
                    elif expected == "dat" and art.lower() == "einen":
                        new_art = "einem"
                    else:
                        continue
                    fixed[art_i] = new_art
                # contract prep + new article when German does
                # (only at the fixed preposition, not elsewhere)
                if low not in CONTRACTED and art_i == i + 1:
                    c = contract(fixed[i].lower(), fixed[art_i].lower())
                    if c:
                        fixed[i:i + 2] = [c]
                q = "Wo? (کجا؟، ثابت)" if expected == "dat" \
                    else "Wohin? (به کجا؟، حرکت)"
                findings.append({
                    "rule": "DPR-04", "error": "wechsel-case",
                    "got": sentence, "want": _join(fixed, sentence),
                    "message": "«%s» اینجا %s است و %s می‌خواهد."
                               % (prep, q, CASE_FA[expected])})
                break
    return findings


def fix_sentence(sentence):
    """Apply fixes until clean (max 4 passes). Returns (fixed, findings).

    Stops at a finding without a 'want' (ambiguous fix — the message
    lists the options instead of guessing one).
    """
    current = sentence
    all_findings = []
    for _ in range(4):
        findings = check_sentence(current)
        if not findings or "want" not in findings[0]:
            if findings:
                all_findings.extend(findings)
            break
        all_findings.extend(findings)
        current = findings[0]["want"]
    return current, all_findings


# ---------------------------------------------------------------- quiz / anki

def quiz_questions(n, level=None, seed=None):
    rng = random.Random(seed)
    pool = [e for e in VERB_PREPS if level is None or e["level"] == level]
    pool.sort(key=lambda e: (e["verb"], e["prep"]))
    out = []
    kinds = ["verb_prep", "wechsel", "time", "da"]
    for _ in range(n):
        kind = rng.choice(kinds)
        if kind == "verb_prep":
            e = rng.choice(pool)
            q = {"kind": "verb_prep",
                 "q": "%s (%s) — حرف اضافه و حالتش؟" % (e["verb"], e["fa"]),
                 "want": e["prep"], "want_case": e["case"],
                 "explain": "%s + %s (%s). مثال: %s"
                            % (e["verb"], e["prep"], CASE_FA[e["case"]], e["ex"])}
        elif kind == "wechsel":
            wo = rng.choice([True, False])
            prep = rng.choice(sorted(WECHSEL))
            q = {"kind": "wechsel",
                 "q": "حرف «%s» با سؤال «%s» چه حالتی می‌گیرد؟ (پاسخ: Dativ یا Akkusativ)"
                     % (prep, "Wo? (کجا؟)" if wo else "Wohin? (به کجا؟)"),
                 "want": "Dativ" if wo else "Akkusativ",
                 "want_case": None,
                 "explain": "%s + Wo? → Dativ، + Wohin? → Akkusativ."
                            % prep}
        elif kind == "time":
            day = rng.choice(sorted(WEEKDAYS))
            q = {"kind": "time",
                 "q": "___ %s habe ich frei. (پاسخ: am / im / um)" % day,
                 "want": "am", "want_case": None,
                 "explain": "روزهای هفته با «am»: am %s." % day}
        else:
            e = rng.choice([x for x in pool
                            if x["prep"] in DA_PREPS
                            and not x.get("lookup_only")])
            da = [k for k, v in DA.items() if v == e["prep"]][0]
            q = {"kind": "da",
                 "q": "«%s %s es» → ترکیب da-؟" % (e["verb"], e["prep"]),
                 "want": da, "want_case": None,
                 "explain": "«%s %s es» → «%s»." % (e["verb"], e["prep"], da)}
        out.append(q)
    return out


def _answer_ok(q, ans):
    a = ans.strip().lower()
    if q["kind"] == "verb_prep":
        if a == q["want"]:
            return True
        parts = a.replace("+", " ").split()
        if parts and parts[0] == q["want"]:
            if len(parts) == 1:
                return True
            case_word = parts[1]
            return case_word in ("akk", "akkusativ", "dat", "dativ",
                                 "gen", "genitiv") and \
                {"akk": "akk", "akkusativ": "akk",
                 "dat": "dat", "dativ": "dat",
                 "gen": "gen", "genitiv": "gen"}[case_word] == q["want_case"]
        return False
    return a == q["want"].lower()


def anki_rows(level=None, kind="verbs"):
    rows = []
    if kind == "verbs":
        for e in sorted(VERB_PREPS, key=lambda x: (x["verb"], x["prep"])):
            if level is not None and e["level"] != level:
                continue
            front = "%s (%s) — حرف اضافه و حالتش؟" % (e["verb"], e["fa"])
            back = "%s + %s — %s. مثال: %s" % (
                e["verb"], e["prep"], CASE_FA[e["case"]], e["ex"])
            rows.append((front, back))
    elif kind == "wechsel":
        for prep in sorted(WECHSEL):
            p = PREPS[prep]
            rows.append(("%s + Wo? (کجا؟) — چه حالتی؟" % prep,
                         "Dativ. مثال: %s" % p["ex"]))
            rows.append(("%s + Wohin? (به کجا؟) — چه حالتی؟" % prep,
                         "Akkusativ. مثال: Das Bild hängt an die Wand."))
    elif kind == "time":
        for day in sorted(WEEKDAYS):
            rows.append(("___ %s habe ich frei. (حرف اضافه؟)" % day,
                         "am %s — روزهای هفته با «am»." % day))
        for month in sorted(MONTHS):
            rows.append(("___ %s fahre ich in den Urlaub. (حرف اضافه؟)" % month,
                         "im %s — ماه‌ها با «im»." % month))
        rows.append(("Der Kurs beginnt ___ 8 Uhr. (حرف اضافه؟)",
                     "um 8 Uhr — ساعت با «um»."))
    elif kind == "da":
        for prep in sorted(DA_PREPS):
            da = [k for k, v in DA.items() if v == prep][0]
            rows.append(("«%s es» → ترکیب da-؟" % prep,
                         "%s — «%s» برای چیز، نه شخص." % (da, prep)))
    return rows


# ---------------------------------------------------------------- CLI

def _print_lookup(name, as_json=False):
    entries = lookup_verb(name)
    if not entries:
        print("«%s» در فهرست ۹۲ فعل نیست." % name, file=sys.stderr)
        sug = suggest_verb(name)
        if sug:
            print("شاید منظورتان این‌هاست: %s" % ", ".join(sug),
                  file=sys.stderr)
        return 1
    _print_verb_entries(entries, as_json)
    return 0


def _print_prep(name, as_json=False):
    p = PREPS.get(name)
    if p is None:
        print("«%s» در جدول حرف‌های اضافه نیست." % name, file=sys.stderr)
        return 1
    _show_prep(p, as_json)
    return 0


def _print_wechsel(prep, where, as_json=False):
    p = PREPS.get(prep)
    if p is None or p["case"] != "wechsel":
        print("«%s» از حرف‌های دوحالتی (Wechsel) نیست." % prep,
              file=sys.stderr)
        return 1
    case = "dat" if where == "wo" else "akk"
    if as_json:
        print(json.dumps({"prep": prep, "where": where, "case": case,
                          "question": "Wo? (کجا؟، ثابت)" if where == "wo"
                          else "Wohin? (به کجا؟، حرکت)",
                          "article_m": correct_article("m", "sg", case),
                          "article_f": correct_article("f", "sg", case),
                          "article_n": correct_article("n", "sg", case),
                          "example": p["ex"]},
                         ensure_ascii=False, indent=2))
        return 0
    q = "Wo? (کجا؟، ثابت)" if where == "wo" else "Wohin? (به کجا؟، حرکت)"
    print("%s + %s → %s" % (prep, q, CASE_FA[case]))
    print("  der → %s · die → %s · das → %s"
          % (correct_article("m", "sg", case),
             correct_article("f", "sg", case),
             correct_article("n", "sg", case)))
    print("  مثال: %s — %s" % (p["ex"], p["ex_fa"]))
    return 0


def _print_contract(form=None, as_json=False):
    if form:
        pair = CONTRACTED.get(form)
        if pair is None:
            print("«%s» یک ادغام نیست." % form, file=sys.stderr)
            return 1
        if as_json:
            print(json.dumps({"form": form, "prep": pair[0],
                              "article": pair[1]}, ensure_ascii=False))
        else:
            print("%s = %s + %s" % (form, pair[0], pair[1]))
        return 0
    if as_json:
        print(json.dumps(CONTRACTIONS, ensure_ascii=False, indent=2))
        return 0
    print("ادغام‌های حرف اضافه + حرف تعریف:")
    for short, (p, a) in sorted(CONTRACTIONS.items()):
        print("  %s = %s + %s" % (short, p, a))
    return 0


def _print_da(prep, as_json=False):
    if prep not in DA and prep not in PREP_NAMES:
        print("«%s» حرف اضافه نیست." % prep, file=sys.stderr)
        return 1
    da = [k for k, v in DA.items() if v == prep]
    wo = [k for k, v in WO.items() if v == prep]
    if not da:
        print("«%s» ترکیب da- ندارد (مثلاً: ohne es درست است، نه ترکیب)."
              % prep)
        return 0
    if as_json:
        print(json.dumps({"prep": prep, "da": da[0], "wo": wo[0] if wo else None},
                         ensure_ascii=False, indent=2))
        return 0
    print("%s + es (چیز) → %s" % (prep, da[0]))
    if wo:
        print("%s + سؤال → %s" % (prep, wo[0]))
    print("  مثال: Ich denke an es. → Ich denke daran.")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    cmd = argv[0]
    args = argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]

    if cmd == "lookup":
        if not args:
            print("usage: lookup <verb> [--json]", file=sys.stderr)
            return 2
        return _print_lookup(args[0], as_json)

    if cmd == "prep":
        if not args:
            print("usage: prep <preposition> [--json]", file=sys.stderr)
            return 2
        return _print_prep(args[0], as_json)

    if cmd == "wechsel":
        if len(args) < 2 or args[1] not in ("wo", "wohin"):
            print("usage: wechsel <preposition> <wo|wohin> [--json]",
                  file=sys.stderr)
            return 2
        return _print_wechsel(args[0], args[1], as_json)

    if cmd == "contract":
        return _print_contract(args[0] if args else None, as_json)

    if cmd == "da":
        if not args:
            print("usage: da <preposition> [--json]", file=sys.stderr)
            return 2
        return _print_da(args[0], as_json)

    if cmd == "check":
        if not args:
            print('usage: check "<sentence>" [--json]', file=sys.stderr)
            return 2
        sentence = " ".join(args)
        findings = check_sentence(sentence)
        if as_json:
            print(json.dumps({"sentence": sentence, "findings": findings},
                             ensure_ascii=False, indent=2))
        else:
            if not findings:
                print("✓ مشکلی پیدا نشد (یا جمله قابل تصمیم‌گیری قطعی نبود).")
            for f in findings:
                print("✗ [%s] %s" % (f["rule"], f["message"]))
                if "want" in f:
                    print("  درستش: %s" % f["want"])
        return 1 if findings else 0

    if cmd == "fix":
        if not args:
            print('usage: fix "<sentence>" [--json]', file=sys.stderr)
            return 2
        sentence = " ".join(args)
        fixed, findings = fix_sentence(sentence)
        if as_json:
            print(json.dumps({"sentence": sentence, "fixed": fixed,
                              "findings": findings},
                             ensure_ascii=False, indent=2))
        else:
            print(fixed)
            for f in findings:
                print("  [%s] %s" % (f["rule"], f["message"]))
        return 1 if findings else 0

    if cmd == "list":
        level = None
        group = None
        i = 0
        while i < len(args):
            if args[i] == "--level" and i + 1 < len(args):
                level = args[i + 1]
                i += 2
            elif args[i] == "--group" and i + 1 < len(args):
                group = args[i + 1]
                i += 2
            else:
                i += 1
        if group in ("akk", "dat", "wechsel", "gen"):
            rows = [p for p in DATA["prepositions"] if p["case"] == group]
            for p in rows:
                print("%-10s %-28s %s" % (p["prep"], CASE_FA[p["case"]], p["fa"]))
            print("%d حرف اضافه" % len(rows))
            return 0
        rows = [e for e in sorted(VERB_PREPS, key=lambda x: (x["verb"], x["prep"]))
                if level is None or e["level"] == level]
        for e in rows:
            print("%-18s %-8s %-4s %s" % (e["verb"], e["prep"],
                                          CASE_SHORT[e["case"]], e["fa"]))
        print("%d مورد" % len(rows))
        return 0

    if cmd == "quiz":
        n, level, seed, answers = 5, None, None, None
        i = 0
        while i < len(args):
            if args[i] == "--n" and i + 1 < len(args):
                n = int(args[i + 1])
                i += 2
            elif args[i] == "--level" and i + 1 < len(args):
                level = args[i + 1]
                i += 2
            elif args[i] == "--seed" and i + 1 < len(args):
                seed = int(args[i + 1])
                i += 2
            elif args[i] == "--answers" and i + 1 < len(args):
                answers = args[i + 1].split(",")
                i += 2
            else:
                i += 1
        qs = quiz_questions(n, level, seed)
        score = 0
        for k, q in enumerate(qs):
            print("سؤال %d: %s" % (k + 1, q["q"]))
            if answers is not None:
                ans = answers[k].strip() if k < len(answers) else ""
                print("  پاسخ شما: %s" % ans)
            else:
                ans = input("  پاسخ: ").strip()
            if _answer_ok(q, ans):
                print("  ✓ درست!")
                score += 1
            else:
                print("  ✗ درستش: %s — %s" % (q["want"], q["explain"]))
        print("نتیجه: %d از %d" % (score, len(qs)))
        return 0 if score == len(qs) else 1

    if cmd == "anki":
        level, out, kind = None, None, "verbs"
        i = 0
        while i < len(args):
            if args[i] == "--level" and i + 1 < len(args):
                level = args[i + 1]
                i += 2
            elif args[i] == "--out" and i + 1 < len(args):
                out = args[i + 1]
                i += 2
            elif args[i] == "--kind" and i + 1 < len(args):
                kind = args[i + 1]
                i += 2
            else:
                i += 1
        if kind not in ("verbs", "wechsel", "time", "da"):
            print("kind باید یکی از این‌ها باشد: verbs, wechsel, time, da",
                  file=sys.stderr)
            return 2
        rows = anki_rows(level, kind)
        text = "\n".join("%s\t%s" % r for r in rows) + "\n"
        if out:
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            print("%d کارت در %s نوشته شد." % (len(rows), out))
        else:
            sys.stdout.write(text)
        return 0

    print("دستور ناشناخته: %s" % cmd, file=sys.stderr)
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

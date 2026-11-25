#!/usr/bin/env python3
"""Tests for deutsch-prepositions-fa (engine + CLI).

Run: python3 -m pytest tests/test_prepositions.py -q
(or: python3 tests/test_prepositions.py)
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "skills" / "deutsch-prepositions-fa" / "scripts" / "prepositions.py"
sys.path.insert(0, str(ENGINE.parent))

import prepositions as P  # noqa: E402


def check(s):
    return P.check_sentence(s)


def fixed(s):
    return P.fix_sentence(s)[0]


class TestData(unittest.TestCase):
    def test_preposition_counts(self):
        from collections import Counter
        c = Counter(p["case"] for p in P.DATA["prepositions"])
        self.assertEqual(c["akk"], 7)
        self.assertEqual(c["dat"], 10)
        self.assertEqual(c["wechsel"], 9)
        self.assertEqual(c["gen"], 12)
        self.assertEqual(len(P.DATA["prepositions"]), 38)

    def test_verb_entry_count(self):
        self.assertEqual(len(P.VERB_PREPS), 92)

    def test_every_verb_prep_in_table(self):
        for e in P.VERB_PREPS:
            self.assertIn(e["prep"], P.PREPS, e)

    def test_every_entry_has_example(self):
        for e in P.VERB_PREPS:
            self.assertTrue(e["ex"].endswith((".", "?", "!")), e)
            self.assertTrue(e["ex_fa"], e)
            self.assertIn(e["level"], ("A1", "A2", "B1"))

    def test_contractions_map_to_real_preps(self):
        for short, (p, _a) in P.CONTRACTIONS.items():
            self.assertIn(p, P.PREPS)
        self.assertEqual(len(P.CONTRACTIONS), 12)

    def test_da_wo_map_to_real_preps(self):
        for comp, p in list(P.DA.items()) + list(P.WO.items()):
            self.assertIn(p, P.PREPS, comp)
        self.assertEqual(len(P.DA), 19)
        self.assertEqual(len(P.WO), 16)

    def test_nouns_have_gender_and_plural(self):
        for n, (g, pl) in P.NOUNS.items():
            self.assertIn(g, ("m", "f", "n"), n)
            self.assertTrue(pl, n)
        self.assertGreaterEqual(len(P.NOUNS), 60)

    def test_multi_prep_verbs(self):
        multi = {v for v in ("sprechen", "denken", "arbeiten",
                              "sich freuen", "sich bedanken",
                              "sich unterhalten", "sich beschweren",
                              "sich bewerben", "leiden",
                              "sich entschuldigen", "bestehen")}
        for v in multi:
            self.assertGreaterEqual(len(P.lookup_verb(v)), 2, v)


class TestForms(unittest.TestCase):
    def test_weak_praesens(self):
        self.assertEqual(P.praesens_forms("warten")[:3],
                         ["warte", "wartest", "wartet"])

    def test_needs_e_insertion(self):
        self.assertEqual(P.praesens_forms("arbeiten")[1], "arbeitest")
        self.assertEqual(P.praesens_forms("bitten")[1], "bittest")

    def test_s_stem(self):
        self.assertEqual(P.praesens_forms("reisen")[1], "reist")

    def test_explicit_forms_win(self):
        e = P.lookup_verb("sprechen")[0]
        self.assertEqual(P.entry_forms(e)[1], "sprichst")
        e = P.lookup_verb("teilnehmen")[0]
        self.assertEqual(P.entry_forms(e)[1], "nimmst")


class TestLookup(unittest.TestCase):
    def test_warten(self):
        es = P.lookup_verb("warten")
        self.assertEqual(len(es), 1)
        self.assertEqual(es[0]["prep"], "auf")
        self.assertEqual(es[0]["case"], "akk")

    def test_sich_freuen_three(self):
        es = P.lookup_verb("sich freuen")
        self.assertEqual({e["prep"] for e in es}, {"über", "auf", "für"})

    def test_lookup_by_base(self):
        self.assertGreaterEqual(len(P.lookup_verb("freuen")), 3)

    def test_unknown_verb(self):
        self.assertEqual(P.lookup_verb("fliegen"), [])

    def test_suggest(self):
        self.assertIn("warten", P.suggest_verb("wart"))

    def test_lookup_only_entries(self):
        es = P.lookup_verb("stolz sein")
        self.assertEqual(len(es), 1)
        self.assertTrue(es[0].get("lookup_only"))


class TestPrepTables(unittest.TestCase):
    def test_prep_auf(self):
        p = P.PREPS["auf"]
        self.assertEqual(p["case"], "wechsel")

    def test_wechsel_wohin(self):
        self.assertEqual(P.correct_article("m", "sg", "akk"), "den")
        self.assertEqual(P.correct_article("f", "sg", "dat"), "der")
        self.assertEqual(P.correct_article("n", "sg", "dat"), "dem")
        self.assertEqual(P.correct_article("m", "pl", "dat"), "den")

    def test_contract(self):
        self.assertEqual(P.contract("in", "dem"), "im")
        self.assertEqual(P.contract("an", "dem"), "am")
        self.assertEqual(P.contract("zu", "der"), "zur")
        self.assertIsNone(P.contract("auf", "dem"))

    def test_article_case(self):
        self.assertEqual(P.article_case("dem"), "dat")
        self.assertEqual(P.article_case("den", "Tisch"), "akk")
        self.assertEqual(P.article_case("den", "Tische"), "dat")
        self.assertEqual(P.article_case("der", "Wand"), "dat")
        self.assertIsNone(P.article_case("der", "Tisch"))
        self.assertEqual(P.article_case("das", "Buch"), "akk")

    def test_da_compound(self):
        self.assertEqual([k for k, v in P.DA.items() if v == "an"], ["daran"])
        self.assertEqual([k for k, v in P.WO.items() if v == "an"], ["woran"])
        self.assertNotIn("ohne", P.DA_PREPS)


class TestDPR01(unittest.TestCase):
    def test_warten_fuer(self):
        f = check("Ich warte für dich.")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["rule"], "DPR-01")
        self.assertEqual(f[0]["want"], "Ich warte auf dich.")

    def test_interessieren_ueber(self):
        f = check("Sie interessiert sich über Musik.")
        self.assertEqual(f[0]["rule"], "DPR-01")
        self.assertEqual(f[0]["want"], "Sie interessiert sich für Musik.")

    def test_warten_fuer_dem_bus_fixes_article(self):
        f = check("Ich warte für dem Bus.")
        self.assertEqual(f[0]["want"], "Ich warte auf den Bus.")

    def test_clean_warten(self):
        self.assertEqual(check("Ich warte auf dich."), [])

    def test_freuen_fuer_is_correct(self):
        self.assertEqual(check("Ich freue mich für dich."), [])

    def test_arbeiten_fuer_is_correct(self):
        self.assertEqual(check("Ich arbeite für eine NGO."), [])


class TestDPR02(unittest.TestCase):
    def test_zu_berlin(self):
        f = check("Ich fahre zu Berlin.")
        self.assertEqual(f[0]["rule"], "DPR-02")
        self.assertEqual(f[0]["want"], "Ich fahre nach Berlin.")

    def test_nach_dem_arzt(self):
        f = check("Ich gehe nach dem Arzt.")
        self.assertEqual(f[0]["rule"], "DPR-02")
        self.assertEqual(f[0]["want"], "Ich gehe zum Arzt.")

    def test_nach_der_schule_is_time(self):
        self.assertEqual(check("Ich gehe nach der Schule nach Hause."), [])

    def test_nach_berlin_clean(self):
        self.assertEqual(check("Wir fahren nach Berlin."), [])


class TestDPR03(unittest.TestCase):
    def test_in_montag(self):
        f = check("Ich komme in Montag.")
        self.assertEqual(f[0]["rule"], "DPR-03")
        self.assertEqual(f[0]["want"], "Ich komme am Montag.")

    def test_um_mai(self):
        f = check("Wir fahren um Mai nach Berlin.")
        self.assertEqual(f[0]["want"], "Wir fahren im Mai nach Berlin.")

    def test_am_8_uhr(self):
        f = check("Der Kurs beginnt am 8 Uhr.")
        self.assertEqual(f[0]["rule"], "DPR-03")
        self.assertEqual(f[0]["want"], "Der Kurs beginnt um 8 Uhr.")

    def test_in_8_uhr(self):
        f = check("Der Kurs beginnt in 8 Uhr.")
        self.assertEqual(f[0]["want"], "Der Kurs beginnt um 8 Uhr.")

    def test_clean_time(self):
        self.assertEqual(check("Ich komme am Montag."), [])
        self.assertEqual(check("Wir fahren im Mai nach Berlin."), [])
        self.assertEqual(check("Der Kurs beginnt um 8 Uhr."), [])


class TestDPR04(unittest.TestCase):
    def test_stellen_auf_dem(self):
        f = check("Ich stelle das Buch auf dem Tisch.")
        self.assertEqual(f[0]["rule"], "DPR-04")
        self.assertEqual(f[0]["want"], "Ich stelle das Buch auf den Tisch.")

    def test_liegt_auf_den(self):
        f = check("Das Buch liegt auf den Tisch.")
        self.assertEqual(f[0]["want"], "Das Buch liegt auf dem Tisch.")

    def test_sitzt_in_das(self):
        f = check("Er sitzt in das Zimmer.")
        self.assertEqual(f[0]["want"], "Er sitzt im Zimmer.")

    def test_steht_hinter_das(self):
        f = check("Er steht hinter das Haus.")
        self.assertEqual(f[0]["want"], "Er steht hinter dem Haus.")

    def test_liegt_aufs(self):
        f = check("Das Buch liegt aufs Bett.")
        self.assertEqual(f[0]["want"], "Das Buch liegt auf dem Bett.")

    def test_clean_wechsel(self):
        self.assertEqual(check("Sie geht in die Schule."), [])
        self.assertEqual(check("Das Buch liegt auf dem Tisch."), [])
        self.assertEqual(check("Ich lege das Buch aufs Bett."), [])

    def test_haengen_ambiguous_is_skipped(self):
        # hängen is both a position and a motion verb: undecidable
        self.assertEqual(check("Das Bild hängt an die Wand."), [])
        self.assertEqual(check("Das Bild hängt an der Wand."), [])

    def test_verb_governed_prep_not_wechsel(self):
        self.assertEqual(check("Ich warte auf den Bus."), [])
        self.assertEqual(check("Ich arbeite an dem Projekt."), [])


class TestDPR05(unittest.TestCase):
    def test_denke_an_es(self):
        f = check("Ich denke an es.")
        self.assertEqual(f[0]["rule"], "DPR-05")
        self.assertEqual(f[0]["want"], "Ich denke daran.")

    def test_freue_auf_es(self):
        f = check("Ich freue mich auf es.")
        self.assertEqual(f[0]["want"], "Ich freue mich darauf.")

    def test_spricht_ueber_es(self):
        f = check("Er spricht über es.")
        self.assertEqual(f[0]["want"], "Er spricht darüber.")

    def test_person_pronoun_clean(self):
        self.assertEqual(check("Ich denke an sie."), [])
        self.assertEqual(check("Ich denke an dich."), [])


class TestDPR06(unittest.TestCase):
    def test_warte_dich(self):
        f = check("Ich warte dich.")
        self.assertEqual(f[0]["rule"], "DPR-06")
        self.assertEqual(f[0]["want"], "Ich warte auf dich.")

    def test_hoffe_gutes_wetter(self):
        f = check("Ich hoffe gutes Wetter.")
        self.assertEqual(f[0]["want"], "Ich hoffe auf gutes Wetter.")

    def test_interessiere_mich_musik(self):
        f = check("Ich interessiere mich Musik.")
        self.assertEqual(f[0]["want"], "Ich interessiere mich für Musik.")

    def test_multi_entry_has_no_want(self):
        f = check("Wir unterhalten uns Politik.")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["rule"], "DPR-06")
        self.assertNotIn("want", f)
        self.assertIn("mit", f[0]["message"])
        self.assertIn("über", f[0]["message"])

    def test_transitive_verbs_clean(self):
        self.assertEqual(check("Ich suche meinen Schlüssel."), [])
        self.assertEqual(check("Ich frage den Lehrer."), [])
        self.assertEqual(check("Sie diskutiert das Thema."), [])
        self.assertEqual(check("Ich glaube dir."), [])

    def test_transitive_separable_clean(self):
        self.assertEqual(check("Ich bereite die Prüfung vor."), [])
        self.assertEqual(check("Ich höre mit dem Rauchen auf."), [])


class TestGuards(unittest.TestCase):
    def test_place_adverbial_not_flagged(self):
        self.assertEqual(check("Ich warte in dem Bus."), [])
        self.assertEqual(check("Ich arbeite im Büro."), [])
        self.assertEqual(check("Ich denke in dem Zimmer."), [])

    def test_time_prep_beats_verb_rule(self):
        f = check("Der Kurs beginnt am 8 Uhr.")
        self.assertEqual(f[0]["rule"], "DPR-03")

    def test_separable_needs_prefix(self):
        # 'hängt' alone is hängen, not abhängen
        self.assertEqual(check("Das Bild hängt an der Wand."), [])
        # ... unless the prefix is there
        self.assertEqual(check("Es hängt von dir ab."), [])


class TestFix(unittest.TestCase):
    def test_fix_round_trip(self):
        for wrong, right in [
            ("Ich warte für dich.", "Ich warte auf dich."),
            ("Er sitzt in das Zimmer.", "Er sitzt im Zimmer."),
            ("Ich stelle das Buch auf dem Tisch.",
             "Ich stelle das Buch auf den Tisch."),
            ("Ich denke an es.", "Ich denke daran."),
            ("Ich fahre zu Berlin.", "Ich fahre nach Berlin."),
            ("Ich komme in Montag.", "Ich komme am Montag."),
            ("Ich warte dich.", "Ich warte auf dich."),
        ]:
            got, _findings = P.fix_sentence(wrong)
            self.assertEqual(got, right, wrong)
            self.assertEqual(check(got), [], got)

    def test_fix_clean_unchanged(self):
        got, findings = P.fix_sentence("Ich warte auf dich.")
        self.assertEqual(got, "Ich warte auf dich.")
        self.assertEqual(findings, [])

    def test_fix_ambiguous_stops(self):
        got, findings = P.fix_sentence("Wir unterhalten uns Politik.")
        self.assertEqual(got, "Wir unterhalten uns Politik.")
        self.assertEqual(len(findings), 1)


class TestQuizAnki(unittest.TestCase):
    def test_quiz_seeded_reproducible(self):
        a = P.quiz_questions(5, seed=42)
        b = P.quiz_questions(5, seed=42)
        self.assertEqual(a, b)

    def test_answer_ok(self):
        q = {"kind": "verb_prep", "want": "auf", "want_case": "akk"}
        self.assertTrue(P._answer_ok(q, "auf"))
        self.assertTrue(P._answer_ok(q, "auf Akk"))
        self.assertTrue(P._answer_ok(q, "auf Akkusativ"))
        self.assertFalse(P._answer_ok(q, "für"))
        self.assertFalse(P._answer_ok(q, "auf Dat"))

    def test_anki_verbs_count(self):
        self.assertEqual(len(P.anki_rows(kind="verbs")), 92)

    def test_anki_wechsel_count(self):
        self.assertEqual(len(P.anki_rows(kind="wechsel")), 18)

    def test_anki_da_count(self):
        self.assertEqual(len(P.anki_rows(kind="da")), len(P.DA_PREPS))

    def test_anki_time_rows(self):
        rows = P.anki_rows(kind="time")
        self.assertGreater(len(rows), 15)


class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        proc = subprocess.run([sys.executable, str(ENGINE), *args],
                              capture_output=True, text=True, timeout=60)
        return proc.returncode, proc.stdout, proc.stderr

    def test_lookup_ok(self):
        code, out, _ = self.run_cli("lookup", "warten")
        self.assertEqual(code, 0)
        self.assertIn("auf", out)

    def test_lookup_unknown(self):
        code, _out, err = self.run_cli("lookup", "fliegen")
        self.assertEqual(code, 1)
        self.assertIn("فهرست", err)

    def test_check_clean(self):
        code, out, _ = self.run_cli("check", "Ich warte auf dich.")
        self.assertEqual(code, 0)
        self.assertIn("✓", out)

    def test_check_wrong(self):
        code, out, _ = self.run_cli("check", "Ich warte für dich.")
        self.assertEqual(code, 1)
        self.assertIn("DPR-01", out)

    def test_check_json(self):
        code, out, _ = self.run_cli("check", "Ich warte für dich.", "--json")
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["findings"][0]["rule"], "DPR-01")

    def test_fix_cli(self):
        code, out, _ = self.run_cli("fix", "Ich warte für dich.")
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("Ich warte auf dich."))

    def test_list_wechsel(self):
        code, out, _ = self.run_cli("list", "--group", "wechsel")
        self.assertEqual(code, 0)
        self.assertIn("9 حرف اضافه", out)

    def test_unknown_command(self):
        code, _out, _err = self.run_cli("nonsense")
        self.assertEqual(code, 2)

    def test_quiz_noninteractive(self):
        code, out, _ = self.run_cli("quiz", "--n", "2", "--seed", "3",
                                     "--answers", "auf,am")
        self.assertIn("نتیجه:", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)

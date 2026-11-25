#!/usr/bin/env python3
"""MCP server for deutsch-prepositions-fa — expose the German
preposition engine as tools for any MCP client.

Zero-dependency (Python standard library only). Speaks JSON-RPC 2.0
over stdio, newline-delimited, following the MCP lifecycle:

    initialize -> notifications/initialized -> tools/list -> tools/call

Tools:
    lookup_verb
        verb    German infinitive, e.g. warten, sich freuen (required)
        format  "text" (default) or "json"
    preposition
        prep    German preposition, e.g. auf, nach, wegen (required)
        format  "text" (default) or "json"
    wechsel
        prep    one of the 9 two-way prepositions (required)
        where   "wo" (position, Dativ) or "wohin" (motion, Akkusativ)
        format  "text" (default) or "json"
    check_sentence
        sentence  German sentence to check (required)
        format    "text" (default) or "json"
    quiz
        n       number of questions (default 5)
        level   A1 | A2 | B1 (optional)
        seed    integer seed for a reproducible set (optional)
        answers comma-separated answers to score non-interactively
    anki_export
        level   A1 | A2 | B1 (optional)
        kind    verbs | wechsel | time | da (default verbs)
    list_prepositions
        group   akk | dat | wechsel | gen (optional)
        level   A1 | A2 | B1 (optional, for the verb list)

The server runs skills/deutsch-prepositions-fa/scripts/prepositions.py
as a subprocess; exit-code semantics are preserved in the returned text
(lookup: 1 = verb not in the curated list; check: 1 = findings).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "skills" / "deutsch-prepositions-fa" / "scripts" / "prepositions.py"

SERVER_INFO = {"name": "deutsch-prepositions-fa", "version": "1.0.0"}
PROTOCOL_VERSION = "2024-11-05"


def run_cli(*args):
    proc = subprocess.run([sys.executable, str(ENGINE), *args],
                          capture_output=True, text=True, timeout=120)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _with_exit(code, out, err):
    lines = []
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


def tool_lookup_verb(args):
    verb = args.get("verb")
    if not verb:
        raise ValueError("lookup_verb requires 'verb'")
    cmd = ["lookup", verb]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_preposition(args):
    prep = args.get("prep")
    if not prep:
        raise ValueError("preposition requires 'prep'")
    cmd = ["prep", prep]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_wechsel(args):
    prep = args.get("prep")
    where = args.get("where")
    if not prep or where not in ("wo", "wohin"):
        raise ValueError("wechsel requires 'prep' and where 'wo'|'wohin'")
    cmd = ["wechsel", prep, where]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_check_sentence(args):
    sentence = args.get("sentence")
    if not sentence:
        raise ValueError("check_sentence requires 'sentence'")
    cmd = ["check", sentence]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_quiz(args):
    cmd = ["quiz"]
    if args.get("n"):
        cmd += ["--n", str(args["n"])]
    if args.get("level"):
        cmd += ["--level", args["level"]]
    if args.get("seed") is not None:
        cmd += ["--seed", str(args["seed"])]
    if args.get("answers"):
        cmd += ["--answers", args["answers"]]
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_anki_export(args):
    cmd = ["anki"]
    if args.get("level"):
        cmd += ["--level", args["level"]]
    if args.get("kind"):
        cmd += ["--kind", args["kind"]]
    code, out, err = run_cli(*cmd)
    lines = [f"anki exit code: {code}",
             f"{len(out.splitlines())} cards (TSV: front<TAB>back)"]
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


def tool_list_prepositions(args):
    cmd = ["list"]
    if args.get("group"):
        cmd += ["--group", args["group"]]
    if args.get("level"):
        cmd += ["--level", args["level"]]
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


TOOLS = [
    {
        "name": "lookup_verb",
        "description": (
            "Look up which preposition (and case) a German verb takes, "
            "from a hand-checked A1-B1 list of 92 verb+preposition "
            "entries with Persian glosses — e.g. warten takes auf + "
            "Akkusativ, sich freuen takes auf/über/für with different "
            "meanings. Use instead of guessing a verb's preposition. "
            "Answers in German with Persian explanations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "verb": {"type": "string",
                         "description": "German infinitive, e.g. warten, sich freuen"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["verb"],
        },
    },
    {
        "name": "preposition",
        "description": (
            "Look up a German preposition: the case it governs "
            "(Akkusativ / Dativ / Wechsel / Genitiv), its Persian "
            "meaning, an example, which verbs take it, and its "
            "da-/wo- compounds and contractions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prep": {"type": "string",
                         "description": "German preposition, e.g. auf, nach, wegen"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["prep"],
        },
    },
    {
        "name": "wechsel",
        "description": (
            "Answer a Wechselpräposition question: given one of the 9 "
            "two-way prepositions (an, auf, hinter, in, neben, über, "
            "unter, vor, zwischen) and Wo? (position) or Wohin? "
            "(motion), return the case (Dativ / Akkusativ) and the "
            "correct articles (der/die/das -> den/die/das or "
            "dem/der/dem)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prep": {"type": "string",
                         "description": "one of the 9 Wechsel prepositions"},
                "where": {"type": "string", "enum": ["wo", "wohin"],
                          "description": "'wo' = position (Dativ), 'wohin' = motion (Akkusativ)"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["prep", "where"],
        },
    },
    {
        "name": "check_sentence",
        "description": (
            "Check a Persian-speaking learner's German sentence for "
            "preposition errors — wrong verb+preposition (DPR-01), "
            "nach/zu destinations (DPR-02), wrong time preposition "
            "(DPR-03), wrong Wechsel case (DPR-04), pronoun instead of "
            "a da-compound (DPR-05), missing preposition (DPR-06) — "
            "only where deterministically decidable. Conservative: no "
            "finding does not mean the sentence is perfect. "
            "Explanations in Persian, with the corrected sentence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sentence": {"type": "string",
                             "description": "German sentence to check"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["sentence"],
        },
    },
    {
        "name": "quiz",
        "description": (
            "Drill German prepositions: verb+preposition, Wechsel "
            "Wo/Wohin, time prepositions and da-compounds, from the "
            "curated A1-B1 list, with scoring. Pass answers to score "
            "non-interactively; pass a seed for a reproducible set."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "n": {"type": "integer",
                      "description": "number of questions (default 5)"},
                "level": {"type": "string", "enum": ["A1", "A2", "B1"],
                          "description": "restrict to one level"},
                "seed": {"type": "integer",
                         "description": "seed for a reproducible question set"},
                "answers": {"type": "string",
                            "description": "comma-separated answers to score"},
            },
        },
    },
    {
        "name": "anki_export",
        "description": (
            "Export the curated lists as Anki-importable TSV "
            "(front: question; back: answer). Kinds: verbs (verb + "
            "preposition), wechsel (Wo/Wohin), time (am/im/um), da "
            "(da-compounds)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["A1", "A2", "B1"],
                          "description": "restrict to one level"},
                "kind": {"type": "string",
                         "enum": ["verbs", "wechsel", "time", "da"],
                         "description": "card set (default verbs)"},
            },
        },
    },
    {
        "name": "list_prepositions",
        "description": (
            "List the curated prepositions (by case group) or the "
            "verb+preposition entries (optionally by level), with "
            "Persian glosses."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "group": {"type": "string",
                          "enum": ["akk", "dat", "wechsel", "gen"],
                          "description": "preposition case group"},
                "level": {"type": "string", "enum": ["A1", "A2", "B1"],
                          "description": "level filter for the verb list"},
            },
        },
    },
]

HANDLERS = {
    "lookup_verb": tool_lookup_verb,
    "preposition": tool_preposition,
    "wechsel": tool_wechsel,
    "check_sentence": tool_check_sentence,
    "quiz": tool_quiz,
    "anki_export": tool_anki_export,
    "list_prepositions": tool_list_prepositions,
}


def handle(request):
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"tools": TOOLS},
        }
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if handler is None:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32602,
                          "message": f"unknown tool: {name}"},
            }
        try:
            text = handler(arguments)
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        except Exception as exc:  # noqa: BLE001 - surface as tool error
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text",
                                        "text": f"error: {exc}"}],
                           "isError": True},
            }
    return {
        "jsonrpc": "2.0", "id": req_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()

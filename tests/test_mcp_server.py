#!/usr/bin/env python3
"""MCP end-to-end tests for deutsch-prepositions-fa.

Spawns the real server over stdio and drives the JSON-RPC lifecycle:
initialize -> tools/list -> tools/call for every tool.

Run: python3 -m unittest tests.test_mcp_server -v
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "mcp-server" / "deutsch_prepositions_mcp_server.py"


def drive(requests):
    """Send newline-delimited JSON-RPC requests, return responses."""
    proc = subprocess.run(
        [sys.executable, str(SERVER)],
        input="\n".join(json.dumps(r) for r in requests) + "\n",
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    out = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def rpc_call(tool, args, req_id):
    return {"jsonrpc": "2.0", "id": req_id, "method": "tools/call",
            "params": {"name": tool, "arguments": args}}


def text_of(resp):
    return resp["result"]["content"][0]["text"]


class TestMCP(unittest.TestCase):
    def test_initialize_and_list(self):
        resps = drive([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual(len(resps), 2)
        init = resps[0]["result"]
        self.assertEqual(init["serverInfo"]["name"],
                         "deutsch-prepositions-fa")
        tools = resps[1]["result"]["tools"]
        names = {t["name"] for t in tools}
        self.assertEqual(names, {"lookup_verb", "preposition", "wechsel",
                                 "check_sentence", "quiz", "anki_export",
                                 "list_prepositions"})

    def test_lookup_verb(self):
        resps = drive([rpc_call("lookup_verb", {"verb": "warten"}, 1)])
        text = text_of(resps[0])
        self.assertIn("auf", text)
        self.assertIn("Akkusativ", text)

    def test_lookup_verb_json(self):
        resps = drive([rpc_call("lookup_verb",
                                {"verb": "sich freuen", "format": "json"}, 1)])
        data = json.loads(text_of(resps[0]))
        self.assertEqual({e["prep"] for e in data["entries"]},
                         {"über", "auf", "für"})

    def test_preposition(self):
        resps = drive([rpc_call("preposition", {"prep": "wegen"}, 1)])
        text = text_of(resps[0])
        self.assertIn("Genitiv", text)

    def test_wechsel(self):
        resps = drive([rpc_call("wechsel",
                                {"prep": "in", "where": "wohin"}, 1)])
        text = text_of(resps[0])
        self.assertIn("Akkusativ", text)
        self.assertIn("den", text)

    def test_check_sentence_finds_error(self):
        resps = drive([rpc_call("check_sentence",
                                {"sentence": "Ich warte für dich."}, 1)])
        text = text_of(resps[0])
        self.assertIn("DPR-01", text)
        self.assertIn("Ich warte auf dich.", text)

    def test_check_sentence_clean(self):
        resps = drive([rpc_call("check_sentence",
                                {"sentence": "Ich warte auf dich."}, 1)])
        self.assertIn("✓", text_of(resps[0]))

    def test_quiz(self):
        resps = drive([rpc_call("quiz", {"n": 2, "seed": 5,
                                         "answers": "auf,am"}, 1)])
        self.assertIn("نتیجه:", text_of(resps[0]))

    def test_anki_export(self):
        resps = drive([rpc_call("anki_export",
                                {"kind": "wechsel"}, 1)])
        text = text_of(resps[0])
        self.assertIn("18 cards", text)

    def test_list_prepositions(self):
        resps = drive([rpc_call("list_prepositions",
                                {"group": "wechsel"}, 1)])
        text = text_of(resps[0])
        self.assertIn("9 حرف اضافه", text)

    def test_unknown_tool(self):
        resps = drive([rpc_call("nope", {}, 1)])
        self.assertIn("error", resps[0])

    def test_ping(self):
        resps = drive([{"jsonrpc": "2.0", "id": 9, "method": "ping"}])
        self.assertEqual(resps[0]["result"], {})


if __name__ == "__main__":
    unittest.main(verbosity=1)

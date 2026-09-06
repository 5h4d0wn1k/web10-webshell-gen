#!/usr/bin/env python3
"""Tests for WEB10 — Web Shell Generator (Lab) CLI + firmware engine."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(1, os.path.join(ROOT, "firmware"))

import webshell_gen  # noqa: E402
from webshell_gen import WebShellGenerator, PAYLOAD_LIBRARY, OBFUSCATORS  # noqa: E402


class LibraryIntegrityTest(unittest.TestCase):
    def test_languages(self):
        self.assertEqual(set(PAYLOAD_LIBRARY.keys()), {"php", "asp", "jsp"})

    def test_every_language_has_all_categories(self):
        cats = set(PAYLOAD_LIBRARY["php"].keys())
        for lang in PAYLOAD_LIBRARY:
            self.assertEqual(set(PAYLOAD_LIBRARY[lang].keys()), cats)

    def test_all_payloads_have_language_markers(self):
        for lang, cats in PAYLOAD_LIBRARY.items():
            for cat, info in cats.items():
                for p in info["payloads"]:
                    if lang == "php":
                        self.assertIn("<?php", p)
                    elif lang == "asp":
                        self.assertIn("<%", p)
                    else:
                        self.assertIn("<%", p)

    def test_obfuscators_registered(self):
        self.assertEqual(set(OBFUSCATORS.keys()),
                         {"base64", "hex", "randomize_vars"})


class GenerationTest(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp(prefix="web10_test_")

    def test_generate_all_writes_files(self):
        gen = WebShellGenerator(output_dir=self.out)
        results = gen.generate()
        self.assertGreater(len(results), 25)
        for g in results:
            self.assertTrue(os.path.exists(g["file"]))
            with open(g["file"]) as fh:
                self.assertIn("// WEB10 Lab Payload Generator", fh.read())

    def test_generate_php_only(self):
        gen = WebShellGenerator(output_dir=self.out)
        results = gen.generate(languages=["php"])
        self.assertTrue(results)
        self.assertTrue(all(r["language"] == "php" for r in results))

    def test_base64_obfuscation_wraps(self):
        gen = WebShellGenerator(output_dir=self.out)
        results = gen.generate(languages=["php"], categories=["command_exec"],
                               obfuscation=["base64"])
        for g in results:
            with open(g["file"]) as fh:
                self.assertIn("base64_decode", fh.read())

    def test_sha256_recorded(self):
        gen = WebShellGenerator(output_dir=self.out)
        results = gen.generate(languages=["php"], categories=["file_read"])
        for g in results:
            self.assertEqual(len(g["sha256"]), 16)

    def test_html_report_written_with_disclaimer(self):
        gen = WebShellGenerator(output_dir=self.out)
        gen.generate(languages=["php"], categories=["file_read"])
        report = gen.generate_html_report()
        self.assertTrue(os.path.exists(report))
        with open(report) as fh:
            self.assertIn("LEGAL DISCLAIMER", fh.read())


class CLITest(unittest.TestCase):
    def test_demo_returns_0(self):
        self.assertEqual(webshell_gen.run_demo(), 0)


if __name__ == "__main__":
    unittest.main()
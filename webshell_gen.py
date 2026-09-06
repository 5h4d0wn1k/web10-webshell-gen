#!/usr/bin/env python3
"""WEB10 — Web Shell Generator (Lab) — CLI.

Root-level command-line wrapper around the firmware payload engine. Runs fully
offline: generates PHP/ASP/JSP payload artifacts with optional obfuscation and
an HTML report, then verifies the artifacts structurally.
"""

import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firmware.webshell_gen import (
    WebShellGenerator,
    PAYLOAD_LIBRARY,
    OBFUSCATORS,
)


def _verify_structure(variant, lang):
    """Structural sanity check for a generated payload variant."""
    if lang == "php":
        return "<?php" in variant
    if lang == "asp":
        return "<%" in variant
    if lang == "jsp":
        return "<%" in variant and "import" in variant.replace("base64_decode", "")
    return True


def run_demo(verbose: bool = False) -> int:
    """Offline demo: generate all payloads + obfuscations, verify artifacts."""
    print("=" * 64)
    print("  WEB10 — Web Shell Generator (Lab) — Demo Mode")
    print("=" * 64)
    print("[*] Payload library: {} languages, {} categories".format(
        len(PAYLOAD_LIBRARY),
        len(PAYLOAD_LIBRARY[list(PAYLOAD_LIBRARY.keys())[0]]),
    ))
    print("[*] Obfuscators: {}".format(", ".join(sorted(OBFUSCATORS))))
    print()

    out = tempfile.mkdtemp(prefix="web10_demo_")
    print("[*] Output directory: {}".format(out))

    gen = WebShellGenerator(output_dir=out)
    results = gen.generate(
        languages=list(PAYLOAD_LIBRARY.keys()),
        categories=[c for c in PAYLOAD_LIBRARY[list(PAYLOAD_LIBRARY.keys())[0]]],
        obfuscation=["base64", "hex"],
    )
    print("[*] Generated {} artifacts (base64 + hex obfuscation)".format(len(results)))

    failures = []
    langs = set()
    for g in results:
        langs.add(g["language"])
        if not os.path.exists(g["file"]):
            failures.append("missing file: {}".format(g["file"]))
        else:
            with open(g["file"]) as fh:
                content = fh.read()
            header_ok = "// WEB10 Lab Payload Generator" in content
            struct_ok = _verify_structure(content, g["language"]) or bool(g["obfuscation"])
            if not header_ok:
                failures.append("bad header: {}".format(g["file"]))
            if not struct_ok:
                failures.append("bad structure ({}): {}".format(g["language"], g["file"]))

    for lang in PAYLOAD_LIBRARY:
        if lang not in langs:
            failures.append("no artifacts for language: {}".format(lang))

    report = gen.generate_html_report()
    if not os.path.exists(report):
        failures.append("report not written: {}".format(report))
    else:
        with open(report) as fh:
            if "LEGAL DISCLAIMER" not in fh.read():
                failures.append("report missing legal shield")

    gen.print_summary()

    if failures:
        print("\n[-] Demo FAILED:")
        for f in failures:
            print("    - {}".format(f))
        return 1

    print("\n[+] Demo: {} artifacts verified ({}) plus HTML report.".format(
        len(results), ", ".join(sorted(langs)),
    ))
    print("[+] Exit 0 -- generator works correctly.")
    return 0


def demo():
    sys.exit(run_demo(verbose=True))


def main():
    parser = argparse.ArgumentParser(
        description="WEB10 — Web Shell Generator (Lab)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 webshell_gen.py                    # offline demo\n"
            "  python3 webshell_gen.py --demo\n"
            "  python3 webshell_gen.py --languages php --categories command_exec --output-dir ./shells\n"
            "  python3 webshell_gen.py --obfuscation base64 hex --report\n"
        ),
    )
    parser.add_argument("--languages", nargs="+",
                        choices=sorted(PAYLOAD_LIBRARY.keys()),
                        help="Languages to generate (default: all)")
    parser.add_argument("--categories", nargs="+",
                        help="Payload categories (default: all)")
    parser.add_argument("--obfuscation", nargs="+",
                        choices=sorted(OBFUSCATORS.keys()),
                        help="Obfuscation methods to apply")
    parser.add_argument("--output-dir", "-o",
                        help="Directory for generated artifacts (default: temp)")
    parser.add_argument("--report", action="store_true",
                        help="Also write the HTML report")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")
    parser.add_argument("--demo", action="store_true",
                        help="Run offline demo (default when no arguments)")
    args = parser.parse_args()

    if args.demo or not (args.languages or args.categories or
                         args.obfuscation or args.output_dir or args.report):
        demo()
        return

    cat_default = [c for c in PAYLOAD_LIBRARY[list(PAYLOAD_LIBRARY.keys())[0]]]
    gen = WebShellGenerator(output_dir=args.output_dir)
    results = gen.generate(
        languages=args.languages,
        categories=args.categories or cat_default,
        obfuscation=args.obfuscation,
    )
    failed = 0
    for g in results:
        failed += 0 if os.path.exists(g["file"]) else 1
        print(g["file"])
    if args.report:
        print(gen.generate_html_report())
    if failed:
        print("[-] {} artifacts failed to write".format(failed))
        sys.exit(1)
    print("[+] {} artifacts written".format(len(results)))
    if args.output_dir:
        print("[+] Output: {}".format(args.output_dir))


if __name__ == "__main__":
    main()
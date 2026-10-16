"""Command Line Interface (CLI) for QRIS Parser & Validator."""

import argparse
import sys
from typing import Any, Dict

from qris_parser.core import QRIS
from qris_parser.generator import to_dynamic, to_static
from qris_parser.spec import CPM_TAG_DESCRIPTIONS, get_root_name, get_subtag_name

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

    class _EmptyColor:
        CYAN = ""
        YELLOW = ""
        GREEN = ""
        RED = ""
        BLUE = ""
        BRIGHT = ""
        RESET_ALL = ""

        def __getattr__(self, name: str) -> str:
            return ""

    Fore = _EmptyColor()  # type: ignore
    Style = _EmptyColor()  # type: ignore


def _colorize(text: str, color_code: str) -> str:
    if HAS_COLORAMA and sys.stdout.isatty():
        return f"{color_code}{text}{Style.RESET_ALL}"
    return text


def _print_tree(tags: Dict[str, Any], level: int = 0, is_cpm_mode: bool = False, parent_tag: str = "") -> None:
    indent = "   " * level
    for k in sorted(tags.keys()):
        v = tags[k]
        if is_cpm_mode:
            desc = CPM_TAG_DESCRIPTIONS.get(k, "Sub Data" if level > 0 else "Unknown CPM Tag")
        else:
            if level == 0:
                desc = get_root_name(k)
            else:
                desc = get_subtag_name(parent_tag, k)

        key_color = Fore.CYAN if level == 0 else Fore.YELLOW
        key_str = _colorize(f"[{k}]", key_color)

        if isinstance(v, dict):
            print(f"{indent}{key_str} {desc}:")
            _print_tree(v, level + 1, is_cpm_mode=is_cpm_mode, parent_tag=k)
        else:
            val_display = str(v)
            if val_display == "":
                val_display = _colorize("<EMPTY STRING>", Fore.RED)
            print(f"{indent}{key_str} {desc}: {val_display}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lightweight Python parser, compliance auditor, and dynamic generator for QRIS (ASPI v1.0 & EMVCo)."
    )
    parser.add_argument("payload", nargs="?", help="Raw QRIS payload string (MPM or CPM)")
    parser.add_argument("--json", action="store_true", help="Output result as formatted indented JSON")
    parser.add_argument("--validate", action="store_true", help="Validate ASPI compliance and exit with 0 or 1")
    parser.add_argument("--summary", action="store_true", help="Print structured merchant summary")
    parser.add_argument("--to-dynamic", metavar="AMOUNT", help="Convert static QRIS to dynamic with specified amount")
    parser.add_argument("--to-static", action="store_true", help="Convert dynamic QRIS to static QRIS")
    parser.add_argument("--save-image", metavar="FILENAME", help="Render and save QRIS as an image file (e.g. qris.png)")
    parser.add_argument("--version", action="version", version="qris-parser 0.2.0")

    args = parser.parse_args()

    raw_input_str = args.payload
    if not raw_input_str:
        if not sys.stdin.isatty():
            raw_input_str = sys.stdin.read().strip()
        else:
            print(_colorize("=== QRIS PARSER & ASPI VALIDATOR ===", Style.BRIGHT if HAS_COLORAMA else ""))
            print(_colorize("\nPaste QRIS string and press Enter:", Fore.YELLOW if HAS_COLORAMA else ""))
            try:
                raw_input_str = input("> ").strip()
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                sys.exit(0)

    if not raw_input_str:
        print(_colorize("Error: Payload cannot be empty.", Fore.RED if HAS_COLORAMA else ""), file=sys.stderr)
        sys.exit(1)

    # 1. Image export if requested
    if args.save_image:
        from qris_parser.image import generate_qr_image

        try:
            out_file = generate_qr_image(raw_input_str, args.save_image)
            print(_colorize(f"✅ QR Code image saved: {out_file}", Fore.GREEN if HAS_COLORAMA else ""))
            sys.exit(0)
        except Exception as e:
            print(_colorize(f"❌ Failed to generate QR image: {e}", Fore.RED if HAS_COLORAMA else ""), file=sys.stderr)
            sys.exit(1)

    # 2. Transform commands if requested
    if args.to_dynamic:
        res = to_dynamic(raw_input_str, args.to_dynamic)
        if res.success:
            if args.json:
                print(res.to_json(indent=2))
            else:
                print(_colorize("✅ Dynamic QRIS Generated:", Fore.GREEN if HAS_COLORAMA else ""))
                print(res.payload)
            sys.exit(0)
        else:
            if args.json:
                print(res.to_json(indent=2))
            else:
                print(_colorize(f"❌ Generation Failed: {res.error_message}", Fore.RED if HAS_COLORAMA else ""), file=sys.stderr)
            sys.exit(1)

    if args.to_static:
        res = to_static(raw_input_str)
        if res.success:
            if args.json:
                print(res.to_json(indent=2))
            else:
                print(_colorize("✅ Static QRIS Generated:", Fore.GREEN if HAS_COLORAMA else ""))
                print(res.payload)
            sys.exit(0)
        else:
            if args.json:
                print(res.to_json(indent=2))
            else:
                print(_colorize(f"❌ Generation Failed: {res.error_message}", Fore.RED if HAS_COLORAMA else ""), file=sys.stderr)
            sys.exit(1)

    # 2. Parse QRIS
    qris = QRIS.parse(raw_input_str)

    if args.json:
        # User explicitly requested JSON output
        report = qris.check_compliance()
        output_dict = qris.to_dict()
        output_dict["compliance"] = report.to_dict()
        import json
        print(json.dumps(output_dict, indent=2, ensure_ascii=False))
        sys.exit(0 if (qris.is_valid and report.is_compliant) else 1)

    if args.validate:
        if not qris.is_valid:
            print(_colorize(f"❌ PARSING FAILED: {qris.error_message}", Fore.RED if HAS_COLORAMA else ""), file=sys.stderr)
            sys.exit(1)
        report = qris.check_compliance()
        if report.is_compliant:
            print(_colorize("✅ COMPLIANT: QRIS complies with ASPI specifications.", Fore.GREEN if HAS_COLORAMA else ""))
            sys.exit(0)
        else:
            print(_colorize(f"❌ NON-COMPLIANT: {len(report.errors)} errors found.", Fore.RED if HAS_COLORAMA else ""))
            for err in report.errors:
                print(_colorize(f"  - {err}", Fore.RED if HAS_COLORAMA else ""))
            for warn in report.warnings:
                print(_colorize(f"  - {warn}", Fore.YELLOW if HAS_COLORAMA else ""))
            sys.exit(1)

    # Standard human-readable visual display
    header = "=== QRIS VALIDATOR (ASPI SPEC V1.0) ==="
    print(_colorize(header, Style.BRIGHT if HAS_COLORAMA else ""))
    print(f"Analyzing Payload: {raw_input_str[:40]}...")

    if not qris.is_valid:
        print(_colorize(f"\n❌ PARSING FAILED: {qris.error_message}", Fore.RED if HAS_COLORAMA else ""))
        sys.exit(1)

    mode_label = "CPM (Customer-Presented Mode)" if qris.is_cpm else "MPM (Merchant-Presented Mode)"
    print(_colorize(f"\n✅ FORMAT & CRC VALID [{mode_label}]", Fore.GREEN if HAS_COLORAMA else ""))

    if not args.summary:
        print(_colorize("\n--- DATA STRUCTURE ---", Style.BRIGHT if HAS_COLORAMA else ""))
        _print_tree(qris.tags, level=0, is_cpm_mode=qris.is_cpm)

    if qris.is_mpm:
        sm = qris.summary()
        print(_colorize("\n--- MERCHANT & ISSUER SUMMARY ---", Style.BRIGHT if HAS_COLORAMA else ""))
        print(f"Merchant Name : {sm.merchant_name}")
        print(f"City / Postal : {sm.city} ({sm.postal_code})")
        print(f"QRIS Type     : {sm.qris_type}")
        print(f"Acquirer      : {sm.acquirer} ({sm.product_name})")
        if sm.switchings:
            print(f"Switching     : {', '.join(sm.switchings)}")
        print(f"MCC           : {sm.mcc} ({sm.mcc_description})")
        print(f"NMID          : {sm.nmid}")
        if sm.amount_formatted:
            print(f"Amount        : {sm.amount_formatted}")
        if sm.tip_or_fee:
            print(f"Tip / Fee     : {sm.tip_or_fee}")

    # Compliance report
    report = qris.check_compliance()
    print(_colorize("\n--- COMPLIANCE REPORT ---", Style.BRIGHT if HAS_COLORAMA else ""))
    if report.is_compliant:
        print(_colorize("PERFECT! QRIS fully compliant with ASPI / EMVCo specs.", Fore.GREEN if HAS_COLORAMA else ""))
    else:
        for err in report.errors:
            print(_colorize(f"❌ {err}", Fore.RED if HAS_COLORAMA else ""))
    for warn in report.warnings:
        print(_colorize(f"⚠️ {warn}", Fore.YELLOW if HAS_COLORAMA else ""))


if __name__ == "__main__":
    main()

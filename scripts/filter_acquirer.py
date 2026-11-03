#!/usr/bin/env python3
"""Keep only the Merchant Account Information (MAI) of one acquirer in a QRIS MPM payload.

A QRIS MPM payload can carry several acquirer accounts in tags 26-45. Each MAI
holds a Global Unique Identifier (sub-tag 00, e.g. ``ID.MOTIONPAY.WWW``) and an
MPAN (sub-tag 01) whose first 8 digits are the NNS. This script drops every MAI
except the one you select, keeps every other tag untouched, and recomputes the
CRC so the result is a syntactically valid QRIS string.

    python scripts/filter_acquirer.py "<payload>" --keep MOTIONPAY

WARNING: editing the contents of a live QRIS is only safe when the acquirer (PJP)
that issued it does so. A QR whose accounts no longer match the merchant's
registration at the national repository is not a valid production QR. Use the
output for testing and as a reference for the issuing PJP, not for real payments.
"""

import argparse
import sys
from pathlib import Path

# Allow running as `python scripts/filter_acquirer.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qris_parser.generator import Segment, _get_segments  # noqa: E402
from qris_parser.crc import calculate_crc16  # noqa: E402

MAI_TAGS = {f"{t:02d}" for t in range(26, 46)}  # tags 26-45 carry MAI


def _sub_value(mai_value: str, sub_tag: str) -> str:
    """Return the value of a sub-tag inside an MAI template, or '' if absent."""
    segments = _get_segments(mai_value)
    if not segments:
        return ""
    for seg in segments:
        if seg.tag == sub_tag:
            return seg.value
    return ""


def _matches(mai_value: str, keep: str, match_by: str) -> bool:
    keep = keep.upper()
    if match_by == "gid":
        return keep in _sub_value(mai_value, "00").upper()
    # match_by == "nns": NNS is the first 8 digits of the MPAN (sub-tag 01)
    mpan = _sub_value(mai_value, "01")
    return mpan[:8] == keep


def filter_acquirer(payload: str, keep: str, match_by: str = "gid", renumber: bool = True) -> str:
    """Return a payload keeping only MAIs that match ``keep``; recompute the CRC."""
    segments = _get_segments(payload)
    if not segments:
        raise ValueError("Payload is not well-formed TLV")

    kept: list[Segment] = []
    next_mai = 26
    dropped = []
    for seg in segments:
        if seg.tag == "63":
            continue  # CRC is rebuilt at the end
        if seg.tag in MAI_TAGS:
            if _matches(seg.value, keep, match_by):
                tag = f"{next_mai:02d}" if renumber else seg.tag
                next_mai += 1
                kept.append(Segment(tag, seg.value))
            else:
                dropped.append(seg.tag)
            continue
        kept.append(seg)

    if next_mai == 26:
        raise ValueError(f"No MAI matched '{keep}' (match_by={match_by}); nothing kept")

    body = "".join(s.encode() for s in kept) + "6304"
    result = body + calculate_crc16(body)

    if dropped:
        print(f"Dropped MAI tags: {', '.join(dropped)}", file=sys.stderr)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Keep only one acquirer's MAI in a QRIS payload.")
    parser.add_argument("payload", nargs="?", help="QRIS payload string (reads stdin if omitted)")
    parser.add_argument("--keep", default="MOTIONPAY",
                        help="Global ID keyword (default) or NNS to keep, e.g. MOTIONPAY or 93600816")
    parser.add_argument("--by", choices=["gid", "nns"], default="gid",
                        help="Match --keep against the Global Unique Identifier (gid) or the NNS (nns)")
    parser.add_argument("--no-renumber", action="store_true",
                        help="Keep original tag numbers instead of renumbering kept MAIs from 26")
    args = parser.parse_args()

    payload = args.payload or sys.stdin.read().strip()
    if not payload:
        parser.error("no payload provided")

    try:
        result = filter_acquirer(payload, args.keep, args.by, renumber=not args.no_renumber)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

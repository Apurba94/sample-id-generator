"""Command-line interface for sample-id-generator."""
import argparse
import csv
import sys

from .core import IdGenerator, label_sheet_html, validate_id


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sample-id-generator", description="Generate and validate sample IDs.")
    ap.add_argument("--state", default="sample_ids.json", help="JSON file remembering issued IDs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("new")
    g.add_argument("prefix")
    g.add_argument("-n", type=int, default=1)
    g.add_argument("--random", action="store_true", help="non-sequential IDs (blinding)")
    g.add_argument("--no-year", action="store_true")
    g.add_argument("--csv", help="also write the IDs to this CSV")
    g.add_argument("--labels", help="write a printable HTML label sheet")
    g.add_argument("--columns", type=int, default=4)
    v = sub.add_parser("check")
    v.add_argument("ids", nargs="+")
    args = ap.parse_args(argv)
    if args.cmd == "check":
        bad = 0
        for sid in args.ids:
            ok = validate_id(sid)
            bad += not ok
            print("%-24s %s" % (sid, "valid" if ok else "INVALID (typo?)"))
        return 1 if bad else 0
    gen = IdGenerator(args.state)
    ids = gen.random(args.prefix, args.n) if args.random else gen.sequential(args.prefix, args.n, not args.no_year)
    for sid in ids:
        print(sid)
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["sample_id"])
            w.writerows([s] for s in ids)
    if args.labels:
        with open(args.labels, "w", encoding="utf-8") as fh:
            fh.write(label_sheet_html(ids, args.columns))
        print("label sheet: %s" % args.labels, file=sys.stderr)
    return 0

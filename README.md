# sample-id-generator

**Issue unique, typo-resistant sample IDs (`SOIL-2026-00042-K`) with a check character, never
reuse a number, generate blinded random IDs, and print label sheets.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Sample mix-ups are among the costliest lab errors, and they usually start with an ambiguous or
mistyped ID: `S12` vs `S21`, `O` vs `0`, duplicate numbers from two notebooks. A check character, like
those on credit cards and ISBNs, lets any spreadsheet or LIMS detect a wrong ID immediately.

## Features

- Format `PREFIX-YEAR-NNNNN-C` (year optional); counters per prefix and year stored in a JSON state file
- Crockford base32 alphabet (no I, L, O, U); validation normalizes confusable characters and case
- Luhn mod-32 check character: detects every single-character error and adjacent transpositions
- Random, non-sequential IDs for blinding (unique against everything issued before)
- Printable HTML label sheet (grid for adhesive labels) and CSV export; `check` validates IDs (exit 1 on errors)

## Usage

```bash
pip install .
sample-id-generator new SOIL -n 96 --csv plate1_ids.csv --labels plate1_labels.html
sample-id-generator new BLIND -n 40 --random
sample-id-generator check SOIL-2026-00042-K SOIL-2026-00024-K
```

## Testing

The tests verify that every possible single-character substitution is detected:

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA

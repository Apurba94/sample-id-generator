import datetime
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from sample_id_generator.cli import main
from sample_id_generator.core import ALPHABET, IdGenerator, check_char, label_sheet_html, make_id, validate_id


class CheckTests(unittest.TestCase):
    def test_make_and_validate(self):
        sid = make_id("soil", 42, 2026)
        self.assertTrue(sid.startswith("SOIL-2026-00042-"))
        self.assertTrue(validate_id(sid))
        self.assertTrue(validate_id(sid.lower().replace("-", " ")))

    def test_detects_all_single_substitutions(self):
        sid = make_id("PRJ", 123, 2026)
        body, chk = sid[:-1], sid[-1]
        for i, ch in enumerate(body):
            if ch == "-":
                continue
            for other in ALPHABET:
                if other != ch:
                    self.assertFalse(validate_id(body[:i] + other + body[i + 1:] + chk), (i, other))

    def test_detects_adjacent_transposition(self):
        self.assertFalse(validate_id("PRJ-2026-00012-" + check_char("PRJ-2026-00021")))

    def test_confusable_letters_normalized(self):
        sid = make_id("AB", 10)
        self.assertTrue(validate_id(sid.replace("0", "O")))


class GeneratorTests(unittest.TestCase):
    def test_sequential_persists(self):
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "s.json")
            a = IdGenerator(st, today=datetime.date(2026, 1, 1)).sequential("X", 2)
            b = IdGenerator(st, today=datetime.date(2026, 5, 1)).sequential("X", 1)
            c = IdGenerator(st, today=datetime.date(2027, 1, 1)).sequential("X", 1)
            self.assertEqual([i[:12] for i in a + b], ["X-2026-00001", "X-2026-00002", "X-2026-00003"])
            self.assertTrue(c[0].startswith("X-2027-00001"))

    def test_random_unique_and_valid(self):
        with tempfile.TemporaryDirectory() as d:
            ids = IdGenerator(os.path.join(d, "s.json")).random("BL", 50)
            self.assertEqual(len(set(ids)), 50)
            self.assertTrue(all(validate_id(i) for i in ids))

    def test_labels_and_cli(self):
        self.assertIn("<b>A-1</b><br><small>tube 1</small>", label_sheet_html(["A-1"], extra={"A-1": "tube 1"}))
        with tempfile.TemporaryDirectory() as d:
            st, lab = os.path.join(d, "s.json"), os.path.join(d, "labels.html")
            with redirect_stdout(io.StringIO()) as buf, redirect_stderr(io.StringIO()):
                main(["--state", st, "new", "tis", "-n", "3", "--labels", lab, "--no-year"])
            ids = buf.getvalue().split()
            self.assertEqual(len(ids), 3)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check"] + ids), 0)
                self.assertEqual(main(["check", ids[0][:-1] + ("0" if ids[0][-1] != "0" else "1")]), 1)
            self.assertTrue(os.path.exists(lab))


if __name__ == "__main__":
    unittest.main()

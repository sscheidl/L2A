import tempfile
import unittest
from pathlib import Path

import _src  # noqa: F401
from l2a import case as casemod
from l2a.case import Case, CaseError


class CaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def test_layout(self):
        c = Case.at(self.root / "my case")
        self.assertEqual(c.name, "my_case")
        self.assertEqual(c.project_file, c.root / "ghidra" / "my_case.gpr")
        self.assertEqual(c.out_dir, c.root / "out")

    def test_git_checkout_detection(self):
        repo = self.root / "repo"
        (repo / ".git").mkdir(parents=True)
        inside = repo / "a" / "b"
        inside.mkdir(parents=True)
        self.assertEqual(casemod.git_checkout_of(inside), repo)
        self.assertIsNone(casemod.git_checkout_of(self.root / "elsewhere"))
        with self.assertRaises(CaseError):
            Case.at(inside).check_not_in_git()

    def test_out_relative_goes_to_out_dir(self):
        c = Case.at(self.root / "case")
        self.assertEqual(c.resolve_out("main.c"), c.root / "out" / "main.c")
        self.assertEqual(c.resolve_out("sub/x.txt"), c.root / "out" / "sub" / "x.txt")

    def test_out_outside_case_refused(self):
        c = Case.at(self.root / "case")
        for bad in ("../../escape.c", str(self.root / "other" / "x.c")):
            with self.assertRaises(CaseError):
                c.resolve_out(bad)
        self.assertEqual(c.resolve_out("../../escape.c", allow_outside=True), (self.root / "escape.c").resolve())

    def test_out_inside_git_refused(self):
        repo = self.root / "repo"
        (repo / ".git").mkdir(parents=True)
        c = Case.at(self.root / "case")
        with self.assertRaises(CaseError):
            c.resolve_out(str(repo / "leak.c"))

    def test_records_roundtrip(self):
        c = Case.at(self.root / "case")
        self.assertEqual(c.load_records(), {})
        c.save_records({"a.bin": {"sha256": "00"}})
        self.assertEqual(c.load_records(), {"a.bin": {"sha256": "00"}})

    def test_require_project(self):
        with self.assertRaisesRegex(CaseError, "l2a open"):
            Case.at(self.root / "case").require_project()

    def test_sha256(self):
        p = self.root / "f.bin"
        p.write_bytes(b"abc")
        self.assertEqual(casemod.sha256_file(p), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


RECORD = {"sha256": "ab" * 32, "profile": "cortex-m", "format": "Raw Binary", "language": "ARM:LE:32:Cortex",
          "compiler": "default", "base": "0x24000000", "imported_at": "2026-11-03T12:00:00Z", "function_count": 5}


class CaseMdTest(unittest.TestCase):
    def test_block_inserted_before_findings_and_replaced(self):
        text = "# Case: x\n\n## Target\n\nt\n\n## Findings\n\nf\n"
        block = casemod.imports_block({"a.bin": RECORD})
        once = casemod.update_case_md(text, block)
        self.assertLess(once.index(casemod.IMPORTS_BEGIN), once.index("## Findings"))
        self.assertIn("`a.bin`", once)
        twice = casemod.update_case_md(once, casemod.imports_block({"a.bin": RECORD, "b.elf": RECORD}))
        self.assertEqual(twice.count(casemod.IMPORTS_BEGIN), 1)
        self.assertIn("`b.elf`", twice)
        self.assertTrue(twice.endswith("f\n"))

    def test_block_appended_without_findings(self):
        out = casemod.update_case_md("# Case: x\n", casemod.imports_block({}))
        self.assertTrue(out.rstrip().endswith(casemod.IMPORTS_END))

    def test_initial_case_md_uses_template(self):
        template = Path(__file__).resolve().parents[1] / "templates" / "case.md"
        text = casemod.initial_case_md("demo", template)
        self.assertTrue(text.startswith("# Case: demo"))
        self.assertIn("## Findings", text)
        self.assertIn("# Case: demo", casemod.initial_case_md("demo", None))


if __name__ == "__main__":
    unittest.main()

"""Full Ghidra integration test: `l2a open` and `l2a query` on a real Cortex-M build.

Runs only locally and only when L2A_GHIDRA_IT=1 (about two minutes). It needs the venv with PyGhidra and two
targets from our own Daisy build (never committed):

    L2A_IT_BIN  raw image   (default D:\\L2A-cases\\pyghidra-check\\target\\PhysicalModeling-v0.1.0.bin)
    L2A_IT_ELF  same build  (default D:\\L2A-cases\\pyghidra-check\\target\\PhysicalModeling-v0.1.0.elf)

The test case folder is created in the system temp folder and deleted afterwards.
"""

import contextlib
import io
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import _src  # noqa: F401

DEFAULT_TARGETS = Path(r"D:\L2A-cases\pyghidra-check\target")
BIN = Path(os.environ.get("L2A_IT_BIN", DEFAULT_TARGETS / "PhysicalModeling-v0.1.0.bin"))
ELF = Path(os.environ.get("L2A_IT_ELF", DEFAULT_TARGETS / "PhysicalModeling-v0.1.0.elf"))


def run(*argv):
    from l2a import cli

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


@unittest.skipUnless(os.environ.get("L2A_GHIDRA_IT") == "1", "set L2A_GHIDRA_IT=1 to run the Ghidra integration test")
class GhidraIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (BIN.is_file() and ELF.is_file()):
            raise unittest.SkipTest(f"targets missing: {BIN}, {ELF}")
        cls.tmp = tempfile.mkdtemp(prefix="l2a-it-")
        cls.case = str(Path(cls.tmp) / "it-case")
        code, out, err = run("open", cls.case, str(BIN), "--profile", "cortex-m", "--base", "0x24000000")
        assert code == 0, out + err
        code, out, err = run("open", cls.case, str(ELF), "--profile", "cortex-m-elf")
        assert code == 0, out + err

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def q(self, *argv, program=BIN.name):
        code, out, err = run("query", self.case, "-p", program, *argv)
        self.assertEqual(code, 0, out + err)
        return out

    def test_records_and_case_md(self):
        from l2a.case import Case

        c = Case.at(self.case)
        recs = c.load_records()
        self.assertEqual(recs[BIN.name]["base"], "0x24000000")
        self.assertEqual(recs[BIN.name]["vector_table"]["reset"], "0x24000748")
        self.assertEqual(recs[ELF.name]["language"], "ARM:LE:32:Cortex")
        self.assertTrue((c.target_dir / BIN.name).is_file())  # target copied into the case
        md = c.case_md.read_text(encoding="utf-8")
        self.assertIn(f"`{BIN.name}`", md)
        self.assertIn(f"`{ELF.name}`", md)

    def test_open_again_is_a_no_op(self):
        code, out, _ = run("open", self.case, str(BIN), "--profile", "cortex-m", "--base", "0x24000000")
        self.assertEqual(code, 0)
        self.assertIn("nothing to do", out)

    def test_raw_vector_handlers_match_elf_symbols(self):
        elf = self.q("disasm", "Reset_Handler", "--count", "1", program=ELF.name)
        raw = self.q("disasm", "reset_handler", "--count", "1")
        addr = lambda text: re.search(r"^\s+([0-9a-f]{8})\s", text, re.M).group(1)  # noqa: E731
        self.assertEqual(addr(elf), "24000748")
        self.assertEqual(addr(raw), "24000748")

    def test_queries_on_raw_image(self):
        out = self.q("info", "--then", "functions", "--sort", "fp", "--max-lines", "5",
                     "--then", "decompile", "reset_handler", "--then", "calls", "reset_handler",
                     "--then", "table", "vector_table", "--type", "uint32", "--count", "2",
                     "--then", "search", "--float", "48000")
        self.assertIn("ARM:LE:32:Cortex", out)
        self.assertIn("next: --offset 5", out)
        self.assertIn("void reset_handler", out)
        self.assertIn("callees (", out)
        self.assertIn("(0x24000749)", out)
        self.assertRegex(out, r"search: [1-9]\d* hits")
        self.assertEqual(out.count("--- BEGIN TARGET DATA"), 6)

    def test_queries_on_elf(self):
        out = self.q("xrefs", "main", "--then", "consts", "main", "--then", "disasm", "main", "--max-lines", "3",
                     program=ELF.name)
        self.assertIn("in Reset_Handler", out)
        self.assertIn("constants of 240009d4", out)

    def test_out_file_and_guard(self):
        out = self.q("decompile", "reset_handler", "--out", "reset.c")
        self.assertIn("wrote", out)
        self.assertTrue((Path(self.case) / "out" / "reset.c").is_file())
        code, _, err = run("query", self.case, "-p", BIN.name, "decompile", "reset_handler",
                           "--out", str(Path(self.tmp) / "outside.c"))
        self.assertEqual(code, 2)
        self.assertIn("outside the case folder", err)

    def test_two_programs_need_p(self):
        code, _, err = run("query", self.case, "info")
        self.assertEqual(code, 2)
        self.assertIn("choose one with -p", err)

    def test_queries_do_not_change_the_project(self):
        from l2a import ghidra
        from l2a.case import Case

        c = Case.at(self.case)
        self.q("functions", "--then", "decompile", "reset_handler")
        project = ghidra.open_project(c, create=False)
        try:
            df = ghidra.domain_file(project, BIN.name)
            self.assertFalse(df.isChanged())
            with ghidra.read_program(project, BIN.name) as program:
                self.assertEqual(program.getFunctionManager().getFunctionCount(),
                                 c.load_records()[BIN.name]["function_count"])
        finally:
            project.close()

    def test_zy_failed_reimport_leaves_project_and_record(self):
        from l2a.case import Case

        c = Case.at(self.case)
        before = c.load_records()[BIN.name]
        # A wrong base passes the block check, but the vector table no longer points into code.
        code, out, err = run("open", self.case, str(BIN), "--profile", "cortex-m", "--base", "0x08000000", "--reimport")
        self.assertEqual(code, 2, out + err)
        self.assertIn("no valid Cortex-M vector table", err)
        self.assertEqual(c.load_records()[BIN.name], before)
        out = self.q("disasm", "reset_handler", "--count", "1", "--then", "info")
        self.assertIn("24000748", out)
        self.assertIn(f"functions: {before['function_count']}", out)

    def test_zz_reimport_keeps_backup(self):
        code, out, err = run("open", self.case, str(BIN), "--profile", "cortex-m", "--base", "0x24000000", "--reimport")
        self.assertEqual(code, 0, out + err)
        self.assertTrue(any(p.name.startswith("ghidra-backup-") for p in Path(self.case).iterdir()))


if __name__ == "__main__":
    unittest.main()

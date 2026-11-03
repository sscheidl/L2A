"""Regression tests for the Codex security review of f287fca (docs/reviews/SECURITY_REVIEW_f287fca.md, F1-F7)."""

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import _src  # noqa: F401
from l2a import case as casemod, cli, output
from l2a.case import Case, CaseError
from l2a.ghidra import PINNED_GHIDRA, PINNED_JDK, tool_trust_problems

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import check_repo  # noqa: E402


def make_dir_link(link: Path, target: Path) -> bool:
    """A directory symlink, or an NTFS junction where symlinks need privileges. False if neither works."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    try:
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
        return True
    except (ImportError, OSError):
        return False


class TmpTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.case = Case.at(self.tmp / "case")
        self.case.root.mkdir()
        self.repo = self.tmp / "repo"
        (self.repo / ".git").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()


class F1LayoutTest(TmpTest):
    def test_linked_case_folders_are_refused(self):
        for sub in ("target", "ghidra", "out"):
            link = self.case.root / sub
            if not make_dir_link(link, self.repo):
                self.skipTest("cannot create directory links here")
            with self.assertRaisesRegex(CaseError, "link or junction"):
                self.case.check_layout()
            try:
                link.unlink()
            except OSError:
                os.rmdir(link)  # a junction, or a directory symlink on Windows

    def test_nested_checkout_in_case_folder_is_refused(self):
        (self.case.target_dir / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(CaseError, "git checkout"):
            self.case.check_layout()

    def test_open_refuses_before_copying(self):
        if not make_dir_link(self.case.target_dir, self.repo):
            self.skipTest("cannot create directory links here")
        src = self.tmp / "fw.bin"
        src.write_bytes(b"SYNTHETIC")
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            code = cli.main(["open", str(self.case.root), str(src), "--profile", "cortex-m", "--base", "0x24000000"])
        self.assertEqual(code, 2)
        self.assertFalse((self.repo / "fw.bin").exists())

    def test_metadata_replace_does_not_write_through_hardlinks(self):
        seed = self.repo / "seed.txt"
        seed.write_text("ORIGINAL")
        os.link(seed, self.case.case_md)
        casemod.write_text_atomic(self.case.case_md, "NEW")
        self.assertEqual(seed.read_text(), "ORIGINAL")
        self.assertEqual(self.case.case_md.read_text(), "NEW")

    def test_program_names(self):
        for ok in ("PhysicalModeling-v0.1.0.bin", "plug (x64).dll", "Größe_1.elf"):
            self.assertEqual(casemod.check_program_name(ok), ok)
        for bad in ("", ".", "..", ".hidden", "a/b", "a\\b", "a:b", "a|b", "a\nb", "`x`", "x" * 129):
            with self.assertRaises(CaseError):
                casemod.check_program_name(bad)


class F2FramingTest(unittest.TestCase):
    def test_forged_end_marker_stays_inside_the_data(self):
        text = output.render("t", [output.END, "after", "line1\nline2\r\x1b[2J", "sep x"])
        lines = text.split("\n")
        self.assertEqual(lines.count(output.END), 1)  # only the real marker
        begin, end = lines.index(output.BEGIN), lines.index(output.END)
        self.assertEqual(end, len(lines) - 1)
        self.assertTrue(all(line.startswith(output.DATA_PREFIX) for line in lines[begin + 1:end]))
        self.assertIn("line1\\x0aline2\\x0d\\x1b[2J", text)
        self.assertIn("sep\\u2028x", text)

    def test_title_cannot_add_lines(self):
        self.assertEqual(output.render("a\nb", []).split("\n")[0], "[l2a] a\\x0ab")

    def test_out_file_uses_the_same_framing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "o.txt"
            output.write_full(p, "t", [output.END, "x"])
            lines = p.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines.count(output.END), 1)
            self.assertEqual(lines[-1], output.END)

    def test_quote_and_markdown_cells(self):
        self.assertEqual(output.quote("a\nb|c"), '"a\\nb|c"')
        cell = casemod.md_code("` **x** |y\n")
        self.assertNotIn("\n", cell)
        self.assertIn("\\|", cell)
        self.assertTrue(cell.startswith("`` ") and cell.endswith(" ``"))

    def test_error_lines_are_escaped(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = cli.main(["query", "x", "-p"])
        self.assertEqual(code, 2)
        self.assertTrue(err.getvalue().startswith("l2a: error: "))


class F3OutTest(TmpTest):
    def test_protected_case_paths_are_refused_even_with_allow_outside(self):
        for bad in ("../ghidra/l2a-imports.json", "../case.md", "../target/fw.bin", "../ghidra/case.gpr", "."):
            for allow in (False, True):
                with self.assertRaises(CaseError, msg=bad):
                    self.case.resolve_out(bad, allow_outside=allow)
        self.assertEqual(self.case.resolve_out("sub/x.c"), self.case.out_dir / "sub" / "x.c")

    def test_out_file_does_not_write_through_hardlink(self):
        seed = self.repo / "seed.txt"
        seed.write_text("ORIGINAL")
        self.case.out_dir.mkdir()
        os.link(seed, self.case.out_dir / "result.txt")
        output.write_full(self.case.resolve_out("result.txt"), "t", ["SYNTHETIC"])
        self.assertEqual(seed.read_text(), "ORIGINAL")


class F5F6RepoGuardTest(unittest.TestCase):
    def setUp(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        shutil.copy(REPO / ".gitignore", self.root / ".gitignore")

    def tearDown(self):
        self._tmp.cleanup()

    def add(self, rel: str, data: bytes = b"SYNTHETIC_ONLY\n") -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        subprocess.run(["git", "-c", "core.autocrlf=false", "add", "-f", "--", rel], cwd=self.root, check=True,
                       capture_output=True)

    def test_case_layout_is_reported(self):
        for rel in ("one-case/case.md", "one-case/ghidra/l2a-imports.json", "one-case/out/notes.c",
                    "one-case/ghidra-backup-20261103/analysis.txt", "one-case/target-backup-20261103/fw.upd",
                    "one-case/target/fw.upd"):
            self.add(rel)
        found = "\n".join(check_repo.problems(self.root))
        for rel in ("case.md", "l2a-imports.json", "out/notes.c", "ghidra-backup-20261103", "target-backup-20261103",
                    "target/fw.upd"):
            self.assertIn(rel, found)

    def test_template_is_allowed(self):
        self.add("templates/case.md")
        self.assertEqual(check_repo.problems(self.root), [])

    def test_large_file_with_non_ascii_name(self):
        self.add("large-ä.txt", b"x" * (check_repo.MAX_BYTES + 1))
        self.assertTrue(any("larger than" in p for p in check_repo.problems(self.root)))


class F7ToolTrustTest(unittest.TestCase):
    def test_pinned_and_clean(self):
        self.assertEqual(tool_trust_problems(PINNED_GHIDRA, PINNED_JDK, [], [], False, False), [])

    def test_deviations_need_an_opt_in(self):
        problems = tool_trust_problems("12.2", "21.0.9", ["X/Extensions/foo"], ["pyghidra.setup:x=y"], False, False)
        self.assertEqual(len(problems), 4)
        self.assertEqual(tool_trust_problems("12.2", "21.0.9", [], [], True, False), [])
        self.assertEqual(len(tool_trust_problems(PINNED_GHIDRA, PINNED_JDK, ["e"], ["p"], False, True)), 0)


if __name__ == "__main__":
    unittest.main()

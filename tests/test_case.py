import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _src  # noqa: F401
from l2a import case as casemod
from l2a.case import Case, CaseError


@unittest.skipUnless(shutil.which("git"), "needs git")
class ExcludedCaseTest(unittest.TestCase):
    """A case inside a checkout is allowed only when git confirms a rule from that checkout's info/exclude."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve() / "repo"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q")
        self.exclude("/L2A-cases/\n")
        self.case = Case.at(self.repo / "L2A-cases" / "one")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, cwd, *args):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

    def exclude(self, text):
        (self.repo / ".git" / "info" / "exclude").write_text(text, encoding="utf-8")

    def test_excluded_case_is_allowed_even_before_it_exists(self):
        self.assertFalse(self.case.root.exists())
        self.case.check_layout()
        self.case.root.mkdir(parents=True)
        self.case.check_layout()

    def test_spaces_and_non_ascii_names_are_allowed(self):
        Case.at(self.repo / "L2A-cases" / "Fälle Nr 1").check_layout()

    def test_out_inside_an_excluded_case_is_allowed(self):
        self.case.root.mkdir(parents=True)
        self.assertEqual(self.case.resolve_out("dump.txt"), self.case.out_dir / "dump.txt")

    def test_only_a_plain_direct_subfolder_is_a_case(self):
        root = self.repo / "L2A-cases"
        for bad in (root, root / "_sealed", root / ".hidden", root / "one" / "nested"):
            with self.assertRaises(CaseError, msg=str(bad)):
                Case.at(bad).check_not_in_git()

    def test_other_excluded_folder_is_refused(self):
        self.exclude("/other/\n")
        with self.assertRaisesRegex(CaseError, "direct subfolder"):
            Case.at(self.repo / "other" / "one").check_not_in_git()

    def test_gitignore_match_does_not_count(self):
        self.exclude("")
        (self.repo / ".gitignore").write_text("/L2A-cases/\n", encoding="utf-8")
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            self.case.check_not_in_git()

    def test_unlisted_folder_is_refused(self):
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            Case.at(self.repo / "elsewhere" / "one").check_not_in_git()

    def test_negated_rule_is_refused(self):
        self.exclude("/L2A-cases/*\n!/L2A-cases/one\n")
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            self.case.check_not_in_git()

    def test_tracked_file_below_the_case_is_refused(self):
        self.case.root.mkdir(parents=True)
        (self.case.root / "case.md").write_text("x", encoding="utf-8")
        self.git(self.repo, "add", "-f", "L2A-cases/one/case.md")
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            self.case.check_not_in_git()

    def test_file_tracked_under_another_spelling_is_refused(self):
        lower = self.repo / "l2a-cases" / "one" / "out"
        lower.mkdir(parents=True)
        (lower / "result.txt").write_text("x", encoding="utf-8")
        self.git(self.repo, "add", "-f", "l2a-cases/one/out/result.txt")
        (self.repo / "l2a-cases").rename(self.repo / "moved")
        (self.repo / "moved").rename(self.repo / "L2A-cases")
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            self.case.check_not_in_git()
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            self.case.resolve_out("dump.txt")

    def test_similar_tracked_name_does_not_block(self):
        (self.repo / "L2A-cases").mkdir()
        (self.repo / "L2A-cases" / "one-more").write_text("x", encoding="utf-8")
        self.git(self.repo, "add", "-f", "L2A-cases/one-more")
        self.case.check_not_in_git()

    def test_rule_from_a_foreign_exclude_file_is_refused(self):
        self.exclude("")
        foreign = self.repo.parent / "foreign" / "info" / "exclude"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("/L2A-cases/\n", encoding="utf-8")
        self.git(self.repo, "config", "core.excludesFile", foreign.as_posix())
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            self.case.check_not_in_git()

    def check_ignore_answers(self, stdout):
        """Run the guard with `stdout` as the answer of check-ignore; the other git calls stay real."""
        real = subprocess.run

        def fake(cmd, **kwargs):
            if "check-ignore" in cmd:
                return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=b"")
            return real(cmd, **kwargs)

        with mock.patch.object(casemod.subprocess, "run", side_effect=fake):
            return casemod.git_excludes(self.repo, self.case.root)

    def test_only_one_complete_check_ignore_record_counts(self):
        source = str(self.repo / ".git" / "info" / "exclude").encode()
        path = b"L2A-cases/one"
        self.assertTrue(self.check_ignore_answers(b"\0".join([source, b"1", b"/L2A-cases/", path, b""])))
        for bad in (b"\0".join([source, b"1", b""]),
                    b"\0".join([source, b"1", b"", path, b""]),
                    b"\0".join([source, b"0", b"/L2A-cases/", path, b""]),
                    b"\0".join([source, b"x", b"/L2A-cases/", path, b""]),
                    b"\0".join([source, b"1", b"!/L2A-cases/", path, b""]),
                    b"\0".join([source, b"1", b"/L2A-cases/", b"L2A-cases/two", b""]),
                    b"\0".join([source, b"1", b"/L2A-cases/", path]),
                    b"\0".join([source, b"1", b"/L2A-cases/", path, source, b"1", b"x", path, b""])):
            self.assertFalse(self.check_ignore_answers(bad), bad)

    def test_checkout_root_is_refused(self):
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            Case.at(self.repo).check_not_in_git()

    def test_no_git_or_a_hanging_git_is_refused(self):
        for error in (FileNotFoundError("git"), subprocess.TimeoutExpired("git", 1)):
            with mock.patch.object(casemod.subprocess, "run", side_effect=error):
                with self.assertRaisesRegex(CaseError, "inside the git checkout"):
                    self.case.check_not_in_git()

    def test_invalid_inner_git_does_not_fall_through_to_the_outer_repository(self):
        inner = self.repo / "L2A-cases" / "fake"
        (inner / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            Case.at(inner / "one").check_not_in_git()

    def test_outer_checkout_must_exclude_too(self):
        outer = self.repo.parent
        self.git(outer, "init", "-q")
        with self.assertRaisesRegex(CaseError, "inside the git checkout"):
            self.case.check_not_in_git()


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

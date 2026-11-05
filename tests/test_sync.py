"""Tests for sync.sh, run as a real process against a disposable home.

Run: python3 -B -m unittest discover -s tests -p 'test_sync.py'

Every case uses a fresh TemporaryDirectory as HOME and clears the DOTFILES_*
and CODEX_HOME overrides, so neither sync.sh nor sync-skills.sh nor
lib/common.sh can write settings, skills, state or logs outside the fixture.
"""
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SYNC = os.path.join(REPO, "sync.sh")
DIRS = ("bin", "commands", "hooks", "skills")
FILES = (".zshrc", ".gitconfig", ".p10k.zsh", ".tmux.conf")
ISOLATED = (
    "CODEX_HOME",
    "DOTFILES_SKILLS_DIR",
    "DOTFILES_REPO",
    "DOTFILES_STATE_DIR",
    "DOTFILES_LOG_DIR",
    "DOTFILES_ROLE_FILE",
    "DOTFILES_LAST_RUN_LOG",
)
# The fake ln delegates here. Fall back to the POSIX location rather than
# failing the whole module at import when PATH has no ln.
REAL_LN = shutil.which("ln") or "/bin/ln"


class SyncCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = os.path.realpath(self.tmp.name)
        self.claude = os.path.join(self.home, ".claude")

    def sync(self, path_prefix=None, extra_env=None, repo=REPO):
        env = dict(os.environ)
        for name in ISOLATED:
            env.pop(name, None)
        env["HOME"] = self.home
        if path_prefix:
            env["PATH"] = path_prefix + os.pathsep + env.get("PATH", "")
        env.update(extra_env or {})
        proc = subprocess.run(
            [os.path.join(repo, "sync.sh")], cwd=repo, env=env,
            capture_output=True, text=True, timeout=60,
        )
        return proc.returncode, proc.stdout + proc.stderr

    def minimal_checkout(self, omit_dir):
        """A checkout with copies of the sync scripts and canonical files, empty
        .claude/<dir> stubs for every directory but one, and an empty
        .codex/skills, built inside the fixture so the real repo is untouched."""
        repo = os.path.join(self.home, "checkout")
        os.makedirs(os.path.join(repo, "lib"))
        os.makedirs(os.path.join(repo, ".codex", "skills"))
        for rel in ("sync.sh", "sync-skills.sh", os.path.join("lib", "common.sh")) + FILES:
            shutil.copy2(os.path.join(REPO, rel), os.path.join(repo, rel))
        for name in DIRS:
            if name != omit_dir:
                os.makedirs(os.path.join(repo, ".claude", name))
        return os.path.realpath(repo)

    def fake_ln(self, fail_target):
        """A fixture ln that fails for one target and delegates otherwise."""
        bindir = os.path.join(self.home, "fakebin")
        os.makedirs(bindir)
        path = os.path.join(bindir, "ln")
        with open(path, "w") as fh:
            fh.write(
                '#!/bin/bash\n'
                '[ "${@: -1}" = "$FAKE_LN_FAIL" ] && exit 1\n'
                'exec "%s" "$@"\n' % REAL_LN
            )
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return bindir, {"FAKE_LN_FAIL": fail_target}

    def dest(self, name):
        return os.path.join(self.claude, name)

    def src(self, name):
        return os.path.join(REPO, ".claude", name)


class DirectoryLinks(SyncCase):
    def test_fresh_home_links_four_dirs(self):  # T1
        code, out = self.sync()
        self.assertEqual(code, 0, out)
        self.assertTrue(os.path.isdir(self.claude) and not os.path.islink(self.claude))
        for name in DIRS:
            self.assertTrue(os.path.islink(self.dest(name)), name)
            self.assertEqual(os.readlink(self.dest(name)), self.src(name))
        for name in ("CLAUDE.md", "docs", "templates", "PLAN.templating-machine.md"):
            self.assertFalse(os.path.lexists(self.dest(name)), name)
        for name in FILES:
            self.assertEqual(os.readlink(os.path.join(self.home, name)), os.path.join(REPO, name))
        self.assertTrue(os.path.isdir(os.path.join(self.home, ".codex", "skills")))

    def test_second_run_is_idempotent(self):  # T2
        self.assertEqual(self.sync()[0], 0)
        before = {n: os.lstat(self.dest(n)).st_ino for n in DIRS}
        code, out = self.sync()
        self.assertEqual(code, 0, out)
        for name in DIRS:
            self.assertEqual(os.readlink(self.dest(name)), self.src(name))
            self.assertEqual(os.lstat(self.dest(name)).st_ino, before[name])
            self.assertIn("%s already points to the canonical" % self.dest(name), out)
        self.assertNotIn("Linked %s/" % self.claude, out)

    def test_real_dir_and_file_are_refused_others_continue(self):  # T3
        os.makedirs(self.dest("bin"))
        with open(os.path.join(self.dest("bin"), "sentinel"), "w") as fh:
            fh.write("keep")
        with open(self.dest("commands"), "w") as fh:
            fh.write("keep-file")
        code, out = self.sync()
        self.assertNotEqual(code, 0)
        self.assertTrue(os.path.isdir(self.dest("bin")) and not os.path.islink(self.dest("bin")))
        with open(os.path.join(self.dest("bin"), "sentinel")) as fh:
            self.assertEqual(fh.read(), "keep")
        self.assertTrue(os.path.isfile(self.dest("commands")) and not os.path.islink(self.dest("commands")))
        with open(self.dest("commands")) as fh:
            self.assertEqual(fh.read(), "keep-file")
        self.assertIn("Refusing to replace %s" % self.dest("bin"), out)
        self.assertIn("Refusing to replace %s" % self.dest("commands"), out)
        self.assertNotIn("Move machine-specific changes", out)
        self.assertNotIn("bin.local", out)
        self.assertNotIn("commands.local", out)
        for name in ("hooks", "skills"):
            self.assertEqual(os.readlink(self.dest(name)), self.src(name))

    def test_foreign_dir_symlink_is_refused(self):  # T4
        foreign = os.path.join(self.home, "foreign")
        os.makedirs(foreign)
        with open(os.path.join(foreign, "sentinel"), "w") as fh:
            fh.write("foreign")
        os.makedirs(self.claude)
        os.symlink(foreign, self.dest("bin"))
        code, out = self.sync()
        self.assertNotEqual(code, 0)
        self.assertEqual(os.readlink(self.dest("bin")), foreign)
        with open(os.path.join(foreign, "sentinel")) as fh:
            self.assertEqual(fh.read(), "foreign")
        self.assertIn("Refusing to replace %s" % self.dest("bin"), out)
        self.assertNotIn("Move machine-specific changes", out)

    def test_dangling_foreign_dir_symlink_is_refused(self):  # T5
        # [ -e ] is false for a dangling link; without an [ -L ] check first
        # the shared tail would rm -f it and relink silently.
        gone = os.path.join(self.home, "does-not-exist")
        os.makedirs(self.claude)
        os.symlink(gone, self.dest("bin"))
        code, out = self.sync()
        self.assertNotEqual(code, 0)
        self.assertEqual(os.readlink(self.dest("bin")), gone)
        self.assertIn("Refusing to replace %s" % self.dest("bin"), out)

    def assert_ln_failure_reported(self, target):
        bindir, env = self.fake_ln(target)
        code, out = self.sync(path_prefix=bindir, extra_env=env)
        self.assertNotEqual(code, 0, out)
        self.assertIn("Failed to link %s" % target, out)
        self.assertNotIn("Linked %s " % target, out)
        self.assertFalse(os.path.lexists(target))
        # Independent links keep processing.
        self.assertEqual(os.readlink(self.dest("commands")), self.src("commands"))
        self.assertEqual(os.readlink(os.path.join(self.home, ".gitconfig")),
                         os.path.join(REPO, ".gitconfig"))

    def test_ln_failure_is_reported_for_dir(self):  # T6
        self.assert_ln_failure_reported(self.dest("bin"))

    def test_ln_failure_is_reported_for_file(self):  # T6
        self.assert_ln_failure_reported(os.path.join(self.home, ".zshrc"))

    def test_uncreatable_parent(self):  # T7
        with open(self.claude, "w") as fh:
            fh.write("not a dir")
        code, out = self.sync()
        self.assertNotEqual(code, 0)
        self.assertTrue(os.path.isfile(self.claude) and not os.path.islink(self.claude))
        with open(self.claude) as fh:
            self.assertEqual(fh.read(), "not a dir")
        self.assertIn("Cannot create", out)
        self.assertNotIn("Linked %s/" % self.claude, out)

    def test_missing_canonical_source_is_refused(self):  # review R1
        # A checkout missing .claude/<dir> used to fall into the file branch,
        # leave a dangling link and print "Linked" with exit 0 -- the same
        # false-success class this item removes.
        repo = self.minimal_checkout(omit_dir="bin")
        code, out = self.sync(repo=repo)
        self.assertNotEqual(code, 0, out)
        self.assertIn("Canonical source %s is missing" % os.path.join(repo, ".claude", "bin"), out)
        self.assertNotIn("Linked %s " % self.dest("bin"), out)
        self.assertFalse(os.path.lexists(self.dest("bin")))
        for name in ("commands", "hooks", "skills"):
            self.assertEqual(os.readlink(self.dest(name)), os.path.join(repo, ".claude", name))

    def test_existing_link_to_missing_source_is_not_canonical(self):  # review R1
        # A link that already points at the canonical path is still dangling
        # when that path is gone; the missing-source check runs before the
        # "already points" early return so it is not reported as canonical.
        repo = self.minimal_checkout(omit_dir="bin")
        os.makedirs(self.claude)
        missing = os.path.join(repo, ".claude", "bin")
        os.symlink(missing, self.dest("bin"))
        code, out = self.sync(repo=repo)
        self.assertNotEqual(code, 0, out)
        self.assertIn("Canonical source %s is missing" % missing, out)
        self.assertNotIn("%s already points to the canonical" % self.dest("bin"), out)
        self.assertEqual(os.readlink(self.dest("bin")), missing)

    def test_settings_json_untouched(self):  # T8
        os.makedirs(self.claude)
        path = self.dest("settings.json")
        with open(path, "w") as fh:
            fh.write('{"permissions": {"allow": []}}\n')
        os.utime(path, (1_000_000_000, 1_000_000_000))
        before = os.stat(path)
        code, out = self.sync()
        self.assertEqual(code, 0, out)
        after = os.stat(path)
        self.assertEqual(after.st_mtime_ns, before.st_mtime_ns)
        with open(path) as fh:
            self.assertEqual(fh.read(), '{"permissions": {"allow": []}}\n')


class FileLinkCompatibility(SyncCase):
    def read(self, rel):
        with open(os.path.join(REPO, rel)) as fh:
            return fh.read()

    def test_existing_file_policy_preserved(self):  # T9
        h = lambda n: os.path.join(self.home, n)
        # identical regular file -> replaced by canonical link
        with open(h(".zshrc"), "w") as fh:
            fh.write(self.read(".zshrc"))
        # differing real files -> refused with the right companion
        with open(h(".gitconfig"), "w") as fh:
            fh.write("[user]\n\tname = local\n")
        with open(h(".p10k.zsh"), "w") as fh:
            fh.write("# local p10k\n")
        # foreign symlink to identical contents -> replaced
        elsewhere = os.path.join(self.home, "elsewhere-tmux")
        with open(elsewhere, "w") as fh:
            fh.write(self.read(".tmux.conf"))
        os.symlink(elsewhere, h(".tmux.conf"))
        code, out = self.sync()
        self.assertNotEqual(code, 0)
        self.assertEqual(os.readlink(h(".zshrc")), os.path.join(REPO, ".zshrc"))
        self.assertEqual(os.readlink(h(".tmux.conf")), os.path.join(REPO, ".tmux.conf"))
        with open(elsewhere) as fh:
            self.assertEqual(self.read(".tmux.conf"), fh.read())
        for name in (".gitconfig", ".p10k.zsh"):
            self.assertFalse(os.path.islink(h(name)), name)
            self.assertIn("Refusing to replace %s" % h(name), out)
        with open(h(".gitconfig")) as fh:
            self.assertEqual(fh.read(), "[user]\n\tname = local\n")
        with open(h(".p10k.zsh")) as fh:
            self.assertEqual(fh.read(), "# local p10k\n")
        self.assertIn("into %s before retrying" % h(".gitconfig.local"), out)
        self.assertIn("into %s before retrying" % h(".p10k.local.zsh"), out)
        # Claude directory links still processed.
        self.assertEqual(os.readlink(self.dest("bin")), self.src("bin"))

    def test_dangling_file_symlink_is_replaced(self):  # T9
        os.symlink(os.path.join(self.home, "gone"), os.path.join(self.home, ".zshrc"))
        code, out = self.sync()
        self.assertEqual(code, 0, out)
        self.assertEqual(os.readlink(os.path.join(self.home, ".zshrc")), os.path.join(REPO, ".zshrc"))


if __name__ == "__main__":
    unittest.main()

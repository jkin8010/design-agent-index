import contextlib
import datetime
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


SPEC = importlib.util.spec_from_file_location("build_index", Path(__file__).resolve().parents[1] / "scripts/build_index.py")
index = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(index)
SIGNALS = {"stars": 11, "forks": 1, "pushed": "2026-01-01", "created": "2025-01-01",
           "files": 2, "skill_md": True, "design_md": False, "plugin": False,
           "tests": False, "ci": False, "license": "MIT", "topics": [], "archived": False}
META = {"stargazers_count": 100, "forks_count": 2, "pushed_at": "2026-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z", "default_branch": "main", "license": {"spdx_id": "MIT"}}


class Response:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return io.BytesIO(json.dumps(self.data).encode())

    def __exit__(self, *args):
        pass


class RefreshTests(unittest.TestCase):
    def run_case(self, failures):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshots = root / "snapshots"
            snapshots.mkdir()
            registry = root / "registry.json"
            readme = root / "README.md"
            names = ["one/repo", "two/repo", "three/repo", "four/repo", "five/repo", "six/repo"]
            entries = [{"repo": n, "category": "skill", "signals": dict(SIGNALS)} for n in names]
            registry.write_text(json.dumps(entries))
            previous = [{**e, "signals": {**SIGNALS, "stars": 42}} for e in entries]
            old = snapshots / "2020-01-01.json"
            old.write_text(json.dumps({"entries": previous}))
            original = old.read_bytes()
            seen = []

            def urlopen(req, timeout):
                url = req.full_url
                name = next(n for n in names if f"/repos/{n}" in url)
                stage = "tree" if "/git/trees/" in url else "meta"
                seen.append((name, stage))
                failure = failures.get((name, stage))
                if isinstance(failure, int):
                    raise urllib.error.HTTPError(url, failure, "stub", {}, None)
                if failure == "network":
                    raise urllib.error.URLError("stub network")
                return Response(META if stage == "meta" else {"tree": [{"path": "SKILL.md"}]})

            output = io.StringIO()
            with mock.patch.multiple(index, REGISTRY=str(registry), SNAPSHOT_DIR=str(snapshots), README=str(readme)), \
                 mock.patch.object(index.sys, "argv", ["build_index.py", "--refresh"]), \
                 mock.patch.object(index.urllib.request, "urlopen", side_effect=urlopen), \
                 contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                result = index.main()
                first_readme = readme.read_text()
                result2 = index.main()
                self.assertEqual(first_readme, readme.read_text())
            self.assertEqual(result, result2)
            self.assertEqual(original, old.read_bytes())
            self.assertIn((names[-1], "tree"), seen)
            self.assertTrue(all(name in output.getvalue() for name in names))
            today = datetime.date.today().isoformat()
            snapshot = json.loads((snapshots / f"{today}.json").read_text())
            self.assertTrue((snapshots / f"{today}-0001.json").exists())
            errors_path = snapshots / f"{today}.errors.json"
            errors = json.loads(errors_path.read_text()) if errors_path.exists() else []
            return result, snapshot["entries"], errors, first_readme

    def test_normal_and_missing_metadata_and_tree(self):
        status, entries, errors, readme = self.run_case({("two/repo", "meta"): 404, ("three/repo", "tree"): 410})
        self.assertEqual(status, 0)
        self.assertEqual(entries[0]["signals"]["stars"], 100)
        for entry in entries[1:3]:
            self.assertEqual(entry["signals"]["stars"], 42)
            self.assertTrue(entry["missing"])
            self.assertIn(entry["unavailable_at"], readme)
        self.assertEqual([e["stage"] for e in errors], ["meta", "tree"])
        self.assertEqual([e["http_status"] for e in errors], [404, 410])
        self.assertTrue(all(e["kind"] == "unavailable" for e in errors))
        for error in errors:
            self.assertTrue(all(key in error for key in ("repo", "url", "http_status", "stage", "ts")))

    def test_auth_rate_server_and_network_fail_after_processing(self):
        status, entries, errors, _ = self.run_case({("one/repo", "meta"): 403, ("two/repo", "tree"): 429,
                                                     ("three/repo", "meta"): "network", ("four/repo", "tree"): 503})
        self.assertEqual(status, 1)
        self.assertEqual([e["kind"] for e in errors], ["authentication", "rate_limit_or_server", "network", "rate_limit_or_server"])
        self.assertIsNone(errors[2]["http_status"])
        self.assertTrue(all(e["missing"] and e["signals"]["stars"] == 42 for e in entries[:4]))
        self.assertEqual(entries[-1]["signals"]["stars"], 100)

    def test_latest_numbered_snapshot_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, stars in (("2026-11-01.json", 1), ("2026-11-01-0001.json", 2)):
                (root / name).write_text(json.dumps({"entries": [{"repo": "one/repo", "signals": {"stars": stars}}]}))
            with mock.patch.object(index, "SNAPSHOT_DIR", str(root)):
                self.assertEqual(index.previous_entries()["one/repo"]["signals"]["stars"], 2)

    def test_process_exit_status(self):
        script = """
import importlib.util, json, sys, urllib.error
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('index', sys.argv[1])
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)
index.REGISTRY, index.SNAPSHOT_DIR, index.README = sys.argv[2:5]
status = int(sys.argv[5])
def fail(req, timeout):
    if status == 0:
        raise urllib.error.URLError('stub network')
    raise urllib.error.HTTPError(req.full_url, status, 'stub', {}, None)
sys.argv = ['build_index.py', '--refresh']
with patch.object(index.urllib.request, 'urlopen', side_effect=fail):
    sys.exit(index.main())
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "registry.json"
            registry.write_text(json.dumps([{"repo": "one/repo", "category": "skill", "signals": SIGNALS}]))
            for http_status, expected in ((404, 0), (410, 0), (403, 1), (429, 1), (500, 1), (0, 1)):
                result = subprocess.run([sys.executable, "-c", script, str(Path(index.__file__)),
                                         str(registry), str(root / "snapshots"), str(root / "README.md"),
                                         str(http_status)], capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_all_success(self):
        status, entries, errors, _ = self.run_case({})
        self.assertEqual(status, 0)
        self.assertEqual(errors, [])
        self.assertTrue(all(e["signals"]["stars"] == 100 and "missing" not in e for e in entries))


if __name__ == "__main__":
    unittest.main()

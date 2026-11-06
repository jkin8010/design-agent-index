#!/usr/bin/env python3
"""Run one benchmark cell: (skill, brief) -> index.html.

  python3 bench/runner.py --skill hallmark --brief 01-saas-landing
  python3 bench/runner.py --skill control --brief 01-saas-landing --agent codex

A cell is a directory under bench/runs/<date>/<skill>/<brief>/ containing:
  index.html     the deliverable
  prompt.md      exactly what the agent was asked
  meta.json      model, CLI version, duration, exit code, skill commit
"""
import argparse
import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

BENCH = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BENCH)
SKILLS = json.load(open(os.path.join(BENCH, "skills.json")))
TIMEOUT = 900


class Result:
    def __init__(self, code, out, err):
        self.returncode, self.stdout, self.stderr = code, out, err


def sh(cmd, cwd=None, timeout=TIMEOUT, env=None):
    """Run in its own process group so a hung agent (and its children) can be killed.

    Claude Code spawns helper processes that inherit stdout; a plain subprocess.run
    timeout leaves the pipe open and the call hangs forever. This is the fix.
    """
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, env=env, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
        code = p.returncode
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except Exception:  # noqa: BLE001
            p.kill()
        out, err = p.communicate()
        code = "timeout"
    return Result(code, out, err), round(time.time() - t0, 1)


def install_skill(skill, workspace):
    """Clone the skill repo and expose every SKILL.md directory under .claude/skills/."""
    if not skill["repo"]:
        return []
    cache = os.path.join(BENCH, ".cache", skill["name"])
    if not os.path.isdir(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        sh(["git", "clone", "--depth", "1", f"https://github.com/{skill['repo']}.git", cache])
    head = subprocess.run(["git", "-C", cache, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    dest_root = os.path.join(workspace, ".claude", "skills")
    os.makedirs(dest_root, exist_ok=True)
    installed = []
    for dirpath, dirnames, filenames in os.walk(cache):
        if ".git" in dirpath:
            continue
        if "SKILL.md" in filenames:
            rel = os.path.relpath(dirpath, cache)
            name = skill["name"] if rel == "." else f"{skill['name']}-{rel.replace(os.sep, '-')}"
            shutil.copytree(dirpath, os.path.join(dest_root, name), dirs_exist_ok=True)
            installed.append(name)
            dirnames[:] = []
    return installed, head


def agent_cmd(agent, prompt):
    if agent == "claude":
        return ["claude", "-p", prompt, "--permission-mode", "acceptEdits"]
    if agent == "codex":
        return ["codex", "exec", "--full-auto", prompt]
    raise SystemExit(f"unknown agent {agent}")


def clean_claude_home():
    """A per-bench Claude config: auth/model env only, no personal plugins or skills.

    Without this every cell would inherit the operator's global plugins, which is a
    silent contamination of the benchmark.
    """
    src = os.path.expanduser("~/.claude/settings.json")
    dst_dir = os.path.join(BENCH, ".cache", "claude-home")
    os.makedirs(dst_dir, exist_ok=True)
    clean = {"env": {}, "permissions": {"allow": []}}
    if os.path.exists(src):
        cfg = json.load(open(src))
        clean["env"] = cfg.get("env", {})
    with open(os.path.join(dst_dir, "settings.json"), "w") as f:
        json.dump(clean, f, indent=1)
    return dst_dir


def cli_version(agent):
    try:
        out = subprocess.run([agent, "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:  # noqa: BLE001
        out = "unknown"
    return out.splitlines()[0] if out else "unknown"


def run_cell(skill, brief_id, agent, date, force=False):
    brief_path = os.path.join(BENCH, "briefs", f"{brief_id}.md")
    brief = open(brief_path).read()
    cell = os.path.join(BENCH, "runs", date, skill["name"], brief_id)
    out_html = os.path.join(cell, "index.html")
    if os.path.exists(out_html) and not force:
        print(f"skip (exists): {skill['name']}/{brief_id}")
        return

    shutil.rmtree(cell, ignore_errors=True)
    os.makedirs(cell, exist_ok=True)
    installed = []
    head = ""
    if skill["repo"]:
        installed, head = install_skill(skill, cell)

    prompt = brief
    if installed:
        prompt += (
            "\n\n---\n\nA design skill is installed at `.claude/skills/`: "
            + ", ".join(installed)
            + ". Read it before you start and follow it. If it conflicts with the hard constraints above, "
            "the hard constraints win.\n"
        )
    else:
        prompt += "\n\n---\n\nNo skill is installed. Work from your own judgement.\n"
    open(os.path.join(cell, "prompt.md"), "w").write(prompt)

    env = dict(os.environ)
    if agent == "claude":
        env["CLAUDE_CONFIG_DIR"] = clean_claude_home()
    try:
        proc, secs = sh(agent_cmd(agent, prompt), cwd=cell, env=env)
        code = proc.returncode
        tail = (proc.stdout or "")[-1500:]
    except subprocess.TimeoutExpired:
        code, secs, tail = "timeout", TIMEOUT, ""

    ok = os.path.exists(out_html)
    meta = {
        "skill": skill["name"],
        "repo": skill["repo"],
        "skill_commit": head,
        "installed_skills": installed,
        "brief": brief_id,
        "agent": agent,
        "agent_version": cli_version(agent),
        "model_env": {k: v for k, v in os.environ.items() if k.startswith("ANTHROPIC_MODEL")},
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "seconds": secs,
        "exit_code": code,
        "html_written": ok,
        "html_bytes": os.path.getsize(out_html) if ok else 0,
        "stdout_tail": tail,
    }
    open(os.path.join(cell, "meta.json"), "w").write(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"{'ok ' if ok else 'FAIL'} {skill['name']}/{brief_id} {secs}s exit={code} bytes={meta['html_bytes']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default="all")
    ap.add_argument("--brief", default="all")
    ap.add_argument("--agent", default="claude")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--parallel", type=int, default=1, help="cells to run concurrently")
    args = ap.parse_args()

    skills = SKILLS["skills"]
    if args.skill != "all":
        skills = [s for s in skills if s["name"] == args.skill]
        if not skills:
            raise SystemExit(f"unknown skill {args.skill}")

    briefs = sorted(f[:-3] for f in os.listdir(os.path.join(BENCH, "briefs")) if f.endswith(".md"))
    if args.brief != "all":
        briefs = [b for b in briefs if b == args.brief or b.startswith(args.brief)]
        if not briefs:
            raise SystemExit(f"unknown brief {args.brief}")

    cells = [(s, b) for s in skills for b in briefs]
    if args.parallel > 1:
        with ThreadPoolExecutor(max_workers=args.parallel) as ex:
            list(ex.map(lambda sb: run_cell(sb[0], sb[1], args.agent, args.date, args.force), cells))
    else:
        for skill, brief in cells:
            run_cell(skill, brief, args.agent, args.date, args.force)


if __name__ == "__main__":
    main()
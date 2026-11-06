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
            # Symlink, not copy: some skills ship 100MB of references and 24 cells
            # would eat gigabytes on a disk that is already 96% full.
            dst = os.path.join(dest_root, name)
            try:
                os.symlink(dirpath, dst)
            except OSError:
                shutil.copytree(dirpath, dst, dirs_exist_ok=True)
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


def model_env():
    """The model actually used, read from the same clean config the agent runs with.

    Recording this is not optional: a score whose model is unknown cannot be compared
    to anything, and the publication gate rejects it.
    """
    path = os.path.join(clean_claude_home(), "settings.json")
    env = json.load(open(path)).get("env", {}) if os.path.exists(path) else {}
    safe = {k: v for k, v in env.items() if "TOKEN" not in k.upper() and "KEY" not in k.upper()}
    return env.get("ANTHROPIC_MODEL") or env.get("ANTHROPIC_DEFAULT_SONNET_MODEL"), safe


def cli_version(agent):
    try:
        out = subprocess.run([agent, "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:  # noqa: BLE001
        out = "unknown"
    return out.splitlines()[0] if out else "unknown"


def run_cell(skill, brief_id, agent, date, force=False, post=False, tag="", timeout=TIMEOUT):
    brief_path = os.path.join(BENCH, "briefs", f"{brief_id}.md")
    brief = open(brief_path).read()
    dir_name = f"{brief_id}__{tag}" if tag else brief_id
    cell = os.path.join(BENCH, "runs", date, skill["name"], dir_name)
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
        proc, secs = sh(agent_cmd(agent, prompt), cwd=cell, env=env, timeout=timeout)
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
        "tag": tag,
        "agent": agent,
        "agent_version": cli_version(agent),
        "model": model_env()[0],
        "model_source": "agent config" if model_env()[0] else "unrecorded",
        "model_env": model_env()[1],
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "seconds": secs,
        "exit_code": code,
        "html_written": ok,
        "html_bytes": os.path.getsize(out_html) if ok else 0,
        "stdout_tail": tail,
    }
    open(os.path.join(cell, "meta.json"), "w").write(json.dumps(meta, ensure_ascii=False, indent=1))
    if ok and post:
        subprocess.run([sys.executable, os.path.join(BENCH, "measure.py"),
                        "--date", date, "--cell", f"{skill['name']}/{dir_name}"])
    print(f"{'ok ' if ok else 'FAIL'} {skill['name']}/{brief_id} {secs}s exit={code} bytes={meta['html_bytes']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default="all")
    ap.add_argument("--skills", default=None, help="comma separated skill names")
    ap.add_argument("--brief", default="all")
    ap.add_argument("--briefs", default=None, help="comma separated brief ids")
    ap.add_argument("--agent", default="claude")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--parallel", type=int, default=1, help="cells to run concurrently")
    ap.add_argument("--post", action="store_true", help="measure each cell as soon as it finishes")
    ap.add_argument("--repeat", type=int, default=1, help="N runs per cell, tagged r1..rN")
    ap.add_argument("--timeout", type=int, default=TIMEOUT, help="per-cell agent budget in seconds")
    args = ap.parse_args()

    skills = SKILLS["skills"]
    if args.skills:
        wanted = [x.strip() for x in args.skills.split(",") if x.strip()]
        skills = [s for s in skills if s["name"] in wanted]
        missing = set(wanted) - {s["name"] for s in skills}
        if missing:
            raise SystemExit(f"unknown skills: {sorted(missing)}")
    elif args.skill != "all":
        skills = [s for s in skills if s["name"] == args.skill]
        if not skills:
            raise SystemExit(f"unknown skill {args.skill}")

    briefs = sorted(f[:-3] for f in os.listdir(os.path.join(BENCH, "briefs")) if f.endswith(".md"))
    if args.briefs:
        wanted = [x.strip() for x in args.briefs.split(",") if x.strip()]
        briefs = [b for b in briefs if any(b.startswith(w) for w in wanted)]
        if not briefs:
            raise SystemExit("no briefs matched")
    elif args.brief != "all":
        briefs = [b for b in briefs if b == args.brief or b.startswith(args.brief)]
        if not briefs:
            raise SystemExit(f"unknown brief {args.brief}")

    os.makedirs(os.path.join(BENCH, "runs", args.date), exist_ok=True)
    json.dump({"batch": args.date, "agent": args.agent, "agent_version": cli_version(args.agent),
               "model": model_env()[0], "timeout_s": args.timeout, "repeat": args.repeat,
               "skills": [s["name"] for s in skills], "briefs": briefs,
               "started": datetime.datetime.now().isoformat(timespec="seconds")},
              open(os.path.join(BENCH, "runs", args.date, "BATCH.json"), "w"), indent=1)

    cells = [(s, b, f"r{i+1}" if args.repeat > 1 else "")
             for i in range(args.repeat) for s in skills for b in briefs]
    if args.parallel > 1:
        with ThreadPoolExecutor(max_workers=args.parallel) as ex:
            list(ex.map(lambda c: run_cell(c[0], c[1], args.agent, args.date, args.force, args.post,
                                           c[2], args.timeout), cells))
    else:
        for skill, brief, tag in cells:
            run_cell(skill, brief, args.agent, args.date, args.force, args.post, tag, args.timeout)

    # DONE marker: the gate treats a batch without finished_at as still running.
    bpath = os.path.join(BENCH, "runs", args.date, "BATCH.json")
    manifest = json.load(open(bpath)) if os.path.exists(bpath) else {"batch": args.date}
    manifest["finished_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump(manifest, open(bpath, "w"), indent=1)


if __name__ == "__main__":
    main()
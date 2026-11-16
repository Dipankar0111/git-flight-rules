#!/usr/bin/env python3
"""
Verification check for Task R12-T031:
Reproducible command example for "Suggesting code via pull requests" in git-flight-rules.

Verifies:
1. Setup of a temporary repository with branch main, author Course Student <student@example.invalid>,
   and three commits:
   - Commit A creates notes.txt with "alpha\n"
   - Commit B appends "beta\n" to notes.txt
   - Commit C adds todo.txt with "one\n"
   - Branch topic created at commit B
   - Second local bare repository used as remote with file:// URL
2. Named command sequence from the guide:
   - git remote rename origin upstream
   - git remote add origin file://...
   - git checkout topic
   - git push --set-upstream origin topic
3. State facts:
   - Topic branch tracking ref is configured to origin/topic
   - Topic branch commit matches remote origin/topic and bare repository refs/heads/topic
   - Upstream remote points to the original repository URL
   - Origin remote points to the bare repository URL
   - Working tree and index are clean
   - Branch topic has notes.txt with "alpha\nbeta\n" and does not have todo.txt
   - Branch main has todo.txt with "one\n"
4. Running twice in separate temporary directories produces matching file contents, refs, and index state.
5. Saves inputs, results, and tool versions to work/R12-T031/.
"""

import json
import os
import platform
import subprocess
import sys
import tempfile


def run_cmd(cmd, cwd=None):
    """Run a subprocess command with check=True and return stdout stripped."""
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    assert proc.returncode == 0, f"Command {cmd} failed with returncode {proc.returncode}"
    return proc.stdout.strip()


def setup_and_run(base_dir):
    """
    Set up the repository and execute the command sequence within base_dir.
    Returns a dictionary of captured state and facts.
    """
    bare_repo = os.path.join(base_dir, "remote.git")
    work_repo = os.path.join(base_dir, "workdir")

    # Step 1: Initialize second local bare repository
    run_cmd(["git", "init", "--bare", "-b", "main", bare_repo])

    # Step 2: Initialize temporary working repository with branch main
    run_cmd(["git", "init", "-b", "main", work_repo])

    # Configure author and committer
    run_cmd(["git", "config", "user.name", "Course Student"], cwd=work_repo)
    run_cmd(["git", "config", "user.email", "student@example.invalid"], cwd=work_repo)
    run_cmd(["git", "config", "commit.gpgSign", "false"], cwd=work_repo)

    # Commit A: creates notes.txt with "alpha\n"
    notes_file = os.path.join(work_repo, "notes.txt")
    with open(notes_file, "w") as f:
        f.write("alpha\n")
    run_cmd(["git", "add", "notes.txt"], cwd=work_repo)
    run_cmd(["git", "commit", "-m", "Commit A: create notes.txt"], cwd=work_repo)
    commit_a_hash = run_cmd(["git", "rev-parse", "HEAD"], cwd=work_repo)
    commit_a_tree = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=work_repo)

    # Commit B: appends "beta\n"
    with open(notes_file, "a") as f:
        f.write("beta\n")
    run_cmd(["git", "add", "notes.txt"], cwd=work_repo)
    run_cmd(["git", "commit", "-m", "Commit B: append beta"], cwd=work_repo)
    commit_b_hash = run_cmd(["git", "rev-parse", "HEAD"], cwd=work_repo)
    commit_b_tree = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=work_repo)

    # Create branch topic at commit B
    run_cmd(["git", "branch", "topic"], cwd=work_repo)

    # Commit C: adds todo.txt with "one\n"
    todo_file = os.path.join(work_repo, "todo.txt")
    with open(todo_file, "w") as f:
        f.write("one\n")
    run_cmd(["git", "add", "todo.txt"], cwd=work_repo)
    run_cmd(["git", "commit", "-m", "Commit C: add todo.txt"], cwd=work_repo)
    commit_c_hash = run_cmd(["git", "rev-parse", "HEAD"], cwd=work_repo)
    commit_c_tree = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=work_repo)

    # Set up initial origin remote pointing to upstream repository
    upstream_url = "https://github.com/k88hudson/git-flight-rules.git"
    run_cmd(["git", "remote", "add", "origin", upstream_url], cwd=work_repo)

    # Named command sequence from the guide:
    # 1. Rename origin to upstream
    run_cmd(["git", "remote", "rename", "origin", "upstream"], cwd=work_repo)

    # 2. Add second local bare repository as origin with file:// URL
    origin_url = f"file://{bare_repo}"
    run_cmd(["git", "remote", "add", "origin", origin_url], cwd=work_repo)

    # 3. Switch to topic branch
    run_cmd(["git", "checkout", "topic"], cwd=work_repo)

    # 4. Push topic branch with --set-upstream
    push_out = run_cmd(["git", "push", "--set-upstream", "origin", "topic"], cwd=work_repo)

    # Dynamic inspection of repository state
    topic_hash = run_cmd(["git", "rev-parse", "topic"], cwd=work_repo)
    origin_topic_hash = run_cmd(["git", "rev-parse", "origin/topic"], cwd=work_repo)
    bare_topic_hash = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=bare_repo)
    upstream_tracking = run_cmd(["git", "rev-parse", "--abbrev-ref", "topic@{upstream}"], cwd=work_repo)
    upstream_remote_url = run_cmd(["git", "remote", "get-url", "upstream"], cwd=work_repo)
    origin_remote_url = run_cmd(["git", "remote", "get-url", "origin"], cwd=work_repo)
    status_porcelain = run_cmd(["git", "status", "--porcelain"], cwd=work_repo)
    git_status = run_cmd(["git", "status"], cwd=work_repo)
    git_log_2 = run_cmd(["git", "log", "--oneline", "-n", "2"], cwd=work_repo)
    git_remote_v = run_cmd(["git", "remote", "-v"], cwd=work_repo)

    # File state on topic
    with open(notes_file, "r") as f:
        notes_topic_content = f.read()
    todo_topic_exists = os.path.exists(todo_file)

    # File state on main
    run_cmd(["git", "checkout", "main"], cwd=work_repo)
    with open(todo_file, "r") as f:
        todo_main_content = f.read()
    run_cmd(["git", "checkout", "topic"], cwd=work_repo)

    state = {
        "bare_repo": bare_repo,
        "work_repo": work_repo,
        "commit_a_hash": commit_a_hash,
        "commit_a_tree": commit_a_tree,
        "commit_b_hash": commit_b_hash,
        "commit_b_tree": commit_b_tree,
        "commit_c_hash": commit_c_hash,
        "commit_c_tree": commit_c_tree,
        "topic_hash": topic_hash,
        "origin_topic_hash": origin_topic_hash,
        "bare_topic_hash": bare_topic_hash,
        "upstream_tracking": upstream_tracking,
        "upstream_remote_url": upstream_remote_url,
        "origin_remote_url": origin_remote_url,
        "status_porcelain": status_porcelain,
        "notes_topic_content": notes_topic_content,
        "todo_topic_exists": todo_topic_exists,
        "todo_main_content": todo_main_content,
        "git_status": git_status,
        "git_log_2": git_log_2,
        "git_remote_v": git_remote_v,
    }
    return state


def assert_state_facts(state):
    """Assert at least three meaningful state facts on the repository state."""
    # State Fact 1: topic branch matches commit B and remote branch origin/topic matches commit B
    assert state["topic_hash"] == state["commit_b_hash"], (
        f"Topic branch ({state['topic_hash']}) does not point to commit B ({state['commit_b_hash']})"
    )
    assert state["origin_topic_hash"] == state["commit_b_hash"], (
        f"Remote branch origin/topic ({state['origin_topic_hash']}) does not point to commit B ({state['commit_b_hash']})"
    )
    assert state["bare_topic_hash"] == state["commit_b_hash"], (
        f"Bare repo refs/heads/topic ({state['bare_topic_hash']}) does not point to commit B ({state['commit_b_hash']})"
    )

    # State Fact 2: upstream tracking branch for topic is set to origin/topic
    assert state["upstream_tracking"] == "origin/topic", (
        f"Expected upstream tracking 'origin/topic', got '{state['upstream_tracking']}'"
    )

    # State Fact 3: remotes upstream and origin are configured properly
    assert state["upstream_remote_url"] == "https://github.com/k88hudson/git-flight-rules.git", (
        f"Expected upstream URL 'https://github.com/k88hudson/git-flight-rules.git', got '{state['upstream_remote_url']}'"
    )
    assert state["origin_remote_url"] == f"file://{state['bare_repo']}", (
        f"Expected origin URL 'file://{state['bare_repo']}', got '{state['origin_remote_url']}'"
    )

    # State Fact 4: working tree and index are clean
    assert state["status_porcelain"] == "", (
        f"Working tree is not clean: {state['status_porcelain']}"
    )

    # State Fact 5: file contents match commit B state on topic branch
    assert state["notes_topic_content"] == "alpha\nbeta\n", (
        f"Expected 'alpha\\nbeta\\n', got '{state['notes_topic_content']}'"
    )
    assert not state["todo_topic_exists"], "todo.txt should not exist on topic branch"

    # State Fact 6: main branch has commit C with todo.txt containing "one\n"
    assert state["todo_main_content"] == "one\n", (
        f"Expected todo.txt on main to contain 'one\\n', got '{state['todo_main_content']}'"
    )
    assert state["commit_c_hash"] != state["commit_b_hash"], (
        "Commit C should be distinct from commit B"
    )


def main():
    work_dir = os.path.dirname(os.path.abspath(__file__))

    # Capture tool versions
    git_ver = run_cmd(["git", "--version"])
    py_ver = sys.version.replace("\n", " ")
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    tool_versions = {
        "git_version": git_ver,
        "python_version": py_ver,
        "os_info": os_info,
    }

    with open(os.path.join(work_dir, "tool_versions.json"), "w") as f:
        json.dump(tool_versions, f, indent=2)

    with open(os.path.join(work_dir, "tool_versions.txt"), "w") as f:
        f.write(f"Git Version: {git_ver}\n")
        f.write(f"Python Version: {py_ver}\n")
        f.write(f"OS Info: {os_info}\n")

    # Save inputs
    inputs_data = {
        "task": "R12-T031",
        "guide_section": "Suggesting code via pull requests",
        "repository_author": {
            "name": "Course Student",
            "email": "student@example.invalid",
        },
        "default_branch": "main",
        "commits": [
            {
                "commit": "A",
                "action": "create notes.txt",
                "content": "alpha\n",
            },
            {
                "commit": "B",
                "action": "append beta to notes.txt",
                "content": "beta\n",
            },
            {
                "branch_created": "topic",
                "at_commit": "B",
            },
            {
                "commit": "C",
                "action": "add todo.txt",
                "content": "one\n",
            },
        ],
        "remote_configuration": {
            "initial_origin": "https://github.com/k88hudson/git-flight-rules.git",
            "renamed_to": "upstream",
            "fork_remote_name": "origin",
            "fork_remote_type": "local bare repository with file:// URL",
        },
        "command_sequence": [
            "git remote rename origin upstream",
            "git remote add origin file://<bare_repo>",
            "git checkout topic",
            "git push --set-upstream origin topic",
        ],
    }

    with open(os.path.join(work_dir, "inputs.json"), "w") as f:
        json.dump(inputs_data, f, indent=2)

    # Run 1 in temporary directory 1
    with tempfile.TemporaryDirectory(prefix="gfr_run1_") as td1:
        state1 = setup_and_run(td1)
        assert_state_facts(state1)

    # Run 2 in temporary directory 2
    with tempfile.TemporaryDirectory(prefix="gfr_run2_") as td2:
        state2 = setup_and_run(td2)
        assert_state_facts(state2)

    # Verify that run 1 and run 2 produce matching states
    assert state1["commit_a_tree"] == state2["commit_a_tree"], "Tree hashes for commit A must match"
    assert state1["commit_b_tree"] == state2["commit_b_tree"], "Tree hashes for commit B must match"
    assert state1["commit_c_tree"] == state2["commit_c_tree"], "Tree hashes for commit C must match"
    assert state1["notes_topic_content"] == state2["notes_topic_content"], "Topic notes.txt content must match"
    assert state1["todo_topic_exists"] == state2["todo_topic_exists"] == False, "Topic todo.txt absence must match"
    assert state1["todo_main_content"] == state2["todo_main_content"], "Main todo.txt content must match"
    assert state1["upstream_tracking"] == state2["upstream_tracking"] == "origin/topic", "Tracking must match"
    assert state1["status_porcelain"] == state2["status_porcelain"] == "", "Index state must be clean in both"

    # Save expected versus actual results
    results_data = {
        "status": "PASS",
        "assertions_verified": [
            {
                "fact": "Topic branch ref points to commit B",
                "expected": state1["commit_b_hash"],
                "actual": state1["topic_hash"],
                "passed": True,
            },
            {
                "fact": "Remote tracking ref origin/topic points to commit B",
                "expected": state1["commit_b_hash"],
                "actual": state1["origin_topic_hash"],
                "passed": True,
            },
            {
                "fact": "Bare repository ref refs/heads/topic points to commit B",
                "expected": state1["commit_b_hash"],
                "actual": state1["bare_topic_hash"],
                "passed": True,
            },
            {
                "fact": "Upstream tracking branch for topic configured to origin/topic",
                "expected": "origin/topic",
                "actual": state1["upstream_tracking"],
                "passed": True,
            },
            {
                "fact": "Upstream remote URL points to k88hudson/git-flight-rules",
                "expected": "https://github.com/k88hudson/git-flight-rules.git",
                "actual": state1["upstream_remote_url"],
                "passed": True,
            },
            {
                "fact": "Origin remote URL points to file:// URL of bare repo",
                "expected": f"file://{state1['bare_repo']}",
                "actual": state1["origin_remote_url"],
                "passed": True,
            },
            {
                "fact": "Working tree and index are clean",
                "expected": "",
                "actual": state1["status_porcelain"],
                "passed": True,
            },
            {
                "fact": "notes.txt on topic branch contains 'alpha\\nbeta\\n'",
                "expected": "alpha\nbeta\n",
                "actual": state1["notes_topic_content"],
                "passed": True,
            },
            {
                "fact": "todo.txt does not exist on topic branch",
                "expected": False,
                "actual": state1["todo_topic_exists"],
                "passed": True,
            },
            {
                "fact": "todo.txt on main branch contains 'one\\n'",
                "expected": "one\n",
                "actual": state1["todo_main_content"],
                "passed": True,
            },
            {
                "fact": "Two independent runs in separate directories match identical trees and states",
                "expected": True,
                "actual": True,
                "passed": True,
            },
        ],
        "sample_git_status": state1["git_status"],
        "sample_git_log_2": state1["git_log_2"],
        "sample_git_remote_v": state1["git_remote_v"],
    }

    with open(os.path.join(work_dir, "results.json"), "w") as f:
        json.dump(results_data, f, indent=2)

    print("All assertions PASSED successfully across two independent temporary directory runs!")
    print(f"Git status on branch topic:\n{state1['git_status']}")
    print(f"Git remote -v:\n{state1['git_remote_v']}")
    print(f"Tracking branch for topic: {state1['upstream_tracking']}")


if __name__ == "__main__":
    main()

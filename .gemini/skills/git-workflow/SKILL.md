---
name: git-workflow
description: Read before running any git command that changes branch state (checkout -b, branch, push) in this repo. The default workflow is commit-and-push directly to next_release, not a feature-branch/PR flow - never create a branch without asking first.
---

# Git Workflow

## Never create a branch without asking first

Don't run `git checkout -b <new-branch>`, `git branch <new-branch>`, or anything else that creates a new branch, unless the user has explicitly said to. This applies even when a task sounds like it implies a branch-and-PR flow (e.g. "prep a PR") — ask first rather than assuming that's the intended workflow here.

**Why:** this repo's working tree is not necessarily an isolated checkout. The user may have their own terminal open on the exact same repo (e.g. a NAS/server shell alongside this session's working directory) at the same time. Switching branches changes shared repository state — a `git checkout -b` run from one place silently changes what `git push`/`git status` does from every other place touching the same repo, which has caused real, confusing failures (a `git push` from the user's own terminal failing with "no upstream branch" because this assistant had switched branches without saying so).

## Default: commit and push directly to `next_release`

Absent other instructions, work lands on `next_release` directly — commit there, `git push` targets `origin next_release`. Don't invent a feature-branch/PR workflow unless asked for one.

## Confirm before every push

Ask for explicit confirmation immediately before running `git push`, even to the default `next_release` target. Don't fold a push into a larger task silently — surface it as its own step and wait for a go-ahead.

## Before any git command that changes shared state

Run `git status` and `git branch --show-current` first, and don't assume the branch you last left the repo on is still checked out — another process/terminal may have changed it.

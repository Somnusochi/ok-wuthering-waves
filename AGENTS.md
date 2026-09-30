# Agent Instructions

## Python

- When running Python commands in this repository, use the local virtual environment if it exists.
- On Windows/PowerShell, prefer `.\.venv\Scripts\python.exe` when present.
- On POSIX shells, prefer `./.venv/bin/python` when present.
- Fall back to `python` only when no local `.venv` interpreter exists.
- Prefer invoking the interpreter directly, for example `.\.venv\Scripts\python.exe -m pytest`, instead of relying on shell activation.

## Local pyappify / exe build

The Windows local build uses `local_ok_ww` as the runnable pyappify app root. Be careful: the outer `ok-ww.exe` is only the launcher shell; the Python app code is loaded from the pyappify app repositories under `local_ok_ww\data\apps\ok-ww`.

When building or refreshing a local exe, keep all of these in sync:

- `local_ok_ww\ok-ww.exe` is the exe users should open for local testing.
- `ok-ww.exe` at the repository root may be copied for convenience, but do not treat the repository root as the pyappify runtime root.
- `.codex\local-source` is the local git source referenced by the Local profile.
- `local_ok_ww\data\apps\ok-ww\repo` is the internal git repo used by pyappify.
- `local_ok_ww\data\apps\ok-ww\working` is the runtime working tree copied from the internal repo.
- `local_ok_ww\data\apps\ok-ww\app.json` controls the installed version/profile.

Before launching a local build, verify the app is pinned to the Local profile:

- `local_ok_ww\pyappify.yml`
- `.codex\local-source\pyappify.yml`
- `local_ok_ww\data\apps\ok-ww\repo\pyappify.yml`
- `local_ok_ww\data\apps\ok-ww\working\pyappify.yml`

All four must contain only the Local profile:

```yaml
name: "ok-ww"
uac: true
profiles:
  - name: "Local"
    git_url: "D:/coding/ok-wuthering-waves/.codex/local-source"
    admin: true
    main_script: "main.py"
    requires_python: "3.12"
    requirements: "requirements.txt"
    use_pythonw: true
    show_add_defender: true
```

Do not allow local build config to fall back to upstream profiles such as `China` or `Global`; that makes the app checkout online releases such as `v3.4.x` instead of the local source.

Required local packaging flow:

1. Preserve unrelated user changes in the main repository. Do not commit or revert them unless explicitly asked. Before merging or pushing, compare the local branch against both remotes so the scope is explicit:

```powershell
git log --oneline --decorate origin/master..HEAD
git diff --stat origin/master..HEAD
git log --oneline --decorate master..upstream/master
git diff --stat upstream/master..HEAD
```

If a tracked local change must be protected before merging and `git stash` fails, save that file's patch, verify it can be reversed with `git apply --check -R`, apply the reverse patch, merge, then reapply the saved patch.

2. Do not stage local packaging artifacts such as `.codex`, `local_ok_ww`, `pyappify_build`, `EBWebView`, `data`, root `ok-ww.exe`, desktop screenshots, or temporary patch files into the main repository unless the user explicitly asks for those artifacts.
3. Copy tracked project files into `.codex\local-source`, `local_ok_ww\data\apps\ok-ww\repo`, and `local_ok_ww\data\apps\ok-ww\working`.
4. After copying tracked files, overwrite `pyappify.yml` in all three target trees with `local_ok_ww\pyappify.yml` so the Local profile is preserved.
5. Ensure a `pyappify` helper package exists in both `.codex\local-source\pyappify` and `local_ok_ww\data\apps\ok-ww\repo\pyappify`. If needed, restore it from `local_ok_ww\data\apps\ok-ww\python\Lib\site-packages\pyappify`.
6. For the local pyappify source only, do not commit submodule gitlinks. Remove `.gitmodules` and cached gitlinks such as `ok_templates` from `.codex\local-source` and `local_ok_ww\data\apps\ok-ww\repo` before tagging, or the launcher can hang while updating submodules.
7. If `local_ok_ww\data\apps\ok-ww\python\Lib\site-packages\ok` contains a patched ok-script dependency, remove stale `local_ok_ww\data\apps\ok-ww\working\ok` before verification so the working tree does not shadow the installed dependency.
8. Commit changes inside `.codex\local-source` and tag/retag the local version, for example `v0.0.18`.
9. Commit changes inside `local_ok_ww\data\apps\ok-ww\repo` and tag/retag the same local version. Make sure the internal repo tag points to the same commit as `.codex\local-source`.
10. Write `local_ok_ww\data\apps\ok-ww\app.json` as UTF-8 without BOM. Set `current_version`, `app_starting_version`, and `available_versions[0]` to the local tag, and set `current_profile` plus the sole profile name to `Local`.
11. Run Python syntax compilation with the local packaged Python when no repository `.venv` exists, for example `local_ok_ww\data\apps\ok-ww\python\python.exe`.
12. Build the launcher shell with `cargo build --release` from `pyappify_build\src-tauri`.
13. Copy `pyappify_build\src-tauri\target\release\ok-ww.exe` to `local_ok_ww\ok-ww.exe`. Optionally also copy it to the repository root for convenience.
14. Before verification, close any old `ok-ww.exe` / `pythonw.exe` process that belongs to the previous local launch. A stale backend can hide the real result of the new build. That process is elevated because `pyappify.yml` sets `uac: true` and `admin: true`, so a non-elevated `Stop-Process` or `taskkill /F` fails with `拒绝访问` (Access Denied). It is also the user's live game-automation session, so ask before killing it, then stop it with an elevated `taskkill` and warn that a UAC prompt will appear. Do not rely on the window title to tell versions apart: it reads `OK-WW v0.0.NN Local - OK-WW` only briefly during startup and then collapses to `OK-WW`. Confirm the running version from the log's `PYAPPIFY_APP_VERSION` and `pyappify_executable` lines instead.
15. Open `local_ok_ww\ok-ww.exe`, not the root exe, for local verification. This raises a second UAC prompt.

After launch, verify the log under `local_ok_ww\logs\app.YYYY-MM-DD` contains all of these:

- `PYAPPIFY_APP_PROFILE=Local`
- `PYAPPIFY_APP_VERSION=<local tag>`
- `ok:OK start`
- `MainWindow:main window __init__ done`
- `MainWindow:Window has fully displayed`

If the log shows `China`, `Global`, or an online version such as `v3.4.x`, stop and fix the local pyappify config before continuing. If the log never reaches `ok:OK start`, the backend did not start. If it reaches `ok:OK start` but not `MainWindow:main window __init__ done`, inspect the Python traceback before changing build files.

Useful local checks:

```powershell
Get-Content local_ok_ww\logs\app.$(Get-Date -Format yyyy-MM-dd) -Tail 160
Get-Content local_ok_ww\data\apps\ok-ww\app.json
$LocalTag = (Get-Content local_ok_ww\data\apps\ok-ww\app.json | ConvertFrom-Json).current_version
git --git-dir=.codex\local-source\.git --work-tree=.codex\local-source rev-parse $LocalTag
git --git-dir=local_ok_ww\data\apps\ok-ww\repo\.git --work-tree=local_ok_ww\data\apps\ok-ww\repo rev-parse $LocalTag
git --git-dir=.codex\local-source\.git --work-tree=.codex\local-source ls-tree HEAD .gitmodules ok_templates
git --git-dir=local_ok_ww\data\apps\ok-ww\repo\.git --work-tree=local_ok_ww\data\apps\ok-ww\repo ls-tree HEAD .gitmodules ok_templates

# find the previous local instance, then stop it elevated (UAC prompt).
# ExecutablePath comes back empty for an elevated process queried from a
# non-elevated shell, so take the PID from the log and confirm it is the local
# build via pyappify_executable before killing it.
$Log = "local_ok_ww\logs\app.$(Get-Date -Format yyyy-MM-dd)"
$OldPid = (Select-String -Path $Log -Pattern 'OK start id:\d+ pid:(\d+)' |
  Select-Object -Last 1).Matches[0].Groups[1].Value
(Select-String -Path $Log -Pattern 'pyappify_executable:(\S+)' |
  Select-Object -Last 1).Matches[0].Groups[1].Value
Start-Process taskkill.exe -ArgumentList '/F','/PID',$OldPid -Verb RunAs -Wait
```

Common failure modes:

- WebView shows `localhost refused`: the pyappify backend did not start. Check `local_ok_ww\logs\app.YYYY-MM-DD` first.
- `Failed to deserialize app.json`: rewrite `app.json` as UTF-8 without BOM.
- App silently switches to an online version: one of the local `pyappify.yml` files or the internal repo tag still points at upstream profiles.
- Runtime loses `pyappify` imports after update: the helper package was missing from the internal repo and got deleted during repo-to-working sync.
- Launch hangs after checking out the local tag and the log stops at `Found 1 submodules ... Updating them`: the local tag still contains a submodule gitlink. Remove it from the local packaging repositories and retag.
- App starts then exits with `Unknown config type` after ok-script UI changes: a stale `working\ok` directory is shadowing the patched `site-packages\ok`. Remove the stale working copy or reinstall/copy the patched dependency consistently.
- `Stop-Process` or `taskkill /F` returns `拒绝访问` (Access Denied) on the old `pythonw`: the local app runs elevated. Stop it with `Start-Process taskkill.exe -ArgumentList '/F','/PID',$OldPid -Verb RunAs`. Never report verification results while a stale elevated instance still holds the single-instance mutex, because the new launch will not start its own backend.
- Grepping the launch log for `ERROR`, `Global`, or `v3.` produces false positives: the `ok:ok-script init` line dumps the entire config dict, which contains `global_configs` and the upstream `links` URLs. Judge the launch only by the five markers above.
- Printing translations with the packaged Python dies with `UnicodeEncodeError: 'gbk' codec can't encode character`: set `PYTHONIOENCODING=utf-8`. The catalogs are fine; only the console encoding is wrong.

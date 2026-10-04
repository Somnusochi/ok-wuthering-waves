# Agent Instructions

## Python

- When running Python commands in this repository, use the local virtual environment if it exists.
- On Windows/PowerShell, prefer `.\.venv\Scripts\python.exe` when present.
- On POSIX shells, prefer `./.venv/bin/python` when present.
- Fall back to `python` only when no local `.venv` interpreter exists.
- Prefer invoking the interpreter directly, for example `.\.venv\Scripts\python.exe -m pytest`, instead of relying on shell activation.

## Syncing upstream

`origin` is the fork, `upstream` is `ok-oldking/ok-wuthering-waves`. When merging `upstream/master` into `master`:

- First check whether there is anything to merge: `git rev-list --left-right --count master...upstream/master`. If upstream is not ahead, stop. Do not rebuild or retag the local package for nothing.
- `src/char/*`: always take upstream. Do not preserve fork-local character edits.
- Only the fork's own commits may be touched. Never rewrite or "clean up" other contributors' code or history.
- Fork-specific work that must survive every merge: the `multi_selection_dropdown` UI in `src/task/DailyTask.py`, its gettext entries, this `AGENTS.md`, the `.github/pr-assets/` screenshots, and the related tests. Since v3.7.3 this also includes `tests/TestDeathReentry.py`, whose stubs are widened for the fork's signatures, so it will conflict again whenever upstream touches that file.
- The fork widens signatures that upstream tests like to stub: `use_stamina(..., allow_double=)`, `farm_in_domain(..., max_claims=, allow_double=)` returning a 4-tuple `(finished, must_use, used, claims)`, and `farm_tacet(..., must_use=, max_claims=, allow_double=)`. A new upstream test that stubs these with a narrow `lambda` fails with `TypeError: ... got an unexpected keyword argument`. Widen the stub with `**kwargs` and match the 4-tuple in the fork's copy of that test; never weaken the fork feature just to satisfy a stub.
- Upstream's death-recovery paths `return None` (for example `farm_tacet` once `max_recovery_retries` is exceeded), while the fork's `farm_*` functions return used stamina as an `int` and `DailyTask` compares `used <= 0`. Keep the normalization in `DailyTask._run_daily_farm_target` (`return used or 0`): it stops `None` from reaching that comparison as a `TypeError`, and it leaves upstream's `return None` and its `assertIsNone` assertions untouched.
- `ok_templates` is a submodule. Take upstream's gitlink, then run `git submodule update --init ok_templates`, or the tree keeps an unstaged submodule drift.
- i18n needs care. Let the `i18n/*/LC_MESSAGES/ok.po` text catalogs three-way merge normally, then recompile every `ok.mo` from the merged `.po`:

```bash
for L in es_ES ja_JP ko_KR zh_CN zh_TW; do
  msgfmt --check-format -o i18n/$L/LC_MESSAGES/ok.mo i18n/$L/LC_MESSAGES/ok.po
done
PYTHONIOENCODING=utf-8 python -c "import gettext;print(gettext.GNUTranslations(open('i18n/zh_CN/LC_MESSAGES/ok.mo','rb')).gettext('Farm Goal'))"
```

The last command must print `刷取目标`. Never resolve the binary `.mo` conflict by just taking one side: git cannot merge `.mo`, and gettext reads only `.mo` at runtime, so a stale or upstream-only `.mo` silently discards the fork's translations and the UI falls back to English. `msgfmt` output is byte-deterministic, so recompiling yields a stable diff.

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
- `Unknown config type: multi_selection_dropdown` right after upstream bumps the `ok-script` pin in `requirements.txt`: installing the new ok-script overwrites `ConfigItemFactory.py` and drops the local patch. See "Local ok-script patch" below and re-apply it before launching.
- `Stop-Process` or `taskkill /F` returns `拒绝访问` (Access Denied) on the old `pythonw`: the local app runs elevated. Stop it with `Start-Process taskkill.exe -ArgumentList '/F','/PID',$OldPid -Verb RunAs`. Never report verification results while a stale elevated instance still holds the single-instance mutex, because the new launch will not start its own backend.
- Grepping the launch log for `ERROR`, `Global`, or `v3.` produces false positives: the `ok:ok-script init` line dumps the entire config dict, which contains `global_configs` and the upstream `links` URLs. Judge the launch only by the five markers above.
- Printing translations with the packaged Python dies with `UnicodeEncodeError: 'gbk' codec can't encode character`: set `PYTHONIOENCODING=utf-8`. The catalogs are fine; only the console encoding is wrong.

## Local ok-script patch

`src/task/DailyTask.py` uses `'type': "multi_selection_dropdown"` for 「刷什么」. That type does **not** exist in upstream ok-script — `ok-oldking/ok-script` PR #68 was never merged, so it lives only as a two-file patch inside the packaged interpreter:

- `local_ok_ww\data\apps\ok-ww\python\Lib\site-packages\ok\ui\qt\tasks\LabelAndMultiSelectionDropDown.py` (new file, not in the wheel)
- `local_ok_ww\data\apps\ok-ww\python\Lib\site-packages\ok\ui\qt\tasks\ConfigItemFactory.py` (one import plus one `elif resolved_type == 'multi_selection_dropdown':` branch)

Installing a newer ok-script replaces `ConfigItemFactory.py` with the stock file. The widget file survives because pip only removes files listed in the wheel's RECORD, but it then becomes unreachable and DailyTask fails with `Unknown config type`. Whenever a merge changes the `ok-script` pin in `requirements.txt`:

1. Back up both patched files before installing anything.
2. Compare `Requires-Dist` between the old and new wheels. If the dependency set is unchanged, install with `pip install --no-deps --force-reinstall <wheel>` so the rest of the environment is not churned.
3. Diff the stock new `ConfigItemFactory.py` against the stock old one. If they are identical, copy the backed-up patched file straight back.
4. Clear stale bytecode: `find site-packages/ok -name __pycache__ -type d -exec rm -rf {} +`.
5. Verify before launching: `grep -c multi_selection_dropdown .../ConfigItemFactory.py` must be at least 1, and a headless import (`QT_QPA_PLATFORM=offscreen`) of `LabelAndMultiSelectionDropDown` must succeed.
6. Re-check after launch. pyappify did not re-run pip on the app version change, so the patch persists once applied — but confirm it in the log rather than assuming.

Do not confuse `ok-script-fork/` (the clone of `Somnusochi/ok-script` at `0daee60`) with the live patch. That clone still uses the pre-rename `ok/gui/tasks/` path, while ok-script moved to `ok/ui/qt/`; the installed `ok/ui/qt/tasks/` copy is the adapted, authoritative one. Leftover directories under `site-packages/ok/gui/` are dead code: `ok/gui/__init__.py` installs a `_QtAliasFinder` on `sys.meta_path` that redirects every `ok.gui.*` import to `ok.ui.qt.*`, which is why upstream's `src/gui/CharacterCodeTab.py` can import `ok.gui.tasks.*` and still resolve.

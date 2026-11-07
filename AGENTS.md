# Agent Instructions

## Python

- When running Python commands in this repository, use the local virtual environment if it exists.
- On Windows/PowerShell, prefer `.\.venv\Scripts\python.exe` when present.
- On POSIX shells, prefer `./.venv/bin/python` when present.
- Fall back to `python` only when no local `.venv` interpreter exists.
- Prefer invoking the interpreter directly, for example `.\.venv\Scripts\python.exe -m pytest`, instead of relying on shell activation.

## Fork Scope (2026-11-07)

Keep only controller-triggered auto combat (R3, disabled by default) and auto
combat for single-character story/trial encounters without the usual party HUD.
Their implementation is in `src/task/AutoCombatTask.py` and
`src/util/ControllerTrigger.py`; tests are in `tests/TestControllerTrigger.py`.
Keep their necessary gettext entries and this operational build guide.
Everything else follows upstream, including characters, daily tasks, farming,
Garden, death recovery, normal dropdowns, and translations. Do not restore the
old daily multi-select UI, claim-count extensions, farming guards, their obsolete
tests, or PR screenshots. Do not reapply the old ok-script widget/factory patch.

## Syncing upstream

`origin` is the fork, `upstream` is `ok-oldking/ok-wuthering-waves`. When merging `upstream/master` into `master`:

- First check whether there is anything to merge: `git rev-list --left-right --count master...upstream/master`. If upstream is not ahead, stop. Do not rebuild or retag the local package for nothing.
- `src/char/*`: always take upstream. Do not preserve fork-local character edits.
- Only the fork's own commits may be touched. Never rewrite or "clean up" other contributors' code or history.
- Preserve only the two features listed in Fork Scope, their tests, and their necessary gettext entries. All other application files must match upstream. Do not rewrite commit history to remove retired features; remove them in a normal commit.
- Follow upstream's representation of `ok_templates`. When `git ls-tree upstream/master ok_templates` reports mode `160000`, take its gitlink and run `git submodule update --init ok_templates`. Since upstream commit `20a43c44`, it is a normal tracked directory (mode `040000`) and `.gitmodules` is removed: preserve its tracked files, and do not recreate a gitlink. Before this one-time migration, verify the old submodule is clean and back it up, then deinitialize its working directory so the merge can write the regular files.
- i18n needs care. Let the `i18n/*/LC_MESSAGES/ok.po` text catalogs three-way merge normally, then recompile every `ok.mo` from the merged `.po`:

```bash
for L in es_ES ja_JP ko_KR zh_CN zh_TW; do
  msgfmt --check-format -o i18n/$L/LC_MESSAGES/ok.mo i18n/$L/LC_MESSAGES/ok.po
done
PYTHONIOENCODING=utf-8 python -c "import gettext;print(gettext.GNUTranslations(open('i18n/zh_CN/LC_MESSAGES/ok.mo','rb')).gettext('Controller Trigger'))"
```

The last command must print `手柄触发`. Never resolve the binary `.mo` conflict by just taking one side: gettext reads `.mo` at runtime. Preserve upstream translations and add only the retained controller feature's entries. Do not restore retired daily-task translations.

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

### Safety Gate: Stage First

- Inspect real `ok-ww.exe` / `pythonw.exe` processes with sufficient read privileges before making any runtime changes. A sandboxed or non-elevated query can hide an elevated process.
- Copy the runtime and local source repo into a separate directory under `data/`. All dependency installation, source copying, asset removal, and verification steps below apply to that staged copy first, never to a running installation.
- Set `PYTHONNOUSERSITE=1` during isolated installation and tests. Do not upgrade or uninstall the user's global/Roaming packages. Use the staged interpreter when no project `.venv` exists.
- Enable `core.longpaths=true` in local packaging repositories before staging or merging files. Nested staging paths can exceed Windows MAX_PATH; preserve upstream template filenames instead of renaming them.
- Keep the current Local profile's final `git_url` in the staged configuration. Commit the package only once in the staged source, and fetch the same commit into the staged internal repo.
- Before publishing, check active processes again. If an old session exists, ask before stopping it. If permission is declined, keep the new build staged and leave all live source, dependencies, assets, app.json, and local-source tags unchanged.
- Once no old session remains, preserve current configs, fast-forward `.codex/local-source` to the staged commit, and publish the validated runtime. Check resolved absolute paths before directory moves. Keep the previous runtime as a rollback copy.
- Never repeat the 2026-10-31 failure: replacing resources under a running old process caused GardenTask to request the deleted `assets/images/38.png`.

### Packaging Steps

1. Preserve unrelated user changes in the main repository. Do not commit or revert them unless explicitly asked. Before merging or pushing, compare the local branch against both remotes so the scope is explicit:

```powershell
git log --oneline --decorate origin/master..HEAD
git diff --stat origin/master..HEAD
git log --oneline --decorate master..upstream/master
git diff --stat upstream/master..HEAD
```

If a tracked local change must be protected before merging and `git stash` fails, save that file's patch, verify it can be reversed with `git apply --check -R`, apply the reverse patch, merge, then reapply the saved patch.

2. Do not stage local packaging artifacts such as `.codex\local-source`, temporary repositories under `.codex`, `local_ok_ww`, `pyappify_build`, `EBWebView`, `data`, root `ok-ww.exe`, desktop screenshots, or temporary patch files into the main repository unless the user explicitly asks for those artifacts. Keep upstream's tracked `.codex\run.ps1` and `.codex\environments\environment.toml`; these are source files, not local packaging output.
3. Copy tracked project files into `.codex\local-source`, `local_ok_ww\data\apps\ok-ww\repo`, and `local_ok_ww\data\apps\ok-ww\working`.
4. After copying tracked files, overwrite `pyappify.yml` in all three target trees with `local_ok_ww\pyappify.yml` so the Local profile is preserved.
5. Ensure a `pyappify` helper package exists in both `.codex\local-source\pyappify` and `local_ok_ww\data\apps\ok-ww\repo\pyappify`. If needed, restore it from `local_ok_ww\data\apps\ok-ww\python\Lib\site-packages\pyappify`.
6. For the local pyappify source only, do not commit submodule gitlinks. Remove `.gitmodules` and index entries with mode `160000` from `.codex\local-source` and `local_ok_ww\data\apps\ok-ww\repo` before tagging, or the launcher can hang while updating submodules. Preserve ordinary tracked files under `ok_templates`: upstream now vendors this directory, so its mode `040000` tree must remain in both local package commits and the runtime working directory.
7. Use the stock ok-script dependency. Remove stale `working\ok` shadows and retired custom widget patches from the staged copy. With ok-script 3.x, remove incompatible old Qt distributions from the staged interpreter before installing the upstream lockfile.
8. Commit changes inside `.codex\local-source` and tag/retag the local version, for example `v0.0.18`.
9. Commit changes inside `local_ok_ww\data\apps\ok-ww\repo` and tag/retag the same local version. Make sure the internal repo tag points to the same commit as `.codex\local-source`. Committing separately in each repo yields different SHAs because the committer timestamps differ; instead commit once in `.codex\local-source`, then in the internal repo run `git fetch <abs path to>/.codex/local-source master` followed by `git merge --ff-only FETCH_HEAD`, which reproduces the identical SHA. The `--ff-only` aborts with `Please move or remove them before you merge` for files that are new in the incoming commit but still untracked locally (a prior `git reset` leaves them that way); re-stage with `git add -A`, confirm `git diff --cached FETCH_HEAD --name-only` is empty so the fast-forward provably discards nothing, then merge.
10. Write `local_ok_ww\data\apps\ok-ww\app.json` as UTF-8 without BOM. Set `current_version`, `app_starting_version`, and `available_versions[0]` to the local tag, and set `current_profile` plus the sole profile name to `Local`. For the direct-run Local package, explicitly set `auto_start: true` and `update_method: "MANUAL_UPDATE"`; pyappify 1.2.3 stores these preferences per app, not in the old global config.
11. Run Python syntax compilation with the local packaged Python when no repository `.venv` exists, for example `local_ok_ww\data\apps\ok-ww\python\python.exe`.
12. Read `config.py`'s `update_pyappify.to_version` before choosing launcher sources. Build that pyappify release, not an old cached checkout: the current application requires `v1.2.3`, and `v1.1.6` starts the GUI but cannot serve the update API. Preserve existing dirty launcher sources by creating a separate detached worktree at the required tag. Apply only local branding, UAC, and the embedded Local profile. Build with `node_modules\.bin\tauri.cmd build --no-bundle` from that worktree, which embeds the offline frontend without creating an installer. If the frontend was already built with `tsc` and `vite build`, pass `--config offline-build.json` with `{"build":{"beforeBuildCommand":""}}` to skip only that duplicate step. Do not substitute plain `cargo build --release`: it lacks Tauri's release configuration, leaves the frontend pointing at `localhost:1420`, and never starts Python. When sharing the existing target cache, set `CARGO_TARGET_DIR` to `pyappify_build\src-tauri\target`. Do not rebuild from the old checkout afterward. If sharing `node_modules`, do not let pnpm purge the shared directory.
13. Copy `pyappify_build\src-tauri\target\release\ok-ww.exe` to `local_ok_ww\ok-ww.exe`. Optionally also copy it to the repository root for convenience.
14. Before verification, close any old `ok-ww.exe` / `pythonw.exe` process that belongs to the previous local launch. A stale backend can hide the real result of the new build. That process is elevated because `pyappify.yml` sets `uac: true` and `admin: true`, so a non-elevated `Stop-Process` or `taskkill /F` fails with `拒绝访问` (Access Denied). It is also the user's live game-automation session, so ask before killing it, then stop it with an elevated `taskkill` and warn that a UAC prompt will appear. Do not rely on the window title to tell versions apart: it reads `OK-WW v0.0.NN Local - OK-WW` only briefly during startup and then collapses to `OK-WW`. Confirm the running version from the log's `PYAPPIFY_APP_VERSION` and `pyappify_executable` lines instead.
15. Open `local_ok_ww\ok-ww.exe`, not the root exe, for local verification. This raises a second UAC prompt.

After launch, verify the log under `local_ok_ww\logs\app.YYYY-MM-DD` contains all of these:

- `PYAPPIFY_APP_PROFILE=Local`
- `PYAPPIFY_APP_VERSION=<local tag>`
- `ok:OK start`
- `MainWindow:main window __init__ done`
- `MainWindow:Window has fully displayed`

Also verify `pyappify_version` matches `config.py`'s required launcher version and the update check has no unsupported-version or automatic launcher-upgrade failure. The Local application tag and launcher version are separate values.

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
- `PyAppify does not support checking for updates` or a failed automatic launcher download: check `pyappify_version` against `config.py` before changing application code. Build the required launcher release locally while preserving all four Local profiles; do not weaken upstream's version requirement.
- `Failed to deserialize app.json`: rewrite `app.json` as UTF-8 without BOM.
- App silently switches to an online version: one of the local `pyappify.yml` files or the internal repo tag still points at upstream profiles.
- Runtime loses `pyappify` imports after update: the helper package was missing from the internal repo and got deleted during repo-to-working sync.
- Launch hangs after checking out the local tag and the log stops at `Found 1 submodules ... Updating them`: the local tag still contains a submodule gitlink. Remove it from the local packaging repositories and retag.
- App starts then exits with `Unknown config type`: verify the app matches upstream except the two retained features. `multi_selection_dropdown` is retired; do not reapply its old dependency patch. Check for stale `working\ok` shadows or mismatched versions.
- `Stop-Process` or `taskkill /F` returns `拒绝访问` (Access Denied) on the old `pythonw`: the local app runs elevated. Stop it with `Start-Process taskkill.exe -ArgumentList '/F','/PID',$OldPid -Verb RunAs`. Never report verification results while a stale elevated instance still holds the single-instance mutex, because the new launch will not start its own backend.
- Grepping the launch log for `ERROR`, `Global`, or `v3.` produces false positives: the `ok:ok-script init` line dumps the entire config dict, which contains `global_configs` and the upstream `links` URLs. Judge the launch only by the five markers above.
- Printing translations with the packaged Python dies with `UnicodeEncodeError: 'gbk' codec can't encode character`: set `PYTHONIOENCODING=utf-8`. The catalogs are fine; only the console encoding is wrong.

## Stock ok-script

The application now follows upstream's Qt kit and pinned ok-script version. Do not modify its installed factory or add custom multi-selection widgets. `ok-script-fork/` is only a separate old checkout and is not a runtime dependency. Keep all dependency changes confined to the staged interpreter until publication.

The launcher's startup log may stop after the main window displays. Subsequent backend errors are in `local_ok_ww\data\apps\ok-ww\working\logs\ok-script.log`; read that file when diagnosing live task failures.

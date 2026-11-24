# AGENTS.md - Natural 2-finger scrolling

NVDA add-on that adds momentum scrolling for two-finger flicks on touch
screens. Repository is local for now; publishing to GitHub is planned.

## Build and test

```
scons            # package .nvda-addon
scons install    # build and install into %APPDATA%\nvda\addons
scons pot        # regenerate translation template
scons updatePo   # merge template into all .po files
python -m pytest tests -q
```

`xgettext.exe` and `msgfmt.exe` are committed in the repository root because
they are not on PATH on the development machine. The SCons interpreter needs
Python's `markdown` module for the readme HTML.

## Layout

- `addon/globalPlugins/naturalTwoFingerScrolling/__init__.py` - plugin,
  gesture scripts, settings panel and animation loop.
- `addon/globalPlugins/naturalTwoFingerScrolling/momentum.py` - pure math,
  no NVDA imports, covered by tests.
- `addon/locale/<lang>/LC_MESSAGES/nvda.po` - translations, tracked in git.
- `buildVars.py` - add-on metadata and the list of source files.
- Generated and git-ignored: `.mo`, `.html`, generated `.ini`, `.nvda-addon`.

## Documentation location

The canonical NVDA touch documentation - NVDA configuration, Windows settings,
gestures, cheat sheets and the deployable `.nvdaprofile` - lives outside this
repository:

`C:\Users\stefa\ownCloud\Personal\AppData\NVDATouch`

When the add-on changes anything the touch setup depends on (gestures,
swallowed gestures, pointer behaviour, calibration), update that folder first,
then the pointers in `~/admin/AGENTS.md` and here. The folder is synced through
ownCloud and is used to roll the setup out to other touch devices via
`NVDAProfileManagerCLI.exe`.

## Conventions

- Tabs for indentation, maximum line length 110 (see `flake8.ini`).
- All user-facing strings in `_()` with a `Translators:` comment above.
- Base language English; German is maintained as the author's language.
- Do not rename or move the config section `naturalTwoFingerScrolling`, it
  holds user settings.
- Gestures are bound per touch mode (`ts(text)`, `ts(object)`, `ts(browse)`),
  never with the generic `ts:` identifier, so that touch modes of other
  add-ons keep working.

## Known constraints

- NVDA resolves the mode specific gesture identifier before the generic one,
  and global plugins before `globalCommands`, so these bindings win over the
  built-in review mode gestures.
- The wheel event targets the window under the mouse pointer, which is why the
  pointer is moved to the touch point.
- Partial wheel deltas are honoured by Chromium and most Win32 apps; the
  "full notches" option covers applications that are not.

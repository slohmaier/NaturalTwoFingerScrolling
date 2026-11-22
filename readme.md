# Natural 2-finger scrolling

An NVDA add-on that gives touch screens momentum scrolling with two fingers,
similar to a phone or tablet.

The add-on follows your two fingers while they move: the content under the
fingers scrolls with them. When the fingers leave the screen, the measured
speed continues as a short gliding tail.

To do this it wraps NVDA's raw touch tracker and takes over two-finger
movement gestures. NVDA's own actions for those gestures (review mode cycling,
two-finger document navigation) do not run while the add-on is active. Taps
stay with NVDA: two-finger tap still stops speech, two-finger double tap still
opens the NVDA menu, one-finger exploration is untouched.

If the wrapping is unavailable, for example after a future NVDA change, the
add-on falls back to scrolling after the finished flick.

## Download

The latest packaged add-on is attached to the releases:

https://github.com/slohmaier/NaturalTwoFingerScrolling/releases

## Usage

Flick up or down with two fingers over the content you want to scroll. The
faster the flick, the further it goes. The content under your fingers scrolls,
not necessarily the window with the focus.

By default a flick up scrolls forward, like Android and iOS.

## Settings

The add-on adds a category "Natural 2-finger scrolling" to NVDA's settings:

- Scroll direction: natural (flick up scrolls forward) or traditional.
- Scroll speed in percent: scales the gliding tail for a given lift speed.
- Pointer behaviour: keep the pointer at the touch point, restore it after
  the glide, or leave the pointer alone.
- Send only full wheel notches: for applications that ignore partial wheel
  deltas.
- Content follows the two fingers while they move, and the sensitivity in
  pixels per wheel tick for that follow phase.

## Interaction with NVDA

The add-on binds the two-finger flick up and down gestures in the text, object
and browse touch modes, plus the sequential two-finger gestures that NVDA forms
when two quick flicks follow each other. For those sequences the direction of
the second flick wins, so a quick up-then-down scrolls backward instead of
being swallowed. NVDA's own bindings for the plain flicks, which cycle the
review modes, are therefore not executed while the add-on is active. The
review mode commands remain available and can be bound to other gestures, for
example three-finger flicks, in NVDA's Input Gestures dialog.

Two-finger tap (stop speech), two-finger double tap (NVDA menu) and
two-finger flicks left and right are not affected. Custom touch modes added by
other add-ons are not captured.

## Building

Requirements:

- SCons
- Python's `markdown` module in the interpreter that runs SCons
- gettext tools (`xgettext`, `msgfmt`); `msgfmt.exe` and `xgettext.exe` are
  bundled in the repository root for Windows

Commands:

```
scons            # build the .nvda-addon package
scons install    # build and install into the current user's NVDA
scons pot        # regenerate the translation template
scons updatePo   # merge the template into all .po files
python -m pytest tests -q
```

## Translations

All user-facing strings are wrapped in `_()` and marked with a
`Translators:` comment. The base language is English. Translation files live
in `addon/locale/<language>/LC_MESSAGES/nvda.po`; the `.mo` files and the
translated `manifest.ini` are generated during the build and are not tracked
in git.

## License

GNU General Public License version 2 or later, see `COPYING.txt`.

# Tasks

## Done

- 2026-11-22: Repository scaffolded from the LangDetectSpeech template.
- 2026-11-22: Momentum engine with velocity based tick mapping.
- 2026-11-22: Two-finger flick bindings for text, object and browse touch modes.
- 2026-11-22: Pointer movement to the touch point, optional restore.
- 2026-11-22: Settings panel and configuration section.
- 2026-11-22: Unit tests for the momentum math.
- 2026-11-22: English and German translations.
- 2026-11-22: Sequential two-finger flick bindings, direction follows the second flick.
- 2026-11-22: Recalibrated momentum: 200 px/s per tick, 2 to 15 ticks, 250 to 900 ms.
- 2026-11-22: INFO diagnostics line `NaturalScrolling:` for tuning on the device.
- 2026-11-22: 0.2.0: live touch tracking. Wraps `touchTracker.TrackerManager.update`
  to follow the fingers and `inputCore.InputManager.executeGesture` to swallow
  two-finger movement gestures. Taps stay with NVDA. Momentum tail at lift.
- 2026-11-22: First working live scrolling, marked by git tag
  `v0.2.0-first-working` (recorded as "first working natural 3 finger scroll"
  in the user's words; the implementation itself follows two fingers).
- 2026-11-22: Glide after lift fixed: session ends at the last finger, fastest
  lift velocity wins, touch hovers no longer cancel the glide, stray one-finger
  flicks after a session are swallowed, threshold lowered to 80 px/s.
- 2026-11-22: Published to GitHub:
  https://github.com/slohmaier/NaturalTwoFingerScrolling, release v0.2.0 with
  the packaged add-on attached.
- 2026-11-22: Double tap activation with click fallback for objects without an
  accessibility action (for example Windows 11 taskbar icons).
- 2026-11-22: Double tap and hold bound to a context menu at the touch point.
- 2026-11-22: Published release v0.2.1 with the packaged add-on attached.
- 2026-11-24: 0.2.2: releases touch support while the session is locked and
  restores it on unlock, so Windows can handle the lock screen swipe and PIN.
- 2026-11-24: 0.2.3: after the lock screen disappears, touch is restored at the
  sign-in screen (lock screen window class polling), so the session NVDA can
  explore and activate the PIN pad.

## Open

- Test on the ThinkPad L13 Yoga: Brave, File Explorer, Settings, Telegram, including the screen edges for exploration.
- Verify the logged velocity and tick count and tune `PIXELS_PER_TICK` and `followPixelsPerTick`.
- Check whether Brave honours partial wheel deltas; if not, use the full notch option.
- Downgrade the `NaturalScrolling:` log lines from info to debug once tuning is done.
- Verify that `enhancedTouchGestures` synth settings touch mode is not captured and that load order is irrelevant.
- Publish to the NVDA Add-on Store once the add-on feels right.
- Consider proposing kinetic touch scrolling upstream to NV Access.

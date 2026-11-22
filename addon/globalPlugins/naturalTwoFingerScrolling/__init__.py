# -*- coding: UTF-8 -*-
# Natural 2-finger scrolling: momentum scrolling for touch screens in NVDA.
# Copyright (C) 2026 Stefan Lohmaier
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.

import addonHandler

addonHandler.initTranslation()

import config
import core
import globalPluginHandler
import gui
import gui.guiHelper
import inputCore
import mouseHandler
import touchHandler
import winUser
import wx
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel
from logHandler import log
from scriptHandler import script

from . import momentum
from . import touchhook

ADDON_SECTION = "naturalTwoFingerScrolling"

#: Configuration defaults and validation rules for this add-on.
CONFIG_SPEC = {
	"direction": "option('natural', 'traditional', default='natural')",
	"speed": "integer(20, 400, default=100)",
	"maxTicks": "integer(1, 30, default=15)",
	"pointer": "option('keep', 'restore', 'off', default='keep')",
	"fullNotches": "boolean(default=False)",
	"follow": "boolean(default=True)",
	"followPixelsPerTick": "integer(20, 200, default=55)",
}

#: Translation context for the script category, matches NVDA's built-in one.
SCRCAT_TOUCH = _("Touch screen")

_DIRECTION_KEYS = ("natural", "traditional")
_POINTER_KEYS = ("keep", "restore", "off")

#: Fixed amount of wheel ticks for sequential two-finger flicks, where no
#: reliable velocity is available.
_SEQUENTIAL_TICKS = 4.0

#: Sequential two-finger gestures whose second flick points down.
_SEQUENTIAL_END_DOWN = tuple(
	"ts(%s):2finger_%s" % (mode, action)
	for mode in ("text", "object", "browse")
	for action in ("flickupthendown", "flickrightthendown", "flickleftthendown")
)

#: Sequential two-finger gestures whose second flick points up.
_SEQUENTIAL_END_UP = tuple(
	"ts(%s):2finger_%s" % (mode, action)
	for mode in ("text", "object", "browse")
	for action in ("flickdownthenup", "flickrightthenup", "flickleftthenup")
)


def _fingerVelocity(gesture):
	"""Return the averaged (vx, vy) velocity of the fingers in pixels per second."""
	vx = vy = 0.0
	count = 0
	for tracker in gesture.tracker.iterAllRawSingleTouchTrackers():
		try:
			trackerVx, trackerVy = tracker.getVelocity()
		except Exception:
			log.debugWarning("Could not read finger velocity", exc_info=True)
			continue
		vx += trackerVx
		vy += trackerVy
		count += 1
	if not count:
		return 0.0, 0.0
	return vx / count, vy / count


class NaturalScrollingPanel(SettingsPanel):
	# Translators: Title of the settings category for this add-on.
	title = _("Natural 2-finger scrolling")

	def makeSettings(self, sizer):
		settings = config.conf[ADDON_SECTION]
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)

		# Translators: Label for the scroll direction choice.
		directionLabel = _("Scroll direction:")
		self._directionChoices = [
			# Translators: Direction option, matching phone and tablet behaviour.
			_("Natural (flick up scrolls forward)"),
			# Translators: Direction option, matching the traditional desktop direction.
			_("Traditional (flick down scrolls forward)"),
		]
		self.directionChoice = helper.addLabeledControl(
			directionLabel,
			wx.Choice,
			choices=self._directionChoices,
		)
		self.directionChoice.SetSelection(_DIRECTION_KEYS.index(settings["direction"]))

		# Translators: Label for the speed spin control.
		speedLabel = _("Scroll speed in percent:")
		self.speedControl = helper.addLabeledControl(
			speedLabel,
			wx.SpinCtrl,
			min=20,
			max=400,
			initial=settings["speed"],
		)

		# Translators: Label for the pointer behaviour choice.
		pointerLabel = _("Pointer behaviour:")
		self._pointerChoices = [
			# Translators: Move the mouse pointer to the touch point and leave it there.
			_("Move to the touch point and keep it there"),
			# Translators: Move the mouse pointer to the touch point, then restore it.
			_("Move to the touch point, restore the pointer afterwards"),
			# Translators: Do not move the mouse pointer at all.
			_("Do not move the pointer"),
		]
		self.pointerChoice = helper.addLabeledControl(
			pointerLabel,
			wx.Choice,
			choices=self._pointerChoices,
		)
		self.pointerChoice.SetSelection(_POINTER_KEYS.index(settings["pointer"]))

		# Translators: Check box for applications that ignore partial wheel scrolling.
		self.fullNotchesCheckBox = helper.addItem(
			wx.CheckBox(
				self,
				label=_("Send only full wheel notches (for applications that ignore partial scrolling)"),
			),
		)
		self.fullNotchesCheckBox.SetValue(settings["fullNotches"])

		# Translators: Check box to enable live following of the fingers.
		self.followCheckBox = helper.addItem(
			wx.CheckBox(
				self,
				label=_("Content follows the two fingers while they move"),
			),
		)
		self.followCheckBox.SetValue(settings["follow"])

		# Translators: Label for the follow sensitivity spin control.
		followLabel = _("Pixels per wheel tick while following:")
		self.followPixelsControl = helper.addLabeledControl(
			followLabel,
			wx.SpinCtrl,
			min=20,
			max=200,
			initial=settings["followPixelsPerTick"],
		)

	def onSave(self):
		settings = config.conf[ADDON_SECTION]
		settings["direction"] = _DIRECTION_KEYS[self.directionChoice.GetSelection()]
		settings["speed"] = self.speedControl.GetValue()
		settings["pointer"] = _POINTER_KEYS[self.pointerChoice.GetSelection()]
		settings["fullNotches"] = self.fullNotchesCheckBox.GetValue()
		settings["follow"] = self.followCheckBox.GetValue()
		settings["followPixelsPerTick"] = self.followPixelsControl.GetValue()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		config.conf.spec[ADDON_SECTION] = CONFIG_SPEC
		self._generation = 0
		self._steps = []
		self._stepIndex = 0
		self._pendingDelta = 0.0
		self._sign = 0
		self._fullNotches = False
		self._restorePosition = None
		self._hook = touchhook.TouchHook(
			isEnabled=lambda: config.conf[ADDON_SECTION]["follow"],
			getPixelsPerTick=lambda: config.conf[ADDON_SECTION]["followPixelsPerTick"],
			onStart=self._onTouchStart,
			onLift=self._onTouchLift,
		)
		self._hook.install()
		inputCore.decide_executeGesture.register(self._onGesture)
		NVDASettingsDialog.categoryClasses.append(NaturalScrollingPanel)

	def terminate(self):
		if self._hook is not None:
			self._hook.terminate()
			self._hook = None
		inputCore.decide_executeGesture.unregister(self._onGesture)
		self._cancelAnimation()
		try:
			NVDASettingsDialog.categoryClasses.remove(NaturalScrollingPanel)
		except ValueError:
			pass
		super().terminate()

	def _onGesture(self, gesture):
		# Touch hovers fire right after the fingers lift and must not stop the
		# glide. Keyboard input and taps do.
		if isinstance(gesture, touchHandler.TouchInputGesture):
			action = gesture.tracker.action
			if action not in (touchHandler.TouchAction.TAP, touchHandler.TouchAction.TAP_AND_HOLD):
				return True
		self._cancelAnimation()
		return True

	def _cancelAnimation(self):
		self._generation += 1
		self._steps = []
		self._restorePointer()

	def _restorePointer(self):
		if self._restorePosition is None:
			return
		position, self._restorePosition = self._restorePosition, None
		try:
			winUser.setCursorPos(*position)
		except Exception:
			log.debugWarning("Could not restore the mouse pointer", exc_info=True)

	def _movePointer(self, x, y):
		settings = config.conf[ADDON_SECTION]
		if settings["pointer"] == "off":
			return
		try:
			oldPosition = winUser.getCursorPos()
			winUser.setCursorPos(x, y)
		except Exception:
			log.debugWarning("Could not move the mouse pointer", exc_info=True)
			return
		if settings["pointer"] == "restore":
			self._restorePosition = oldPosition

	def _onTouchStart(self, x, y):
		# Called from the touch thread when a two-finger session begins.
		self._cancelAnimation()
		self._movePointer(int(x), int(y))
		log.info(
			"NaturalScrolling: follow start pointer=(%d,%d) px/tick=%d"
			% (x, y, config.conf[ADDON_SECTION]["followPixelsPerTick"]),
		)

	def _onTouchLift(self, velocityY):
		# Called from the touch thread when the two fingers leave the screen.
		core.callLater(0, self._startGlideFromLift, velocityY)

	def _startGlideFromLift(self, velocityY):
		# A tap or a very slow release should not produce momentum.
		if abs(velocityY) < 80:
			log.debug("NaturalScrolling: lift too slow for a glide (%.0f px/s)" % abs(velocityY))
			return
		settings = config.conf[ADDON_SECTION]
		totalTicks = momentum.ticksForVelocity(
			velocityY,
			speedPercent=settings["speed"],
			maxTicks=settings["maxTicks"],
		)
		# Fingers moving up mean the content scrolls forward, which is a
		# negative wheel delta.
		sign = -1 if velocityY < 0 else 1
		log.info(
			"NaturalScrolling: lift v=%.0f px/s ticks=%.2f sign=%d"
			% (abs(velocityY), totalTicks, sign),
		)
		self._startGlide(totalTicks, sign)

	def _startGlide(self, totalTicks, sign):
		self._cancelAnimation()
		self._fullNotches = config.conf[ADDON_SECTION]["fullNotches"]
		self._sign = sign
		durationMs = momentum.durationForTicks(totalTicks)
		self._steps = momentum.buildSteps(totalTicks, durationMs=durationMs)
		self._stepIndex = 0
		self._pendingDelta = 0.0
		self._generation += 1
		core.callLater(momentum.INTERVAL_MS, self._step, self._generation)

	def _scroll(self, gesture, flickUp, fixedTicks=None):
		settings = config.conf[ADDON_SECTION]
		_velocityX, velocityY = _fingerVelocity(gesture)
		if fixedTicks is None:
			totalTicks = momentum.ticksForVelocity(
				velocityY,
				speedPercent=settings["speed"],
				maxTicks=settings["maxTicks"],
			)
		else:
			totalTicks = float(fixedTicks)
		natural = settings["direction"] == "natural"
		forward = flickUp if natural else not flickUp
		# Wheel up is positive and scrolls backwards, wheel down scrolls forwards.
		sign = -1 if forward else 1
		self._movePointer(gesture.x, gesture.y)
		log.info(
			"NaturalScrolling: %s mode=%s v=%.0f px/s ticks=%.2f pointer=(%d,%d)"
			% (
				gesture.identifiers[0],
				getattr(gesture, "mode", "?"),
				abs(velocityY),
				totalTicks,
				gesture.x,
				gesture.y,
			),
		)
		self._startGlide(totalTicks, sign)

	def _step(self, generation):
		if generation != self._generation or self._stepIndex >= len(self._steps):
			return
		stepTicks = self._steps[self._stepIndex]
		self._stepIndex += 1
		self._pendingDelta += stepTicks * self._sign * winUser.WHEEL_DELTA
		if self._fullNotches:
			wheelDelta = int(self._pendingDelta / winUser.WHEEL_DELTA) * winUser.WHEEL_DELTA
		else:
			wheelDelta = int(self._pendingDelta)
		self._pendingDelta -= wheelDelta
		if wheelDelta:
			try:
				mouseHandler.scrollMouseWheel(wheelDelta, isVertical=True)
			except Exception:
				log.exception("Could not send a wheel event")
				self._cancelAnimation()
				return
		if self._stepIndex < len(self._steps):
			core.callLater(momentum.INTERVAL_MS, self._step, generation)
		else:
			self._finishAnimation()

	def _finishAnimation(self):
		if self._pendingDelta:
			try:
				mouseHandler.scrollMouseWheel(int(self._pendingDelta), isVertical=True)
			except Exception:
				log.exception("Could not send the last wheel event")
		self._steps = []
		self._pendingDelta = 0.0
		self._restorePointer()

	@script(
		# Translators: Description of the two finger flick up gesture.
		description=_("Scrolls the content under the fingers forward, with momentum"),
		category=SCRCAT_TOUCH,
		gestures=(
			"ts(text):2finger_flickUp",
			"ts(object):2finger_flickUp",
			"ts(browse):2finger_flickUp",
		),
	)
	def script_scrollWithFlickUp(self, gesture):
		self._scroll(gesture, flickUp=True)

	@script(
		# Translators: Description of the two finger flick down gesture.
		description=_("Scrolls the content under the fingers backward, with momentum"),
		category=SCRCAT_TOUCH,
		gestures=(
			"ts(text):2finger_flickDown",
			"ts(object):2finger_flickDown",
			"ts(browse):2finger_flickDown",
		),
	)
	def script_scrollWithFlickDown(self, gesture):
		self._scroll(gesture, flickUp=False)

	@script(
		# Translators: Description of the sequential two finger gesture ending in a downward flick.
		description=_("Scrolls the content under the fingers backward after a quick two finger flick sequence"),
		category=SCRCAT_TOUCH,
		gestures=_SEQUENTIAL_END_DOWN,
	)
	def script_scrollWithSequentialDown(self, gesture):
		self._scroll(gesture, flickUp=False, fixedTicks=_SEQUENTIAL_TICKS)

	@script(
		# Translators: Description of the sequential two finger gesture ending in an upward flick.
		description=_("Scrolls the content under the fingers forward after a quick two finger flick sequence"),
		category=SCRCAT_TOUCH,
		gestures=_SEQUENTIAL_END_UP,
	)
	def script_scrollWithSequentialUp(self, gesture):
		self._scroll(gesture, flickUp=True, fixedTicks=_SEQUENTIAL_TICKS)

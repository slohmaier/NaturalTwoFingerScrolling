# -*- coding: UTF-8 -*-
# Natural 2-finger scrolling: live touch tracking.
# Copyright (C) 2026 Stefan Lohmaier
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.

"""Live follow layer for two-finger scrolling.

This module wraps two NVDA methods:

- ``touchTracker.TrackerManager.update`` to observe the raw finger positions
  while the fingers are on the screen, so the content can follow them.
- ``inputCore.InputManager.executeGesture`` to swallow NVDA's own two-finger
  movement gestures, so review mode cycling and document navigation do not
  run while our scrolling owns those fingers.

Taps and plurals (two-finger tap, two-finger double tap) are not swallowed.
"""

import time

import core
import inputCore
import mouseHandler
import touchHandler
import touchTracker
import winUser
from logHandler import log

from . import momentum

_MOVEMENT_ACTIONS = frozenset(
	{
		touchTracker.TouchAction.FLICK_UP,
		touchTracker.TouchAction.FLICK_DOWN,
		touchTracker.TouchAction.FLICK_LEFT,
		touchTracker.TouchAction.FLICK_RIGHT,
		touchTracker.TouchAction.HOLD,
		touchTracker.TouchAction.HOVER,
		touchTracker.TouchAction.HOVER_DOWN,
		touchTracker.TouchAction.HOVER_UP,
		touchTracker.TouchAction.FLICK_RIGHT_THEN_LEFT,
		touchTracker.TouchAction.FLICK_LEFT_THEN_RIGHT,
		touchTracker.TouchAction.FLICK_UP_THEN_DOWN,
		touchTracker.TouchAction.FLICK_DOWN_THEN_UP,
		touchTracker.TouchAction.FLICK_RIGHT_THEN_UP,
		touchTracker.TouchAction.FLICK_RIGHT_THEN_DOWN,
		touchTracker.TouchAction.FLICK_LEFT_THEN_UP,
		touchTracker.TouchAction.FLICK_LEFT_THEN_DOWN,
		touchTracker.TouchAction.FLICK_UP_THEN_RIGHT,
		touchTracker.TouchAction.FLICK_UP_THEN_LEFT,
		touchTracker.TouchAction.FLICK_DOWN_THEN_RIGHT,
		touchTracker.TouchAction.FLICK_DOWN_THEN_LEFT,
	},
)

#: Minimum time between two wheel events while following, in seconds.
_MIN_SEND_INTERVAL = 0.008


class TouchHook:
	"""Wraps NVDA's touch layer to provide live two-finger scrolling."""

	def __init__(self, isEnabled, getPixelsPerTick, onStart, onLift):
		self._isEnabled = isEnabled
		self._getPixelsPerTick = getPixelsPerTick
		self._onStart = onStart
		self._onLift = onLift
		self._originalUpdate = None
		self._originalExecuteGesture = None
		self._installed = False
		self._session = None
		self._lastTracker = None

	def install(self):
		if self._installed:
			return True
		try:
			self._originalUpdate = touchTracker.TrackerManager.update
			self._originalExecuteGesture = inputCore.InputManager.executeGesture
			hook = self
			originalUpdate = self._originalUpdate
			originalExecuteGesture = self._originalExecuteGesture

			def update(manager, ID, x, y, complete=False):
				# The completed tracker is removed by the original, so snapshot it first.
				completedTracker = manager.singleTouchTrackersByID.get(ID) if complete else None
				result = originalUpdate(manager, ID, x, y, complete)
				try:
					hook._onUpdate(manager, complete, completedTracker)
				except Exception:
					log.exception("NaturalScrolling: error while following touch")
				return result

			def executeGesture(manager, gesture):
				try:
					if hook._shouldSwallow(gesture):
						return None
				except Exception:
					log.exception("NaturalScrolling: error while filtering a gesture")
				return originalExecuteGesture(manager, gesture)

			touchTracker.TrackerManager.update = update
			inputCore.InputManager.executeGesture = executeGesture
			self._installed = True
			log.info("NaturalScrolling: live touch tracking installed")
			return True
		except Exception:
			log.exception("NaturalScrolling: could not install live touch tracking")
			self._restore()
			return False

	def terminate(self):
		self._restore()

	def _restore(self):
		if self._originalUpdate is not None:
			touchTracker.TrackerManager.update = self._originalUpdate
			self._originalUpdate = None
		if self._originalExecuteGesture is not None:
			inputCore.InputManager.executeGesture = self._originalExecuteGesture
			self._originalExecuteGesture = None
		self._installed = False

	def _shouldSwallow(self, gesture):
		if not self._installed or not self._isEnabled():
			return False
		if not isinstance(gesture, touchHandler.TouchInputGesture):
			return False
		tracker = gesture.tracker
		if tracker.numFingers != 2:
			return False
		if tracker.actionCount > 1:
			return False
		return tracker.action in _MOVEMENT_ACTIONS

	def _onUpdate(self, manager, complete, completedTracker):
		if not self._isEnabled():
			if self._session is not None:
				self._endSession()
			return
		activeTrackers = list(manager.singleTouchTrackersByID.values())
		if complete:
			self._lastTracker = completedTracker
		if len(activeTrackers) != 2:
			if self._session is not None:
				self._endSession()
			return
		averageX = sum(tracker.x for tracker in activeTrackers) / 2.0
		averageY = sum(tracker.y for tracker in activeTrackers) / 2.0
		if self._session is None:
			self._session = {
				"lastY": averageY,
				"pending": 0.0,
				"lastSend": 0.0,
				"pixelsPerTick": max(1.0, float(self._getPixelsPerTick())),
			}
			self._lastTracker = None
			try:
				self._onStart(averageX, averageY)
			except Exception:
				log.exception("NaturalScrolling: start callback failed")
			return
		deltaY = averageY - self._session["lastY"]
		self._session["lastY"] = averageY
		if not deltaY:
			return
		self._session["pending"] += momentum.unitsForMovement(
			deltaY,
			self._session["pixelsPerTick"],
		)
		wheelDelta = int(self._session["pending"])
		if not wheelDelta:
			return
		now = time.time()
		if now - self._session["lastSend"] < _MIN_SEND_INTERVAL:
			return
		self._session["lastSend"] = now
		self._session["pending"] -= wheelDelta
		try:
			mouseHandler.scrollMouseWheel(wheelDelta, isVertical=True)
		except Exception:
			log.exception("NaturalScrolling: could not send a wheel event")

	def _endSession(self):
		session, self._session = self._session, None
		if session is None:
			return
		if session["pending"]:
			try:
				mouseHandler.scrollMouseWheel(int(session["pending"]), isVertical=True)
			except Exception:
				log.exception("NaturalScrolling: could not send the last wheel event")
		velocityY = 0.0
		tracker = self._lastTracker
		self._lastTracker = None
		if tracker is not None:
			try:
				_velocityX, velocityY = tracker.getVelocity()
			except Exception:
				log.debugWarning("NaturalScrolling: could not read lift velocity", exc_info=True)
		try:
			self._onLift(velocityY)
		except Exception:
			log.exception("NaturalScrolling: lift callback failed")

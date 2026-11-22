# -*- coding: UTF-8 -*-
# Pure momentum math for the Natural 2-finger scrolling add-on.
# This module must stay free of NVDA imports so it can be tested standalone.

#: Duration base of the animation in milliseconds.
DURATION_BASE_MS = 250

#: Extra duration per wheel tick in milliseconds.
DURATION_PER_TICK_MS = 40

#: Upper limit for the animation duration in milliseconds.
DURATION_MAX_MS = 900

#: Duration of one animation step in milliseconds.
INTERVAL_MS = 16

#: Roughly how many pixels per second map to one wheel tick.
PIXELS_PER_TICK = 200.0

#: Falloff exponent. Higher values concentrate the movement at the beginning.
DECAY = 1.8

#: Wheel delta units per notch, as defined by Windows.
WHEEL_DELTA_UNITS = 120


def unitsForMovement(deltaPixels, pixelsPerTick=55.0):
	"""Convert a finger movement in pixels into wheel delta units.

	Negative input (fingers moving up) yields negative units, which scroll the
	content forward, matching the behaviour of a touch screen.
	"""
	pixels = max(1.0, float(pixelsPerTick))
	return float(deltaPixels) / pixels * WHEEL_DELTA_UNITS


def ticksForVelocity(velocityPxPerSecond, speedPercent=100.0, maxTicks=15.0):
	"""Convert a measured flick velocity into a number of wheel ticks.

	:param velocityPxPerSecond: Absolute flick speed in pixels per second.
	:param speedPercent: User configured speed scaling, 100 means unchanged.
	:param maxTicks: Upper limit for one gesture.
	:return: A float number of wheel ticks, at least 2 and at most maxTicks.
	"""
	try:
		velocity = abs(float(velocityPxPerSecond))
	except (TypeError, ValueError):
		return 2.0
	ticks = velocity / PIXELS_PER_TICK * (float(speedPercent) / 100.0)
	return max(2.0, min(float(maxTicks), ticks))


def durationForTicks(totalTicks):
	"""Return a sensible animation duration for the given amount of wheel ticks."""
	duration = DURATION_BASE_MS + int(DURATION_PER_TICK_MS * max(0.0, float(totalTicks)))
	return max(DURATION_BASE_MS, min(DURATION_MAX_MS, duration))


def buildSteps(totalTicks, durationMs=320, intervalMs=INTERVAL_MS, decay=DECAY):
	"""Split a total amount of wheel ticks into decaying per-step amounts.

	The returned list sums exactly to totalTicks and decreases monotonically,
	which produces the gliding feel after the fingers leave the screen.

	:param totalTicks: Total number of wheel ticks to distribute.
	:param durationMs: Length of the animation in milliseconds.
	:param intervalMs: Length of one step in milliseconds.
	:param decay: Falloff exponent, higher means faster deceleration.
	:return: List of floats, one per animation step.
	"""
	total = max(0.0, float(totalTicks))
	if total <= 0:
		return []
	steps = max(1, int(round(float(durationMs) / float(intervalMs))))
	weights = [(1.0 - (index / steps)) ** decay for index in range(steps)]
	weightSum = sum(weights)
	if weightSum <= 0:
		weights = [1.0]
		weightSum = 1.0
	return [total * weight / weightSum for weight in weights]

# -*- coding: UTF-8 -*-
"""Unit tests for the pure momentum math.

Run with: python -m pytest tests -q
"""

import importlib.util
import pathlib

MODULE_PATH = (
	pathlib.Path(__file__).resolve().parents[1]
	/ "addon"
	/ "globalPlugins"
	/ "naturalTwoFingerScrolling"
	/ "momentum.py"
)

spec = importlib.util.spec_from_file_location("momentum", MODULE_PATH)
momentum = importlib.util.module_from_spec(spec)
spec.loader.exec_module(momentum)


def test_ticks_have_a_minimum_and_use_absolute_speed():
	assert momentum.ticksForVelocity(0) == 2.0
	assert momentum.ticksForVelocity(-500) == momentum.ticksForVelocity(500) == 2.5


def test_ticks_grow_with_velocity():
	slow = momentum.ticksForVelocity(700)
	fast = momentum.ticksForVelocity(2100)
	assert slow < fast


def test_ticks_respect_maximum():
	assert momentum.ticksForVelocity(100000, maxTicks=15) == 15.0


def test_speed_percentage_scales_ticks():
	assert momentum.ticksForVelocity(1400, speedPercent=200) == 14.0


def test_duration_grows_with_ticks_and_is_capped():
	short = momentum.durationForTicks(2)
	long = momentum.durationForTicks(10)
	assert short < long
	assert long <= momentum.DURATION_MAX_MS
	assert momentum.durationForTicks(1000) == momentum.DURATION_MAX_MS


def test_steps_sum_to_total():
	total = 10
	steps = momentum.buildSteps(total, durationMs=momentum.durationForTicks(total))
	assert abs(sum(steps) - total) < 1e-9


def test_steps_decrease_monotonically():
	steps = momentum.buildSteps(5)
	assert all(a >= b for a, b in zip(steps, steps[1:]))


def test_empty_for_zero_ticks():
	assert momentum.buildSteps(0) == []

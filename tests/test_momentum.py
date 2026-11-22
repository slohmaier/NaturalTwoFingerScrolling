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


def test_ticks_are_clamped_to_at_least_one():
	assert momentum.ticksForVelocity(0) == 1.0
	assert momentum.ticksForVelocity(-500) == 1.0


def test_ticks_grow_with_velocity():
	slow = momentum.ticksForVelocity(700)
	fast = momentum.ticksForVelocity(2100)
	assert slow < fast


def test_ticks_respect_maximum():
	assert momentum.ticksForVelocity(100000, maxTicks=6) == 6.0


def test_speed_percentage_scales_ticks():
	assert momentum.ticksForVelocity(1400, speedPercent=200) == 4.0


def test_steps_sum_to_total():
	steps = momentum.buildSteps(6, durationMs=320, intervalMs=16)
	assert len(steps) == 20
	assert abs(sum(steps) - 6) < 1e-9


def test_steps_decrease_monotonically():
	steps = momentum.buildSteps(5)
	assert all(a >= b for a, b in zip(steps, steps[1:]))


def test_empty_for_zero_ticks():
	assert momentum.buildSteps(0) == []

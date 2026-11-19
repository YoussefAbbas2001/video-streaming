"""Starter tests — they all pass. Your job is to write the tests that FAIL (i.e. find defects).

Run:  python -m pytest -q
"""
import pytest

from rov_core.camera_manager import CameraError, CameraManager, CameraState
from rov_core.command_validator import CommandRejected, CommandValidator


@pytest.fixture
def manager():
    return CameraManager(link_capacity_mbps=100, headroom=0.7)


def test_new_camera_starts_connecting(manager):
    cam = manager.add_camera(1, 1280, 720, 30, 2.5)
    assert cam.state is CameraState.CONNECTING


def test_unknown_camera_is_rejected(manager):
    with pytest.raises(CameraError):
        manager.mark_live(42)


def test_budget_is_link_times_headroom(manager):
    assert manager.budget_mbps() == pytest.approx(70.0)


def test_live_camera_can_be_primary(manager):
    manager.add_camera(1, 1280, 720, 30, 2.5)
    manager.mark_live(1)
    manager.set_primary(1)
    assert manager.primary_is_live()


@pytest.fixture
def validator():
    v = CommandValidator(link_timeout_s=0.5)
    v.heartbeat(now_s=10.0)
    return v


def test_rejects_command_without_link():
    v = CommandValidator()
    with pytest.raises(CommandRejected):
        v.validate({"surge": 0.0}, now_s=1.0)


def test_armed_vehicle_accepts_valid_surge(validator):
    validator.arm()
    assert validator.validate({"surge": 0.5}, now_s=10.1) == {"surge": 0.5}


def test_unknown_gripper_action_rejected(validator):
    with pytest.raises(CommandRejected):
        validator.validate({"gripper": "spin"}, now_s=10.1)

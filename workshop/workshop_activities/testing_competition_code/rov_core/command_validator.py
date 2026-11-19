"""Validates pilot control commands before they are sent to the ROV (testing-competition module).

Read SPECIFICATION.md first: your tests must check the behaviour described there,
not the behaviour of this code.
"""
from __future__ import annotations

AXES = ("surge", "sway", "heave", "yaw")
GRIPPER_ACTIONS = ("open", "close", "hold")


class CommandRejected(Exception):
    """Raised when a command must not be sent to the vehicle."""


class CommandValidator:
    def __init__(self, link_timeout_s: float = 0.5):
        self.armed = False
        self.link_timeout_s = link_timeout_s
        self.last_heartbeat_s: float | None = None

    # ------------------------------------------------------------------ arming & link
    def arm(self) -> None:
        self.armed = True

    def disarm(self) -> None:
        self.armed = False

    def heartbeat(self, now_s: float) -> None:
        self.last_heartbeat_s = now_s

    def link_alive(self, now_s: float) -> bool:
        if self.last_heartbeat_s is None:
            return False
        return now_s - self.last_heartbeat_s <= self.link_timeout_s

    # ------------------------------------------------------------------ validation
    def validate(self, command: dict, now_s: float) -> dict:
        """Return a cleaned command or raise CommandRejected."""
        if not isinstance(command, dict):
            raise CommandRejected("command must be a dict")
        if not self.link_alive(now_s):
            raise CommandRejected("link lost")
        clean: dict = {}
        for axis in AXES:
            if axis not in command:
                continue
            value = command[axis]
            if not isinstance(value, (int, float)):
                raise CommandRejected(f"{axis} must be a number")
            if value > 1.0:
                raise CommandRejected(f"{axis} out of range")
            if axis in ("surge", "sway", "yaw") and not self.armed and value != 0:
                raise CommandRejected("vehicle is disarmed")
            clean[axis] = float(value)
        if "gripper" in command:
            if command["gripper"] not in GRIPPER_ACTIONS:
                raise CommandRejected("unknown gripper action")
            clean["gripper"] = command["gripper"]
        return clean

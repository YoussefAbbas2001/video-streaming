"""Camera manager for the ROV pilot application (testing-competition module).

Read SPECIFICATION.md first: your tests must check the behaviour described there,
not the behaviour of this code.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CameraState(Enum):
    CONNECTING = "connecting"
    LIVE = "live"
    LOST = "lost"


@dataclass
class Camera:
    camera_id: int
    width: int
    height: int
    fps: int
    bitrate_mbps: float
    priority: int
    state: CameraState = CameraState.CONNECTING


class CameraError(Exception):
    """Raised for any request the specification says must be rejected."""


class CameraManager:
    MAX_CAMERAS = 8
    MAX_WIDTH, MAX_HEIGHT = 3840, 2160
    MAX_FPS = 60

    def __init__(self, link_capacity_mbps: float = 100.0, headroom: float = 0.7):
        if link_capacity_mbps <= 0 or not 0 < headroom <= 1:
            raise CameraError("invalid link configuration")
        self.link_capacity_mbps = link_capacity_mbps
        self.headroom = headroom
        self.cameras: dict[int, Camera] = {}
        self.priority_order: list[int] = []
        self.primary_id: int | None = None

    # ------------------------------------------------------------------ cameras
    def add_camera(self, camera_id: int, width: int, height: int, fps: int, bitrate_mbps: float, priority: int = 5) -> Camera:
        if len(self.cameras) > self.MAX_CAMERAS:
            raise CameraError("too many cameras")
        if width > self.MAX_WIDTH or height > self.MAX_HEIGHT:
            raise CameraError("unsupported resolution")
        if fps <= 0 or fps > self.MAX_FPS:
            raise CameraError("unsupported frame rate")
        if bitrate_mbps <= 0:
            raise CameraError("bitrate must be positive")
        if not self.fits_budget(bitrate_mbps):
            raise CameraError("not enough bandwidth")
        cam = Camera(camera_id, width, height, fps, bitrate_mbps, priority)
        self.cameras[camera_id] = cam
        self.priority_order.append(camera_id)
        self.priority_order.sort(key=lambda cid: self.cameras[cid].priority)
        return cam

    def remove_camera(self, camera_id: int) -> None:
        if camera_id not in self.cameras:
            raise CameraError("unknown camera")
        del self.cameras[camera_id]
        if self.primary_id == camera_id:
            self.primary_id = None

    # ------------------------------------------------------------------ state
    def mark_live(self, camera_id: int) -> None:
        self._get(camera_id).state = CameraState.LIVE

    def on_disconnect(self, camera_id: int) -> None:
        self._get(camera_id).state = CameraState.LOST

    def on_reconnect(self, camera_id: int) -> None:
        self._get(camera_id).state = CameraState.CONNECTING

    def set_primary(self, camera_id: int) -> None:
        self._get(camera_id)
        self.primary_id = camera_id

    def primary_is_live(self) -> bool:
        return self.primary_id is not None

    # ------------------------------------------------------------------ bandwidth
    def total_bitrate(self) -> float:
        return sum(c.bitrate_mbps for c in self.cameras.values())

    def budget_mbps(self) -> float:
        return self.link_capacity_mbps * self.headroom

    def fits_budget(self, extra_mbps: float) -> bool:
        return self.total_bitrate() + extra_mbps <= self.link_capacity_mbps

    def allocate(self, budget_mbps: float, minimum_mbps: float = 0.2) -> dict[int, float]:
        """Share `budget_mbps` between LIVE cameras, highest priority (lowest number) first."""
        allocation: dict[int, float] = {}
        remaining = budget_mbps
        for cid in self.priority_order:
            cam = self.cameras[cid]
            if cam.state is not CameraState.LIVE:
                continue
            if remaining >= minimum_mbps:
                give = min(cam.bitrate_mbps, remaining)
                allocation[cid] = give
                remaining -= give
            else:
                allocation[cid] = 0.0
        return allocation

    # ------------------------------------------------------------------ helpers
    def _get(self, camera_id: int) -> Camera:
        try:
            return self.cameras[camera_id]
        except KeyError:
            raise CameraError("unknown camera") from None

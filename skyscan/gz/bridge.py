"""Gazebo transport bridge: bridges Gazebo cameras, poses, and stats to FrameHub and EventBus."""
from __future__ import annotations

import math
import os
import threading
import time
from typing import Any

import numpy as np

from skyscan.bus import EventBus
from skyscan.geo import gz_to_ned, gz_yaw_to_heading_deg
from skyscan.gz.frames import FrameHub
from skyscan.lidar import LidarHub
from skyscan.types import Frame, LidarScan, Truth
from skyscan.utils.logger import get_logger

log = get_logger("GZ/BRIDGE")


class GzBridge:
    """Subscribes to Gazebo transport topics and forwards to FrameHub and bus."""

    def __init__(self, cfg: Any, bus: EventBus, hub: FrameHub, lidar: LidarHub | None = None) -> None:
        self.cfg = cfg
        self.bus = bus
        self.hub = hub
        self.lidar = lidar
        self._lidar_seq = 0

        sim_cfg = getattr(cfg, "sim", cfg)
        self.world_name = str(getattr(sim_cfg, "world_name", "aerothon_mission"))
        self.model_name = str(getattr(sim_cfg, "model_name", "iris"))
        self.gz_partition = str(getattr(sim_cfg, "gz_partition", "") or "")

        self._node: Any = None
        self._running = False
        self._lock = threading.Lock()

        self._seqs: dict[str, int] = {}
        self._truth: Truth | None = None
        self._stats: dict[str, Any] = {
            "rtf": None,
            "sim_time": None,
            "paused": None,
            "age_s": None,
        }
        self._last_stats_t = 0.0

    def start(self) -> None:
        """Start Gazebo bridge and subscribe to topics."""
        if self._running:
            return

        try:
            from gz.transport13 import Node
            from gz.msgs10.image_pb2 import Image
            from gz.msgs10.laserscan_pb2 import LaserScan
            from gz.msgs10.pose_v_pb2 import Pose_V
            from gz.msgs10.world_stats_pb2 import WorldStatistics
        except ImportError as exc:
            log.warn(f"gz-transport not available on this system ({exc}). Sim bridge running in dummy mode.")
            self._running = True
            return

        log.info(f"Starting GzBridge for world '{self.world_name}' and model '{self.model_name}'")
        self._running = True
        if self.gz_partition:
            os.environ["GZ_PARTITION"] = self.gz_partition  # read by the transport when the Node is created
        self._node = Node()

        # Subscribe cameras
        cameras = getattr(self.cfg, "cameras", {})
        for cam_name, cam_cfg in cameras.items():
            topic_tmpl = str(getattr(cam_cfg, "topic", ""))
            topic = topic_tmpl.format(world=self.world_name, model=self.model_name)
            if topic:
                cb = self._make_cam_cb(cam_name)
                ok = self._node.subscribe(Image, topic, cb)
                log.info(f"Subscribed camera '{cam_name}' to topic '{topic}': ok={ok}")

        # Subscribe the 2D lidar (the same sweep the real sensor driver would put into the LidarHub)
        lidar_cfg = getattr(self.cfg, "lidar", None)
        lidar_topic = str(getattr(lidar_cfg, "topic", "") or "").format(world=self.world_name, model=self.model_name)
        if self.lidar is not None and lidar_topic:
            self._lidar_yaw_deg = float(getattr(lidar_cfg, "yaw_offset_deg", 0.0))
            ok_lidar = self._node.subscribe(LaserScan, lidar_topic, self._on_lidar)
            log.info(f"Subscribed lidar to '{lidar_topic}': ok={ok_lidar}")

        # Subscribe model pose
        pose_topic = f"/world/{self.world_name}/dynamic_pose/info"
        ok_pose = self._node.subscribe(Pose_V, pose_topic, self._on_pose)
        log.info(f"Subscribed model pose to '{pose_topic}': ok={ok_pose}")

        # Subscribe world stats
        stats_topic = f"/world/{self.world_name}/stats"
        ok_stats = self._node.subscribe(WorldStatistics, stats_topic, self._on_stats)
        log.info(f"Subscribed stats to '{stats_topic}': ok={ok_stats}")

    def stop(self) -> None:
        """Stop Gazebo bridge."""
        log.info("Stopping GzBridge")
        self._running = False
        with self._lock:
            self._node = None

    def truth(self) -> Truth | None:
        """Return latest ground truth pose of the vehicle."""
        with self._lock:
            return self._truth

    def world_stats(self) -> dict[str, Any]:
        """Return latest simulator statistics."""
        with self._lock:
            now = time.time()
            age = (now - self._last_stats_t) if self._last_stats_t > 0 else None
            st = dict(self._stats)
            st["age_s"] = round(age, 2) if age is not None else None
            return st

    # ───────────────────────────── Callbacks ─────────────────────────────

    def _make_cam_cb(self, cam_name: str) -> Any:
        def cb(msg: Any) -> None:
            if not self._running:
                return
            try:
                import cv2
                ch = 4 if msg.pixel_format_type == 4 else 3
                arr = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, ch)[:, :, :3]
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

                with self._lock:
                    seq = self._seqs.get(cam_name, 0) + 1
                    self._seqs[cam_name] = seq
                    sim_t = self._stats.get("sim_time")

                frame = Frame(
                    cam=cam_name,
                    seq=seq,
                    t=time.time(),
                    img=bgr,
                    sim_t=sim_t,
                )
                self.hub.put(frame)
            except Exception as exc:
                log.debug(f"Error decoding image frame for {cam_name}: {exc}")
        return cb

    def _on_lidar(self, msg: Any) -> None:
        if not self._running or self.lidar is None:
            return
        try:
            self._lidar_seq += 1
            self.lidar.put(LidarScan(
                t=time.time(),
                seq=self._lidar_seq,
                angle_min_deg=math.degrees(float(msg.angle_min)) + getattr(self, "_lidar_yaw_deg", 0.0),
                angle_step_deg=math.degrees(float(msg.angle_step)),
                ranges=[float(r) for r in msg.ranges],
                range_min=float(msg.range_min),
                range_max=float(msg.range_max),
            ))
        except Exception as exc:  # noqa: BLE001 - a bad scan must never kill the transport thread
            log.debug(f"Error decoding lidar scan: {exc}")

    def _on_pose(self, msg: Any) -> None:
        if not self._running:
            return
        now = time.time()
        for p in msg.pose:
            if p.name == self.model_name:
                x, y, z = float(p.position.x), float(p.position.y), float(p.position.z)
                q = p.orientation
                # Yaw from quaternion
                siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
                cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
                yaw_rad = math.atan2(siny_cosp, cosy_cosp)

                ned = gz_to_ned(x, y, z)
                heading = gz_yaw_to_heading_deg(yaw_rad)

                with self._lock:
                    sim_t = self._stats.get("sim_time")
                    self._truth = Truth(
                        t=now,
                        pos_gz=(x, y, z),
                        yaw_gz_rad=yaw_rad,
                        ned=ned,
                        heading_deg=heading,
                        sim_time=sim_t,
                    )
                break

    def _on_stats(self, msg: Any) -> None:
        if not self._running:
            return
        now = time.time()
        rtf = float(msg.real_time_factor) if hasattr(msg, "real_time_factor") else None
        sim_sec = float(msg.sim_time.sec) + float(msg.sim_time.nsec) / 1e9 if hasattr(msg, "sim_time") else None
        paused = bool(msg.paused) if hasattr(msg, "paused") else None

        with self._lock:
            self._last_stats_t = now
            self._stats = {
                "rtf": round(rtf, 2) if rtf is not None else None,
                "sim_time": round(sim_sec, 2) if sim_sec is not None else None,
                "paused": paused,
                "age_s": 0.0,
            }

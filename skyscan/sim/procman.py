"""Simulation process manager supervising Gazebo, ArduCopter SITL, and gzweb."""
from __future__ import annotations

import asyncio
import os
import signal
import socket
import time
from pathlib import Path
from typing import Any

import psutil

from skyscan import REPO_ROOT
from skyscan.bus import EventBus
from skyscan.config import Cfg, repo_path
from skyscan.sim.course import Course
from skyscan.types import ProcStatus, Sev
from skyscan.utils.logger import get_logger

log = get_logger("SIM/PROCMAN")


class ProcessManager:
    """Manages lifecycles of Gazebo Sim, SITL, and optional GUI/websocket processes."""

    def __init__(self, cfg: Cfg, bus: EventBus) -> None:
        self.cfg = cfg
        self.bus = bus

        sim_cfg = getattr(cfg, "sim", cfg)
        self.gz_partition = str(getattr(sim_cfg, "gz_partition", "") or "")
        self.world_name = str(getattr(sim_cfg, "world_name", "aerothon_mission"))
        self.world_file = repo_path(getattr(sim_cfg, "world_file", "sim/worlds/aerothon_mission.sdf"))
        self.models_dir = repo_path(getattr(sim_cfg, "models_dir", "sim/models"))
        self.runtime_dir = repo_path(getattr(sim_cfg, "runtime_dir", ".runtime"))
        self.start_timeout_s = float(getattr(sim_cfg, "start_timeout_s", 90.0))

        sitl_cfg = getattr(sim_cfg, "sitl", sim_cfg)
        self.sitl_binary = str(getattr(sitl_cfg, "binary", "/opt/robotics/ardupilot/build/sitl/bin/arducopter"))
        self.sitl_defaults = [repo_path(p) for p in getattr(sitl_cfg, "defaults", [])]
        self.fdm_port = int(getattr(sitl_cfg, "fdm_port", 9002))
        self.sitl_port = 5760 + 10 * int(getattr(sitl_cfg, "instance", 0))

        ws_cfg = getattr(sim_cfg, "websocket", {})
        self.ws_enabled = bool(getattr(ws_cfg, "enabled", True))
        self.ws_port = int(getattr(ws_cfg, "port", 9090))

        gui_cfg = getattr(sim_cfg, "gui", {})
        self.gui_display = str(getattr(gui_cfg, "display", ":0"))

        self._sim_state = "down"  # down | starting | up | stopping | error
        self._detail = "Sim is stopped"
        self._procs: dict[str, asyncio.subprocess.Process] = {}
        self._proc_status: dict[str, ProcStatus] = {
            "gazebo": ProcStatus(name="gazebo", state="down"),
            "sitl": ProcStatus(name="sitl", state="down"),
            "gz_ws": ProcStatus(name="gz_ws", state="down"),
            "gz_gui": ProcStatus(name="gz_gui", state="down"),
        }

        self._monitor_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    def status(self) -> dict[str, Any]:
        """Return overall sim and process status."""
        host = {
            "cpu_pct": psutil.cpu_percent(),
            "mem_pct": psutil.virtual_memory().percent,
            "load": os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0],
        }
        return {
            "sim": self._sim_state,
            "detail": self._detail,
            "procs": [ps for ps in self._proc_status.values()],
            "host": host,
        }

    async def start_sim(self) -> None:
        """Start Gazebo, SITL, and websocket server."""
        async with self._lock:
            if self._sim_state in ("starting", "up"):
                log.warn("Sim start requested but already up/starting")
                return

            log.info("Starting simulation stack (Gazebo + ArduCopter SITL)")
            self._sim_state = "starting"
            self._detail = "Initializing environment..."
            self.bus.event("SIM", "Starting simulation stack...", Sev.INFO)

            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            sitl_cwd = self.runtime_dir / "sitl"
            sitl_cwd.mkdir(parents=True, exist_ok=True)

            # Ensure world SDF exists; build if not
            if not self.world_file.exists():
                log.info(f"Generating missing world SDF at {self.world_file}")
                from sim.build_world import build_world
                build_world(out_file=self.world_file)

            # 1. Start Gazebo Sim Headless
            try:
                await self._start_gazebo()
            except Exception as exc:
                log.error(f"Gazebo startup failed: {exc}")
                self._sim_state = "error"
                self._detail = f"Gazebo failed to start: {exc}"
                self.bus.event("SIM", self._detail, Sev.ERROR)
                await self._stop_all()
                return

            # 2. Start ArduCopter SITL
            try:
                await self._start_sitl(sitl_cwd)
            except Exception as exc:
                log.error(f"SITL startup failed: {exc}")
                self._sim_state = "error"
                self._detail = f"SITL failed to start: {exc}"
                self.bus.event("SIM", self._detail, Sev.ERROR)
                await self._stop_all()
                return

            # 3. Start Websocket server if enabled
            if self.ws_enabled:
                try:
                    await self._start_ws()
                except Exception as exc:
                    log.warn(f"Websocket server failed to start: {exc}")

            self._sim_state = "up"
            self._detail = "Gazebo & SITL operational"
            self.bus.event("SIM", "Simulation stack is up and operational", Sev.GOOD)
            log.info("Simulation stack is fully up!")

            if self._monitor_task is None or self._monitor_task.done():
                self._monitor_task = asyncio.create_task(self._supervise_loop())

    async def stop_sim(self) -> None:
        """Stop all simulation processes."""
        async with self._lock:
            log.info("Stopping simulation stack")
            self._sim_state = "stopping"
            self._detail = "Stopping processes..."
            self.bus.event("SIM", "Stopping simulation processes...", Sev.INFO)
            await self._stop_all()
            self._sim_state = "down"
            self._detail = "Sim is stopped"
            self.bus.event("SIM", "Simulation stack is stopped", Sev.INFO)

    async def restart_sim(self) -> None:
        """Restart the entire simulation."""
        await self.stop_sim()
        await asyncio.sleep(1.0)
        await self.start_sim()

    async def open_gz_gui(self) -> None:
        """Launch optional native Gazebo GUI window on box display."""
        if "gz_gui" in self._procs and self._procs["gz_gui"].returncode is None:
            return
        log.info(f"Opening Gazebo GUI on display {self.gui_display}")
        env = self._gz_env()
        env["DISPLAY"] = self.gui_display
        proc = await asyncio.create_subprocess_exec(
            "gz", "sim", "-g",
            env=env,
            start_new_session=True
        )
        self._procs["gz_gui"] = proc
        self._proc_status["gz_gui"] = ProcStatus(
            name="gz_gui", state="up", pid=proc.pid, started_at=time.time()
        )

    async def close_gz_gui(self) -> None:
        """Close native Gazebo GUI window."""
        proc = self._procs.get("gz_gui")
        if proc:
            await self._kill_proc(proc)
            del self._procs["gz_gui"]
            self._proc_status["gz_gui"] = ProcStatus(name="gz_gui", state="down")

    # ───────────────────────────── Process Launchers ─────────────────────────────

    def _gz_env(self) -> dict[str, str]:
        """Environment for every gz process. The ROS-vendored gz CLI only lists the ROS install in GZ_CONFIG_PATH, which
        hides the apt-installed `gz launch` command (gz-launch7-cli, needed for the websocket server)."""
        env = os.environ.copy()
        cfgp = [p for p in env.get("GZ_CONFIG_PATH", "").split(":") if p]
        if "/usr/share/gz" not in cfgp and Path("/usr/share/gz").is_dir():
            cfgp.append("/usr/share/gz")
        env["GZ_CONFIG_PATH"] = ":".join(cfgp)
        if self.gz_partition:
            env["GZ_PARTITION"] = self.gz_partition
        # Vendored models/worlds first: SDF_PATH wins over GZ_SIM_RESOURCE_PATH, and the stock models of the same
        # name (iris_with_standoffs, gimbal_small_3d) lack the down camera. The websocket server serves model
        # meshes to the browser from the same path.
        models, worlds, root = str(self.models_dir), str(self.world_file.parent), str(REPO_ROOT)
        env["GZ_SIM_RESOURCE_PATH"] = f"{worlds}:{models}:{root}:{env.get('GZ_SIM_RESOURCE_PATH', '')}"
        env["SDF_PATH"] = f"{models}:{worlds}:{root}:{env.get('SDF_PATH', '')}"
        return env

    async def _world_iterations(self) -> int | None:
        """Gazebo iteration counter from the world stats topic, or None when nothing is published yet."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "gz", "topic", "-e", "-n", "1", "-t", f"/world/{self.world_name}/stats",
                env=self._gz_env(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=4.0)
        except (asyncio.TimeoutError, OSError):
            try:
                proc.kill()  # type: ignore[possibly-undefined]
            except Exception:  # noqa: BLE001
                pass
            return None
        for line in out.decode("utf-8", "replace").splitlines():
            if line.strip().startswith("iterations:"):
                try:
                    return int(line.split(":", 1)[1])
                except ValueError:
                    return None
        return None

    async def _wait_world_stepping(self, min_iterations: int = 1500) -> None:
        """Block until Gazebo has finished loading (sensors, rendering) and is stepping on its own.

        SITL must start AFTER this: the ArduPilot plugin makes Gazebo wait for SITL's servo packets, and a SITL that
        talks to a world that is still loading leaves it stuck at sim time 0.
        """
        self._detail = "Waiting for Gazebo to finish loading the world..."
        t0 = time.time()
        while time.time() - t0 < self.start_timeout_s:
            proc = self._procs.get("gazebo")
            if proc is not None and proc.returncode is not None:
                raise RuntimeError(f"Gazebo exited unexpectedly with code {proc.returncode}")
            it = await self._world_iterations()
            if it is not None and it >= min_iterations:
                log.info(f"Gazebo is stepping ({it} iterations after {time.time() - t0:.1f}s of waiting)")
                return
            await asyncio.sleep(0.5)
        raise TimeoutError("Timeout waiting for the Gazebo world to start stepping")

    async def _start_gazebo(self) -> None:
        self._detail = "Launching Gazebo headless..."
        env = self._gz_env()

        cmd = [
            "gz", "sim", "-s", "-r", "--headless-rendering", "-v2", str(self.world_file)
        ]
        log.info(f"Executing Gazebo: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        self._procs["gazebo"] = proc
        self._proc_status["gazebo"] = ProcStatus(
            name="gazebo", state="starting", pid=proc.pid, started_at=time.time()
        )

        asyncio.create_task(self._stream_logs("gazebo", proc))

        # Wait for plugin to bind UDP 9002
        log.info(f"Waiting for Gazebo plugin to bind UDP {self.fdm_port}...")
        t0 = time.time()
        while time.time() - t0 < self.start_timeout_s:
            if proc.returncode is not None:
                raise RuntimeError(f"Gazebo exited unexpectedly with code {proc.returncode}")
            if self._is_udp_bound(self.fdm_port):
                log.info(f"Gazebo bound UDP {self.fdm_port} after {time.time() - t0:.1f}s")
                await self._wait_world_stepping()
                self._proc_status["gazebo"].state = "up"
                return
            await asyncio.sleep(0.5)

        raise TimeoutError(f"Timeout waiting for Gazebo UDP {self.fdm_port}")

    async def _start_sitl(self, sitl_cwd: Path) -> None:
        self._detail = "Launching ArduCopter SITL..."
        defaults_arg = ",".join(str(p) for p in self.sitl_defaults if p.exists())
        cmd = [
            self.sitl_binary,
            "--model", "JSON",
            "--speedup", "1",
            "--slave", "0",
            "--sim-address=127.0.0.1",
            "-I0",
            "-w",
        ]
        if defaults_arg:
            cmd.extend(["--defaults", defaults_arg])

        log.info(f"Executing SITL: {' '.join(cmd)} in {sitl_cwd}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(sitl_cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        self._procs["sitl"] = proc
        self._proc_status["sitl"] = ProcStatus(
            name="sitl", state="starting", pid=proc.pid, started_at=time.time()
        )

        asyncio.create_task(self._stream_logs("sitl", proc))

        # Wait for SITL to open TCP 5760
        log.info(f"Waiting for SITL to listen on TCP {self.sitl_port}...")
        t0 = time.time()
        while time.time() - t0 < 30.0:
            if proc.returncode is not None:
                raise RuntimeError(f"SITL exited unexpectedly with code {proc.returncode}")
            if self._is_tcp_listening(self.sitl_port):
                self._proc_status["sitl"].state = "up"
                log.info(f"SITL listening on TCP {self.sitl_port} after {time.time() - t0:.1f}s")
                return
            await asyncio.sleep(0.5)

        raise TimeoutError(f"Timeout waiting for SITL TCP {self.sitl_port}")

    async def _start_ws(self) -> None:
        launch_file = repo_path("sim/websocket.gzlaunch")
        if not launch_file.exists():
            return
        log.info("Launching Gazebo websocket server...")
        proc = await asyncio.create_subprocess_exec(
            "gz", "launch", str(launch_file),
            env=self._gz_env(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        self._procs["gz_ws"] = proc
        self._proc_status["gz_ws"] = ProcStatus(
            name="gz_ws", state="up", pid=proc.pid, started_at=time.time()
        )
        asyncio.create_task(self._stream_logs("gz_ws", proc))

    async def _stop_all(self) -> None:
        """Stop all managed child processes."""
        for name in ("gz_gui", "gz_ws", "sitl", "gazebo"):
            proc = self._procs.get(name)
            if proc:
                await self._kill_proc(proc)
                self._proc_status[name] = ProcStatus(name=name, state="down")
        self._procs.clear()

    async def _kill_proc(self, proc: asyncio.subprocess.Process) -> None:
        """Gracefully kill process and its process group."""
        if proc.returncode is not None:
            return
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGINT)
            for _ in range(20):
                if proc.returncode is not None:
                    return
                await asyncio.sleep(0.1)
            os.killpg(pgid, signal.SIGTERM)
            for _ in range(15):
                if proc.returncode is not None:
                    return
                await asyncio.sleep(0.1)
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception as exc:
            log.debug(f"Process termination note: {exc}")

    # ───────────────────────────── Helpers & Supervisors ─────────────────────────────

    def _is_udp_bound(self, port: int) -> bool:
        """Check if UDP port is listening using ss."""
        try:
            for conn in psutil.net_connections(kind="udp"):
                if conn.laddr and conn.laddr.port == port:
                    return True
        except Exception:
            pass
        return False

    def _is_tcp_listening(self, port: int) -> bool:
        """Check if TCP port is accepting connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(("127.0.0.1", port)) == 0

    async def _stream_logs(self, name: str, proc: asyncio.subprocess.Process) -> None:
        """Read stdout and stderr lines and forward to bus."""
        batch: list[str] = []
        last_flush = time.time()

        async def read_stream(stream: asyncio.StreamReader | None) -> None:
            nonlocal last_flush
            if stream is None:
                return
            while not stream.at_eof():
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").strip()
                if not text or "JSON received:" in text:
                    continue
                batch.append(text)

                now = time.time()
                if len(batch) >= 20 or (now - last_flush >= 0.25):
                    self.bus.log_lines(name, list(batch))
                    batch.clear()
                    last_flush = now

        if proc.stdout:
            asyncio.create_task(read_stream(proc.stdout))
        if proc.stderr:
            asyncio.create_task(read_stream(proc.stderr))

    async def _supervise_loop(self) -> None:
        """Supervise process health and update CPU/memory stats."""
        while self._sim_state == "up":
            for name, proc in list(self._procs.items()):
                ps = self._proc_status.get(name)
                if ps and proc.returncode is not None:
                    ps.state = "exited"
                    ps.exit_code = proc.returncode
                    if name in ("gazebo", "sitl") and self._sim_state == "up":
                        log.error(f"Critical process {name} exited with code {proc.returncode}!")
                        self._sim_state = "error"
                        self._detail = f"{name} exited unexpectedly ({proc.returncode})"
                        self.bus.event("SIM", self._detail, Sev.CRITICAL)
                elif ps and proc.pid:
                    try:
                        p = psutil.Process(proc.pid)
                        ps.cpu_pct = p.cpu_percent()
                        ps.rss_mb = round(p.memory_info().rss / 1024 / 1024, 1)
                    except psutil.NoSuchProcess:
                        pass
            await asyncio.sleep(1.0)

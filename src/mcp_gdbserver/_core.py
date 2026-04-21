from __future__ import annotations

import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import IO, Any


@dataclass
class Breakpoint:
    id: int
    type: str
    address: str
    function: str | None = None
    filename: str | None = None
    line: int | None = None
    enabled: bool = True
    hit_count: int = 0


@dataclass
class Frame:
    level: int
    address: str
    function: str | None = None
    filename: str | None = None
    line: int | None = None


@dataclass
class GdbSession:
    session_id: str
    port: int
    gdbserver_pid: int | None = None
    host: str = "localhost"
    inferior_pid: int | None = None
    program: str | None = None
    status: str = "stopped"
    args: list[str] = field(default_factory=list)
    breakpoints: list[Breakpoint] = field(default_factory=list)
    current_frame: Frame | None = None
    thread_id: int | None = None


class GdbMI:
    def __init__(self, process: Any) -> None:
        self._process: Any = process
        self._stdin: IO[str] = process.stdin  # type: ignore[assignment]
        self._stdout = process.stdout
        self._stderr: IO[str] = process.stderr  # type: ignore[assignment]
        self._token = 0
        self._lock = threading.Lock()
        self._result_lock = threading.Lock()
        self._results: dict[int, dict[str, Any]] = {}
        self._running = True
        self._read_thread = threading.Thread(target=self._read_output, daemon=True)
        self._read_thread.start()

    def _parse_result(self, line: str) -> dict[str, Any]:
        line = line.strip()
        match = re.match(r"(\d+)(\^.*?)(\&.*)?", line)
        if match:
            token = int(match.group(1))
            result = match.group(2)
            data: dict[str, Any] = {"token": token, "result": result}
            if match.group(3):
                data["data"] = match.group(3)
            return data
        match = re.match(r"(\^.*)", line)
        if match:
            return {"result": match.group(1)}
        return {"raw": line}

    def _read_output(self) -> None:
        while self._running:
            try:
                line = self._stderr.readline()
                if not line:
                    break
                parsed = self._parse_result(line)
                with self._result_lock:
                    if "token" in parsed:
                        self._results[parsed["token"]] = parsed
            except Exception:
                pass

    def send(self, command: str) -> dict[str, Any]:
        with self._lock:
            self._token += 1
            token = self._token
            full_command = f"{token}{command}\n"
            self._stdin.write(full_command)
            self._stdin.flush()

        for _ in range(100):
            with self._result_lock:
                if token in self._results:
                    result = self._results.pop(token)
                    return result
            time.sleep(0.1)

        return {"error": "timeout"}

    def breakpoint_insert(
        self, location: str, condition: str | None = None
    ) -> dict[str, Any]:
        cmd = "-break-insert"
        if condition:
            cmd = f'{cmd} -c "{condition}"'
        cmd = f"{cmd} {location}"
        return self.send(cmd)

    def breakpoint_delete(self, breakpoint_id: int) -> dict[str, Any]:
        return self.send(f"-break-delete {breakpoint_id}")

    def breakpoint_enable(self, breakpoint_id: int) -> dict[str, Any]:
        return self.send(f"-break-enable {breakpoint_id}")

    def breakpoint_disable(self, breakpoint_id: int) -> dict[str, Any]:
        return self.send(f"-break-disable {breakpoint_id}")

    def exec_continue(self) -> dict[str, Any]:
        return self.send("-exec-continue")

    def exec_next(self) -> dict[str, Any]:
        return self.send("-exec-next")

    def exec_step(self) -> dict[str, Any]:
        return self.send("-exec-step")

    def exec_interrupt(self) -> dict[str, Any]:
        return self.send("-exec-interrupt")

    def stack_list_frames(self, max_depth: int = 10) -> dict[str, Any]:
        return self.send(f"-stack-list-frames 0 {max_depth}")

    def stack_list_variables(self) -> dict[str, Any]:
        return self.send("-stack-list-variables --all")

    def thread_list(self) -> dict[str, Any]:
        return self.send("-thread-list-ids")

    def thread_select(self, thread_id: int) -> dict[str, Any]:
        return self.send(f"-thread-select {thread_id}")

    def register_list(self) -> dict[str, Any]:
        return self.send("-data-list-register-values")

    def register_read(self, reg: str) -> dict[str, Any]:
        return self.send(f"-data-read-memory-groups registers {reg}")

    def memory_read(
        self, address: str, offset: int = 0, length: int = 64
    ) -> dict[str, Any]:
        return self.send(f"-data-read-memory {address} 1 {offset} {length}")

    def data_evaluate_expression(self, expr: str) -> dict[str, Any]:
        return self.send(f'-data-evaluate-expression "{expr}"')

    def file_exec_and_symbols(self, file: str) -> dict[str, Any]:
        return self.send(f'-file-exec-and-symbols "{file}"')

    def target_select(self, type_: str, remote_address: str) -> dict[str, Any]:
        return self.send(f"-target-select {type_} {remote_address}")

    def close(self) -> None:
        self._running = False
        try:
            self._process.terminate()
        except Exception:
            pass


class GdbDebugger:
    def __init__(self) -> None:
        self._sessions: dict[str, GdbSession] = {}
        self._session_counter = 0
        self._lock = threading.Lock()
        self._active_gdb: dict[str, GdbMI] = {}

    def start_gdbserver(
        self,
        host: str = "localhost",
        port: int = 2345,
        program: str | None = None,
        args: list[str] | None = None,
        attach_pid: int | None = None,
        multi: bool = False,
    ) -> GdbSession:
        self._session_counter += 1
        session_id = f"session_{self._session_counter}"

        cmd = ["gdbserver", f"{host}:{port}"]

        if attach_pid is not None:
            cmd.extend(["--attach", str(attach_pid)])
            if multi:
                cmd.insert(2, "--multi")
        elif multi:
            cmd.append("--multi")
        elif program:
            cmd.append(program)
            if args:
                cmd.extend(args)

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        with self._lock:
            session = GdbSession(
                session_id=session_id,
                gdbserver_pid=process.pid,
                host=host,
                port=port,
                program=program,
                args=args or [],
                status="running" if process.poll() is None else "exited",
            )
            self._sessions[session_id] = session

        return session

    def connect_gdb(
        self,
        session_id: str,
        gdb_path: str = "gdb",
    ) -> GdbMI:
        session = self.get_session(session_id)
        remote_target = f"{session.host}:{session.port}"

        cmd = [
            gdb_path,
            "-q",
            "--nx",
            "-iex",
            "set pagination off",
            "-ex",
            f"target remote {remote_target}",
        ]

        if session.program:
            cmd.insert(1, session.program)

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )

        gdb = GdbMI(process)
        self._active_gdb[session_id] = gdb
        return gdb

    def get_gdb(self, session_id: str) -> GdbMI | None:
        return self._active_gdb.get(session_id)

    def stop_session(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session not found: {session_id}")

            session = self._sessions[session_id]

            if session.gdbserver_pid is not None:
                try:
                    os.kill(session.gdbserver_pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

            if session_id in self._active_gdb:
                self._active_gdb[session_id].close()
                del self._active_gdb[session_id]

            del self._sessions[session_id]

            return {"session_id": session_id, "status": "stopped"}

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "session_id": s.session_id,
                    "status": s.status,
                    "host": s.host,
                    "port": s.port,
                    "program": s.program,
                    "gdbserver_pid": s.gdbserver_pid,
                }
                for s in self._sessions.values()
            ]

    def get_session(self, session_id: str) -> GdbSession:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session not found: {session_id}")
            return self._sessions[session_id]

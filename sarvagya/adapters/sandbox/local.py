import os
import subprocess
import tempfile
from pathlib import Path

from sarvagya.core.types import SandboxResult


class LocalSandbox:
    def __init__(self, workdir: str | None = None):
        if workdir:
            self._workdir = Path(workdir).resolve()
            self._workdir.mkdir(parents=True, exist_ok=True)
        else:
            self._workdir = Path(tempfile.mkdtemp(prefix="sarvagya_"))

    @property
    def workdir(self) -> str:
        return str(self._workdir)

    def execute(
        self,
        command: str,
        timeout: int = 120000,
        workdir: str | None = None,
    ) -> SandboxResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout / 1000,
                cwd=workdir or str(self._workdir),
            )
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            return SandboxResult(
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}",
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}ms",
            )
        except Exception as e:
            return SandboxResult(success=False, output="", error=str(e))

    def write_file(self, path: str, content: str) -> None:
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def read_file(self, path: str) -> str:
        full_path = self._resolve(path)
        if not full_path.exists():
            raise FileNotFoundError(str(full_path))
        return full_path.read_text(encoding="utf-8")

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self._workdir / p

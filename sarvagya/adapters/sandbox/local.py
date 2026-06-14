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

    def execute(self, command: str, timeout: int = 120000, workdir: str | None = None) -> SandboxResult:
        try:
            r = subprocess.run(command, shell=True, capture_output=True, text=True,
                               timeout=timeout / 1000, cwd=workdir or str(self._workdir))
            output = r.stdout
            if r.stderr:
                output += "\n" + r.stderr
            return SandboxResult(success=r.returncode == 0, output=output,
                                 error=None if r.returncode == 0 else f"Exit code: {r.returncode}")
        except subprocess.TimeoutExpired:
            return SandboxResult(success=False, output="", error=f"Command timed out after {timeout}ms")
        except Exception as e:
            return SandboxResult(success=False, output="", error=str(e))

    def write_file(self, path: str, content: str) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def read_file(self, path: str) -> str:
        p = self._resolve(path)
        if not p.exists():
            raise FileNotFoundError(str(p))
        return p.read_text(encoding="utf-8")

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        return p if p.is_absolute() else self._workdir / p

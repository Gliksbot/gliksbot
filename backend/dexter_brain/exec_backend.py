from __future__ import annotations
import time, shlex, subprocess, tempfile
from pathlib import Path
from typing import Iterator

class RunHandle:
    def __init__(self, id: str, proc: subprocess.Popen, log_path: Path):
        self.id = id
        self.proc = proc
        self.log_path = log_path

class Limits:
    def __init__(self, timeout_sec: int = 120, cpus: float = 1.0, memory: str = "1g"):
        self.timeout_sec = timeout_sec
        self.cpus = cpus
        self.memory = memory

class ExecBackend:
    name = "base"
    def run(self, pkg_zip: Path, cmd: list[str], limits: Limits) -> RunHandle:
        raise NotImplementedError
    def stream(self, handle: RunHandle) -> Iterator[dict]:
        with open(handle.log_path, 'r', encoding='utf-8') as f:
            while handle.proc.poll() is None:
                line = f.readline()
                if line:
                    yield {"event":"sandbox.stdout","text": line.rstrip()}
                else:
                    time.sleep(0.05)
            for line in f:
                yield {"event":"sandbox.stdout","text": line.rstrip()}
            yield {"event":"sandbox.exit","code": handle.proc.returncode}
    def cancel(self, handle: RunHandle) -> None:
        try:
            handle.proc.terminate()
        except Exception:
            pass

class DockerBackend(ExecBackend):
    name = "docker"
    def __init__(self, image: str, workdir: Path):
        self.image = image
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
    def run(self, pkg_zip: Path, cmd: list[str], limits: Limits) -> RunHandle:
        run_id = f"run_{int(time.time()*1000)}"
        run_dir = self.workdir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        pkg_dst = run_dir / 'pkg.zip'
        pkg_dst.write_bytes(Path(pkg_zip).read_bytes())
        log_path = run_dir / 'stdout.log'
        docker_cmd = [
            'docker','run','--rm','--network','none','--pids-limit','256',
            f'--cpus={limits.cpus}', f'--memory={limits.memory}', '--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges', '-v', f'{run_dir.as_posix()}:/run:rw',
            self.image
        ] + [*cmd]
        proc = subprocess.Popen(docker_cmd, stdout=open(log_path,'w',encoding='utf-8'), stderr=subprocess.STDOUT)
        return RunHandle(run_id, proc, log_path)

class HyperVBackend(ExecBackend):
    name = "hyperv"
    def __init__(self, vm_name: str, host_shared_dir: Path | None = None, vm_shared_dir: str = 'C:/HostShare', python_exe: str = 'python', vm_user: str | None = None, vm_password_env: str | None = None):
        self.vm_name = vm_name
        self.host_shared_dir = Path(host_shared_dir) if host_shared_dir else None
        self.vm_shared_dir = vm_shared_dir.rstrip('\\/')
        self.python_exe = python_exe
        self.vm_user = vm_user
        self.vm_password_env = vm_password_env
    def _build_credential_ps(self) -> str:
        if self.vm_user and self.vm_password_env:
            return (
                f"$sec=ConvertTo-SecureString $env:{self.vm_password_env} -AsPlainText -Force; "
                f"$cred=New-Object System.Management.Automation.PSCredential(\"{self.vm_user}\", $sec); "
            )
        return ""
    def run(self, pkg_zip: Path, cmd: list[str], limits: Limits) -> RunHandle:
        run_id = f"run_{int(time.time()*1000)}"
        tmp = Path(tempfile.mkdtemp(prefix=run_id+"_"))
        log_path = tmp / 'stdout.log'

        # Decide transport: shared folder preferred; else Copy-VMFile
        pkg_name = f"{run_id}.zip"
        if self.host_shared_dir and self.host_shared_dir.exists():
            inbox = self.host_shared_dir / 'inbox'
            inbox.mkdir(parents=True, exist_ok=True)
            host_pkg = inbox / pkg_name
            host_pkg.write_bytes(Path(pkg_zip).read_bytes())
            vm_pkg = f"{self.vm_shared_dir}/inbox/{pkg_name}".replace('\\','/')
            vm_runner = f"{self.vm_shared_dir}/runner.py".replace('\\','/')
            cred_ps = self._build_credential_ps()
            ps = (
                f"$ErrorActionPreference='Stop'; {cred_ps}"
                f"Invoke-Command -VMName {shlex.quote(self.vm_name)} "
                f"{('-Credential $cred ' if cred_ps else '')}"
                f"-ScriptBlock {{ & {self.python_exe} '{vm_runner}' --package '{vm_pkg}' }}"
            )
        else:
            # Fallback: use Copy-VMFile to place package and runner into guest (needs Guest Services)
            vm_dest_dir = f"{self.vm_shared_dir}\\inbox"
            vm_pkg_win = f"{vm_dest_dir}\\{pkg_name}"
            local_tmp_pkg = tmp / pkg_name
            local_tmp_pkg.write_bytes(Path(pkg_zip).read_bytes())
            local_runner = Path('runner.py').resolve()
            vm_runner_win = f"{self.vm_shared_dir}\\runner.py"
            cred_ps = self._build_credential_ps()
            ps = (
                "$ErrorActionPreference='Stop'; "
                f"{cred_ps}"
                # Ensure destination dir exists inside guest
                f"Invoke-Command -VMName {shlex.quote(self.vm_name)} {('-Credential $cred ' if cred_ps else '')}-ScriptBlock {{ New-Item -ItemType Directory -Force -Path '{vm_dest_dir}' | Out-Null }}; "
                # Copy runner.py into guest root share
                f"Copy-VMFile -Name {shlex.quote(self.vm_name)} -SourcePath '{local_runner.as_posix()}' -DestinationPath '{vm_runner_win}' -FileSource Host; "
                # Copy package into guest inbox
                f"Copy-VMFile -Name {shlex.quote(self.vm_name)} -SourcePath '{local_tmp_pkg.as_posix()}' -DestinationPath '{vm_pkg_win}' -FileSource Host; "
                # Run runner inside guest
                f"Invoke-Command -VMName {shlex.quote(self.vm_name)} {('-Credential $cred ' if cred_ps else '')}-ScriptBlock {{ & {self.python_exe} '{self.vm_shared_dir}/runner.py' --package '{self.vm_shared_dir}/inbox/{pkg_name}' }}"
            )

        proc = subprocess.Popen(['powershell','-NoProfile','-NonInteractive','-Command', ps],
                                stdout=open(log_path,'w',encoding='utf-8'), stderr=subprocess.STDOUT)
        return RunHandle(run_id, proc, log_path)


def choose_backend(cfg: dict) -> ExecBackend:
    sandbox = cfg.get('runtime',{}).get('sandbox',{})
    provider = sandbox.get('provider')
    if provider == 'docker':
        image = sandbox.get('docker',{}).get('image')
        workdir = sandbox.get('docker',{}).get('workdir','sandbox/run')
        if not image:
            raise RuntimeError('Docker backend configured without image')
        return DockerBackend(image=image, workdir=Path(workdir))
    if provider == 'hyperv':
        hv = sandbox.get('hyperv',{})
        vm = hv.get('vm_name')
        if not vm:
            raise RuntimeError('Hyper-V backend configured without vm_name')
        host_shared_dir = hv.get('host_shared_dir')
        vm_shared_dir = hv.get('vm_shared_dir','C:/HostShare')
        python_exe = hv.get('python_exe','python')
        vm_user = hv.get('vm_user')
        vm_password_env = hv.get('vm_password_env')
        return HyperVBackend(vm_name=vm,
                             host_shared_dir=Path(host_shared_dir) if host_shared_dir else None,
                             vm_shared_dir=vm_shared_dir,
                             python_exe=python_exe,
                             vm_user=vm_user,
                             vm_password_env=vm_password_env)
    raise RuntimeError('No valid sandbox provider configured')

"""Hyper-V based sandbox provider for Dexter.

Executes skill code inside a Windows Hyper-V guest VM using PowerShell Direct.
Assumptions:
- Host OS is Windows and running this backend.
- A VM (default name from config: DexterVM) is running and has Python available in PATH.
- A shared directory from host to guest is configured so that host path `host_shared_dir` maps to
  guest path `vm_shared_dir` (e.g. via Guest Services / enhanced session / SMB share / mapped drive).
- Environment variable DEXTER_VM_PASSWORD (or configured vm_password_env) holds the VM user's password.

Security Notes:
- Code is executed in the VM; still review outputs before promoting to production.
- Minimal privileges principle: recommend a non-administrator VM user if possible.

Fallback: If any Hyper-V specific step fails, caller should switch to Docker provider.
"""
from __future__ import annotations
import os
import platform
import shutil
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class HyperVSandbox:
    def __init__(self, sandbox_config: Dict[str, Any]):
        if platform.system() != 'Windows':
            raise RuntimeError('Hyper-V sandbox can only be used on Windows hosts.')
        self.config = sandbox_config
        hv = sandbox_config.get('hyperv', {})
        self.vm_name = hv.get('vm_name', 'DexterVM')
        self.vm_user = hv.get('vm_user', 'Administrator')
        self.vm_password_env = hv.get('vm_password_env', 'DEXTER_VM_PASSWORD')
        self.timeout_sec = hv.get('timeout_sec', 120)
        self.host_shared_dir = Path(sandbox_config.get('host_shared_dir', './vm_shared')).resolve()
        self.vm_shared_dir = hv.get('vm_shared_dir', '/sandbox/shared')  # Path inside guest
        self.python_exe = hv.get('python_exe', 'python')
        self.host_shared_dir.mkdir(parents=True, exist_ok=True)

    async def execute_skill(self, skill_code: str, test_code: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        execution_id = f"execution_{int(time.time()*1000)}"
        exec_dir = self.host_shared_dir / execution_id
        exec_dir.mkdir(exist_ok=True)
        skill_path = exec_dir / 'skill.py'
        skill_path.write_text(skill_code, encoding='utf-8')
        test_path = None
        if test_code:
            test_path = exec_dir / 'test_skill.py'
            test_path.write_text(test_code, encoding='utf-8')
        # Guest side paths
        guest_dir = f"{self.vm_shared_dir.rstrip('/')}/{execution_id}"
        run_cmd = f"{self.python_exe} {guest_dir}/skill.py"
        test_cmd = f"{self.python_exe} -m pytest {guest_dir}/test_skill.py -q" if test_code else None
        try:
            skill_result = await self._invoke_vm(run_cmd)
            test_result = None
            if test_cmd and skill_result['exit_code'] == 0:
                test_result = await self._invoke_vm(test_cmd)
            success = skill_result['exit_code'] == 0 and (test_result['exit_code'] == 0 if test_result else True)
            return {
                'success': success,
                'output': skill_result.get('stdout','') + skill_result.get('stderr',''),
                'test_success': (test_result['exit_code'] == 0) if test_result else None,
                'test_output': (test_result.get('stdout','') + test_result.get('stderr','')) if test_result else None,
                'execution_time': time.time() - start,
                'sandbox_type': 'hyperv',
                'execution_id': execution_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start,
                'sandbox_type': 'hyperv',
                'execution_id': execution_id
            }
        finally:
            # Cleanup host temp dir
            shutil.rmtree(exec_dir, ignore_errors=True)

    async def _invoke_vm(self, guest_command: str) -> Dict[str, Any]:
        password = os.environ.get(self.vm_password_env)
        if not password:
            raise RuntimeError(f"VM password env var '{self.vm_password_env}' not set")
        # PowerShell script builds credential and runs command inside VM
        ps_script = f"""
$sec = ConvertTo-SecureString '{password}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('{self.vm_user}', $sec)
Invoke-Command -VMName '{self.vm_name}' -Credential $cred -ScriptBlock {{ param($cmd) & $cmd }} -ArgumentList '{guest_command}' 2>&1 | Out-String
if ($LASTEXITCODE -ne $null) {{ exit $LASTEXITCODE }} else {{ exit 0 }}
"""
        def run_ps():
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True, text=True, timeout=self.timeout_sec
            )
            return {
                'exit_code': completed.returncode,
                'stdout': completed.stdout,
                'stderr': completed.stderr
            }
        return await asyncio.to_thread(run_ps)

    def check_health(self) -> Dict[str, Any]:
        if platform.system() != 'Windows':
            return {'healthy': False, 'provider': 'hyperv', 'error': 'Not a Windows host'}
        try:
            ps = f"(Get-VM -Name '{self.vm_name}' -ErrorAction Stop).State"
            completed = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=15)
            state = completed.stdout.strip()
            return {
                'healthy': 'Running' in state,
                'provider': 'hyperv',
                'vm_state': state or 'Unknown'
            }
        except Exception as e:
            return {'healthy': False, 'provider': 'hyperv', 'error': str(e)}

    async def prepare_environment(self) -> Dict[str, Any]:
        # Basic readiness check
        health = self.check_health()
        if not health.get('healthy'):
            return {'success': False, 'error': 'VM not healthy', 'details': health}
        return {'success': True, 'message': f"Hyper-V VM {self.vm_name} ready"}

__all__ = ['HyperVSandbox']

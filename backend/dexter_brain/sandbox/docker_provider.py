"""Docker-based sandbox provider for secure code execution."""

import asyncio
import docker
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional


class DockerSandbox:
    """Docker-based secure sandbox for code execution."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = docker.from_env()
        self.container_name = "dexter-sandbox"
        self.host_shared_dir = config.get('host_shared_dir', './vm_shared')
        self.container_shared_dir = '/sandbox/shared'
        
        # Docker-specific configuration with defaults
        docker_config = config.get('docker', {})
        self.image = docker_config.get('image', 'python:3.11-slim')
        self.memory_limit = docker_config.get('memory_limit', '256m')
        self.cpu_limit = docker_config.get('cpu_limit', 0.5)
        self.timeout_sec = docker_config.get('timeout_sec', 60)
        self.network_mode = docker_config.get('network_mode', 'none')
        
        # Ensure host shared directory exists and is absolute
        self.host_shared_dir = Path(self.host_shared_dir).resolve()
        self.host_shared_dir.mkdir(parents=True, exist_ok=True)
        
    async def execute_skill(self, skill_code: str, test_code: Optional[str] = None) -> Dict[str, Any]:
        """Execute skill code in isolated Docker container."""
        execution_start = time.time()
        
        try:
            # Create unique execution directory with absolute path
            execution_id = f"execution_{int(time.time() * 1000)}"
            execution_dir = self.host_shared_dir / execution_id
            execution_dir.mkdir(exist_ok=True)
            
            # Write skill and test files
            skill_file = execution_dir / "skill.py"
            skill_file.write_text(skill_code)
            
            test_result = None
            test_logs = ""
            
            # Write test file if provided
            if test_code:
                test_file = execution_dir / "test_skill.py"
                test_file.write_text(test_code)
            
            # Execute skill in container
            skill_result = await self._run_in_container(
                execution_dir, 
                ["python", "/sandbox/shared/skill.py"],
                execution_id
            )
            
            # Run tests if provided
            if test_code:
                test_result = await self._run_in_container(
                    execution_dir,
                    ["python", "-m", "pytest", "/sandbox/shared/test_skill.py", "-v"],
                    f"{execution_id}_test"
                )
                test_logs = test_result.get('output', '')
            
            # Cleanup execution directory
            shutil.rmtree(execution_dir, ignore_errors=True)
            
            execution_time = time.time() - execution_start
            
            return {
                "success": skill_result['exit_code'] == 0,
                "exit_code": skill_result['exit_code'],
                "output": skill_result['output'],
                "test_success": test_result['exit_code'] == 0 if test_result else None,
                "test_output": test_logs,
                "execution_time": execution_time,
                "sandbox_type": "docker",
                "container_id": skill_result.get('container_id'),
                "execution_id": execution_id
            }
            
        except Exception as e:
            # Cleanup on error
            if 'execution_dir' in locals():
                shutil.rmtree(execution_dir, ignore_errors=True)
                
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - execution_start,
                "sandbox_type": "docker",
                "execution_id": execution_id if 'execution_id' in locals() else "unknown"
            }
    
    async def _run_in_container(self, execution_dir: Path, command: list, run_id: str) -> Dict[str, Any]:
        """Run a command in a Docker container."""
        try:
            # Ensure execution directory is absolute
            execution_dir = execution_dir.resolve()
            
            # Prepare volume mount with absolute path
            volume_mount = {
                str(execution_dir): {
                    'bind': self.container_shared_dir,
                    'mode': 'rw'
                }
            }
            
            # Run container
            container = self.client.containers.run(
                self.image,
                command=command,
                volumes=volume_mount,
                working_dir=self.container_shared_dir,
                network_mode=self.network_mode,
                mem_limit=self.memory_limit,
                cpu_period=100000,
                cpu_quota=int(50000 * self.cpu_limit),  # 50% CPU * cpu_limit
                detach=True,
                remove=True,
                user="nobody",  # Run as non-root for security
                read_only=False,  # Allow writes to mounted volume
                cap_drop=["ALL"],  # Drop all capabilities
                security_opt=["no-new-privileges"]  # Prevent privilege escalation
            )
            
            # Wait for execution with timeout
            try:
                result = container.wait(timeout=self.timeout_sec)
                logs = container.logs().decode('utf-8', errors='replace')
                
                return {
                    "exit_code": result['StatusCode'],
                    "output": logs,
                    "container_id": container.id,
                    "run_id": run_id
                }
                
            except docker.errors.APIError as e:
                if container:
                    try:
                        container.kill()
                    except:
                        pass
                raise Exception(f"Container execution failed: {e}")
                
        except Exception as e:
            return {
                "exit_code": -1,
                "output": f"Container execution error: {str(e)}",
                "error": str(e),
                "run_id": run_id
            }
    
    def check_health(self) -> Dict[str, Any]:
        """Check Docker daemon health and availability."""
        try:
            # Check if Docker daemon is running
            self.client.ping()
            
            # Check if our image is available
            try:
                self.client.images.get(self.image)
                image_available = True
            except docker.errors.ImageNotFound:
                image_available = False
            
            # Get Docker info
            docker_info = self.client.info()
            
            return {
                "healthy": True,
                "provider": "docker",
                "daemon_running": True,
                "image_available": image_available,
                "image": self.image,
                "containers_running": docker_info.get('ContainersRunning', 0),
                "memory_limit": self.memory_limit,
                "cpu_limit": self.cpu_limit,
                "network_mode": self.network_mode
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "provider": "docker",
                "error": str(e),
                "daemon_running": False,
                "image_available": False
            }
    
    async def prepare_environment(self) -> Dict[str, Any]:
        """Prepare Docker environment (pull image if needed)."""
        try:
            # Try to pull the image if it doesn't exist
            try:
                self.client.images.get(self.image)
            except docker.errors.ImageNotFound:
                print(f"Pulling Docker image: {self.image}")
                self.client.images.pull(self.image)
            
            return {
                "success": True,
                "message": f"Docker environment ready with image {self.image}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to prepare Docker environment: {e}"
            }
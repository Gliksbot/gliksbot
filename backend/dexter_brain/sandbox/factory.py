"""Factory for creating sandbox instances based on configuration."""

from typing import Dict, Any
from .docker_provider import DockerSandbox


def create_sandbox(config: Dict[str, Any]):
    """Factory method to create appropriate sandbox provider."""
    
    runtime_config = config.get('runtime', {})
    sandbox_config = runtime_config.get('sandbox', {})
    provider = sandbox_config.get('provider', 'docker')
    
    if provider == 'docker':
        return DockerSandbox(sandbox_config)
    elif provider == 'hyperv':
        # For backward compatibility, could implement HyperVSandbox here
        # For now, we'll raise an error suggesting Docker
        raise ValueError(
            f"Hyper-V sandbox provider not fully supported. "
            f"Please use 'docker' provider instead. "
            f"Update your config.json: runtime.sandbox.provider = 'docker'"
        )
    else:
        raise ValueError(f"Unknown sandbox provider: {provider}. Supported providers: 'docker'")


def get_supported_providers() -> list:
    """Get list of supported sandbox providers."""
    return ['docker']


def validate_sandbox_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate sandbox configuration and return validation results."""
    
    runtime_config = config.get('runtime', {})
    sandbox_config = runtime_config.get('sandbox', {})
    provider = sandbox_config.get('provider', 'docker')
    
    validation = {
        "valid": True,
        "provider": provider,
        "errors": [],
        "warnings": []
    }
    
    if provider == 'docker':
        docker_config = sandbox_config.get('docker', {})
        
        # Check required Docker configuration
        if not docker_config.get('image'):
            validation["warnings"].append("No Docker image specified, will use default: python:3.11-slim")
        
        # Check Docker daemon availability
        try:
            import docker
            client = docker.from_env()
            client.ping()
            validation["docker_available"] = True
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Docker daemon not available: {e}")
            validation["docker_available"] = False
            
    elif provider == 'hyperv':
        validation["warnings"].append("Hyper-V provider is deprecated. Consider switching to Docker.")
        
    else:
        validation["valid"] = False
        validation["errors"].append(f"Unsupported provider: {provider}")
    
    return validation
from __future__ import annotations
import os, json
from typing import Any, Dict

class Config:
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        # materialize model slots resolving env API keys
        models = data.setdefault('models', {})
        for name, m in models.items():
            key_env = (m or {}).get('api_key_env')
            if key_env:
                m['api_key'] = os.environ.get(key_env)  # may be None; providers should handle
            m.setdefault('enabled', False)
            m.setdefault('params', {})
            m.setdefault('identity', '')
            m.setdefault('role', '')
            m.setdefault('prompt', '')
        # runtime
        rt = data.setdefault('runtime', {})
        rt.setdefault('db_path', './dexter.db')
        rt.setdefault('enable_fts', True)
        rt.setdefault('stm_ratio', 0.5)
        rt.setdefault('stm_max_bytes', 0)
        rt.setdefault('stm_min_free_bytes', 268_435_456)  # 256MB
        sb = rt.setdefault('sandbox', {})
        sb.setdefault('provider', 'hyperv')
        hv = sb.setdefault('hyperv', {})
        hv.setdefault('vm_name', 'DexterVM')
        hv.setdefault('vm_user', 'Administrator')
        hv.setdefault('vm_password_env', 'DEXTER_VM_PASSWORD')
        hv.setdefault('host_shared_dir', 'm:/gliksbot/vm_shared')
        hv.setdefault('vm_shared_dir', 'C:/HostShare')
        hv.setdefault('python_exe', 'python')
        hv.setdefault('timeout_sec', 60)
        
        # campaigns
        cp = data.setdefault('campaigns', {})
        cp.setdefault('enabled', True)
        cp.setdefault('max_active', 10)
        cp.setdefault('auto_objective_creation', True)

    @classmethod
    def load(cls, path: str) -> 'Config':
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)

    def to_json(self) -> Dict[str, Any]:
        return self._data

    @property
    def models(self) -> Dict[str, Any]:
        return self._data['models']

    @property
    def runtime(self) -> Dict[str, Any]:
        return self._data['runtime']

    @property
    def campaigns(self) -> Dict[str, Any]:
        return self._data['campaigns']

    @property
    def collaboration_contract(self) -> str:
        return self._data.get('collaboration_contract', '')

    @property
    def voting(self) -> Dict[str, Any]:
        return self._data.get('voting', {})

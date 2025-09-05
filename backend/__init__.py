"""Backend package initialization."""

# Make core modules available at package level
from . import dexter_brain
from . import main

# -----------------------------------------------------------------------------
# Backwards‑compatibility alias
#
# Some modules (or external code) may attempt to import ``dexter_brain`` as a
# top‑level package (e.g. ``import dexter_brain.config``).  When the FastAPI
# application is executed in certain contexts (such as via ``uvicorn main:app``),
# relative imports may fail and fallback imports targeting ``dexter_brain`` will
# trigger ``ModuleNotFoundError``.  To maintain compatibility and avoid such
# errors, register the ``dexter_brain`` subpackage from within ``backend`` as a
# top‑level module in ``sys.modules``.  This allows ``import dexter_brain`` to
# succeed even when the package is nested under ``backend``.
import importlib
import sys as _sys
if 'dexter_brain' not in _sys.modules:
    _sys.modules['dexter_brain'] = importlib.import_module('.dexter_brain', __name__)

__all__ = ['dexter_brain', 'main']


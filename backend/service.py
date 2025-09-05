import sys
import os
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil
import uvicorn
from pathlib import Path

class DexterService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DexterAPI"
    _svc_display_name_ = "Dexter v3 API Service"
    _svc_description_ = "Autonomous AI Skill Builder Backend Service"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
        
    def main(self):
        # Set working directory to backend folder so relative paths (e.g. for static
        # files) continue to work.  Determine the project root and ensure it is
        # on ``sys.path`` so that the ``backend`` package can be imported.  When
        # running uvicorn with a module path ("backend.main:app"), this makes
        # relative imports inside ``main.py`` resolve correctly.
        backend_dir = Path(__file__).parent
        os.chdir(backend_dir)
        root_dir = backend_dir.parent
        # Prepend the root directory to sys.path if it's not already present
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))

        # Start uvicorn server.  Use the fully qualified module name rather than
        # "main:app" to avoid ``ImportError: No module named 'dexter_brain'`` when
        # uvicorn imports the module outside of a package context.  Do not enable
        # reload in a Windows service.
        try:
            uvicorn.run(
                "backend.main:app",
                host="0.0.0.0",
                port=8080,
                reload=False,
                log_level="info"
            )
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service failed to start: {e}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(DexterService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(DexterService)

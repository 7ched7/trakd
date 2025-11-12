import sys
import servicemanager
import win32service
import win32serviceutil
from server import Server

class TrakdService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'Trakd'
    _svc_display_name_ = 'Trakd Socket Service'
    _svc_description_ = 'Trakd Socket Service'

    def __init__(self, args):
        super().__init__(args)
        self.server = Server()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.server._graceful_shutdown()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.server.run_server(is_service=True)            

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TrakdService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(TrakdService, argv=sys.argv) 
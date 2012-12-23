import os
import json
from winrm_service import WinRMWebService

def real_winrm_service():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    settings = json.load(open(config_path))
    winrm = WinRMWebService(**settings)
    return winrm
import subprocess
import re
import os


VPN_PASSWORD = os.environ['VPN_PASSWORD']
VPN_HOST = os.environ['VPN_HOST']
VPN_HUB = os.environ['VPN_HUB']

args = ['sudo', '/usr/local/vpnserver/vpncmd', VPN_HOST,
        '/SERVER', f'/HUB:{VPN_HUB}', f'/PASSWORD:{VPN_PASSWORD}', '/cmd', 'sessionlist']

sessionlist = subprocess.check_output(args).decode().split(
    '----------------+----------------------------------\n')
sessionlist.pop(0)
sessionlist[-1] = re.sub('The.command.completed.successfully.\n\n','',sessionlist[-1])

for item in sessionlist:
    print(item)
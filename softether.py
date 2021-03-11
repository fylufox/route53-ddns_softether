import subprocess
import re


def get_sessionlist(cmdpath, hostname, password, hubname):
    args = ['sudo', cmdpath, hostname,
            '/SERVER', f'/HUB:{hubname}', f'/PASSWORD:{password}', '/cmd', 'sessionlist']
    or_sessionlist = subprocess.check_output(args).decode().split(
        '----------------+----------------------------------\n')
    or_sessionlist.pop(0)
    or_sessionlist[-1] = re.sub('The.command.completed.successfully.\n\n',
                                '', or_sessionlist[-1])

    sessionlist = dict()
    for item in or_sessionlist:
        line = item.split('\n')
        session_id = re.split('\s*\|', line[0])[1]
        user_name = re.split('\s*\|', line[3])[1]
        sessionlist[session_id] = user_name

    return sessionlist


def get_sessioninfo_ip(cmdpath, hostname, password, hubname, session_id):
    args = ['sudo', cmdpath, hostname,
            '/SERVER', f'/HUB:{hubname}', f'/PASSWORD:{password}', '/cmd', 'sessionget', session_id]
    sessioninfo = subprocess.check_output(args).decode().split(
        '------------------------------------------+----------------------------------------\n')[1]
    ipaddress = re.split('\s*\|', sessioninfo.split('\n')[0])[1]
    return ipaddress

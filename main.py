import subprocess
import re
import os


VPN_PASSWORD = os.environ['VPN_PASSWORD']
VPN_HOST = os.environ['VPN_HOST']
VPN_HUB = os.environ['VPN_HUB']

f_userlist = open('./userlist.conf', 'r')
conf_userlist = f_userlist.read().split('\n')
f_userlist.close()
userlist = dict()
for item in conf_userlist:
    i = re.split('=', item)
    userlist[i[0]] = i[1]

saveip = dict()
if os.path.isfile('./saveip'):
    f_saveip = open('./saveip', 'r')
    file_saveip = f_saveip.read().split('\n')
    if file_saveip[0] != '':
        for item in file_saveip:
            if item != '':
                i = re.split('=', item)
                saveip[i[0]] = i[1]
    f_saveip.close()

args = ['sudo', '/usr/local/vpnserver/vpncmd', VPN_HOST,
        '/SERVER', f'/HUB:{VPN_HUB}', f'/PASSWORD:{VPN_PASSWORD}', '/cmd', 'sessionlist']

or_sessionlist = subprocess.check_output(args).decode().split(
    '----------------+----------------------------------\n')
del args
or_sessionlist.pop(0)
or_sessionlist[-1] = re.sub('The.command.completed.successfully.\n\n',
                            '', or_sessionlist[-1])
record_ip = dict()
for item in or_sessionlist:
    line = item.split('\n')
    session_id = re.split('\s*\|', line[0])[1]
    user_name = re.split('\s*\|', line[3])[1]
    if user_name in userlist.keys():
        args = ['sudo', '/usr/local/vpnserver/vpncmd', VPN_HOST,
                '/SERVER', f'/HUB:{VPN_HUB}', f'/PASSWORD:{VPN_PASSWORD}', '/cmd', 'sessionget', session_id]
        sessioninfo = subprocess.check_output(args).decode().split(
            '------------------------------------------+----------------------------------------\n')[1]

        ipaddress = re.split('\s*\|', sessioninfo.split('\n')[0])[1]
        record_ip[user_name] = dict(
            [('record', userlist[user_name]), ('ipaddress', ipaddress)])

new_saveip = dict()
for item in userlist.keys():
    if item in record_ip.keys():
        if item in saveip:
            saveip[item] = re.sub('\*+$', '', saveip[item])
            if saveip[item] != record_ip[item]['ipaddress']:
                print(item + ' : not match ipaddress.')
            else:
                print(item + ' : not change ipaddress.')
            new_saveip[item] = record_ip[item]['ipaddress']
        else:
            new_saveip[item] = record_ip[item]['ipaddress']
            print(item+' : new ipaddress.')
    else:
        if item in saveip:
            new_saveip[item] = saveip[item] + '*'
            print(item+' : not connection.')
        else:
            item = re.sub('\*+$', '', item)
            new_saveip[item+'*'] = '0.0.0.0' + '*'
            print(item+' : not connection yet.')

f_newsaveip = open('./saveip', 'w')
for item in new_saveip:
    f_newsaveip.write('{}={}\n'.format(item, new_saveip[item]))

f_newsaveip.close()

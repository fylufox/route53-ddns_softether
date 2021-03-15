import subprocess
import re
import os
import softether

# config
config = dict()
config_key = ''
f_config = open('./route53-ddns.conf', 'r')
file_config = re.split('(\[.+\])\n', f_config.read())
for item in file_config:
    if item == '':
        continue
    i_conf_key = re.findall('\[(.+)\]', item)
    if len(i_conf_key) == 0:
        conf_subkey = dict()
        for iitem in item.split('\n'):
            if iitem == '':
                continue
            i = re.split(' *= *', iitem)
            conf_subkey[i[0]] = i[1]
        config[config_key] = conf_subkey
    else:
        config_key = i_conf_key[0]

VPN_PASSWORD = config['vpn']['VPN_PASSWORD']
VPN_HOST = config['vpn']['VPN_HOST']
VPN_HUB = config['vpn']['VPN_HUB']
VPN_COMMAND_PATH = config['vpn']['VPN_COMMAND_PATH']

NOT_CONNECTION_NUM = int(config['check']['NOT_CONNECTION_NUM'])

# end config.

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


sessionlist = softether.get_sessionlist(
    VPN_COMMAND_PATH, VPN_HOST, VPN_PASSWORD, VPN_HUB)

record_ip = dict()
for item in sessionlist:
    username = sessionlist[item]
    if username in userlist.keys():
        ip = softether.get_sessioninfo_ip(
            VPN_COMMAND_PATH, VPN_HOST, VPN_PASSWORD, VPN_HUB, item)
        record_ip[username] = dict(
            [('record', userlist[username]), ('ipaddress', ip)])

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
        if item in saveip.keys():
            check = saveip[item].count('*')+1
            if check >= NOT_CONNECTION_NUM:
                new_saveip[item + '*'] = re.sub('\**', '', saveip[item])
                print(item+f' : delete route53 record. check count {check}.')
            else:
                new_saveip[item] = saveip[item] + '*'
                print(item+f' : not connection. check count {check}.')
        else:
            item = re.sub('\*+$', '', item)
            new_saveip[item+'*'] = '0.0.0.0'
            print(item+' : not connection yet.')

f_newsaveip = open('./saveip', 'w')
for item in new_saveip:
    f_newsaveip.write('{}={}\n'.format(item, new_saveip[item]))

f_newsaveip.close()

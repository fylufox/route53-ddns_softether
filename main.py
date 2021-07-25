import subprocess
import re
import os
import boto3
import softether
import route53_makerecord
import slack_webhook
import sys
import requests

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

if 'aws' in config.keys():
    ACCESS_KEY = config['aws']['ACCESS_KEY_ID']
    SECRET_KEY = config['aws']['SECRET_ACCESS_KEY']
    route53 = boto3.client('route53',
                           aws_access_key_id=ACCESS_KEY,
                           aws_secret_access_key=SECRET_KEY)
else:
    route53 = boto3.client('rotue53')

HOSTED_ZONE_ID = config['route53']['HOSTED_ZONE_ID']

NOT_CONNECTION_NUM = int(config['check']['NOT_CONNECTION_NUM'])

if 'notifycation' in config.keys():
    SLACK_WEBHOOK_URL = config['notifycation']['SLACK_WEBHOOK']
# end config.

f_userlist = open('./userlist.conf', 'r')
conf_userlist = f_userlist.read().split('\n')
f_userlist.close()
userlist = dict()
for item in conf_userlist:
    if item == '':
        continue
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

try:
    sessionlist = softether.get_sessionlist(
        VPN_COMMAND_PATH, VPN_HOST, VPN_PASSWORD, VPN_HUB)
except:
    subprocess.check_output(['sudo', 'systemctl', 'restart', 'vpnserver.service'])
    res = slack_webhook.push_slack_webhook("VPNプロセスを再起動しました。", SLACK_WEBHOOK_URL)
    if res.status_code != 200:
        print("Webhook Error : "+res.text+"[{}]".format(res.status_code))
    sys.exit()

record_ip = dict()
for item in sessionlist:
    username = sessionlist[item]
    if username in userlist.keys():
        ip = softether.get_sessioninfo_ip(
            VPN_COMMAND_PATH, VPN_HOST, VPN_PASSWORD, VPN_HUB, item)
        record_ip[username] = dict(
            [('record', userlist[username]), ('ipaddress', ip)])

change_batch = []
new_saveip = dict()
for item in userlist.keys():
    if item in record_ip.keys():
        if item in saveip:
            saveip[item] = re.sub('\*+$', '', saveip[item])
            if saveip[item] != record_ip[item]['ipaddress']:
                print(item + ' : not match ipaddress.')
                change_batch.append(
                    route53_makerecord.make_create_record(record_ip[item]['record'], record_ip[item]['ipaddress']))
            else:
                print(item + ' : not change ipaddress.')

            new_saveip[item] = record_ip[item]['ipaddress']
        else:
            new_saveip[item] = record_ip[item]['ipaddress']
            print(item + ' : new ipaddress.')
            change_batch.append(
                route53_makerecord.make_create_record(record_ip[item]['record'], record_ip[item]['ipaddress']))

    else:
        if item in saveip.keys():
            check = saveip[item].count('*')+1
            if check >= NOT_CONNECTION_NUM:
                new_saveip[item + '*'] = re.sub('\**', '', saveip[item])
                print(item + f' : delete route53 record. check count {check}.')
                change_batch.append(
                    route53_makerecord.make_delete_record(userlist[item], new_saveip[item+'*']))

            else:
                new_saveip[item] = saveip[item] + '*'
                print(item+f' : not connection. check count {check}.')
        else:
            item = re.sub('\*+$', '', item)
            new_saveip[item+'*'] = '0.0.0.0'
            print(item + ' : not connection yet.')

if len(change_batch) > 0:
    print(f'{len(change_batch)} update route53.')
    route53.change_resource_record_sets(
        ChangeBatch={'Changes': change_batch},
        HostedZoneId=HOSTED_ZONE_ID,
    )
    if 'SLACK_WEBHOOK_URL' in locals():
        payload_list = []
        payload = dict()
        for item in change_batch:
            action = item['Action']
            record_name = item['ResourceRecordSet']['Name']
            address = item['ResourceRecordSet']['ResourceRecords'][0]['Value']
            payload_list.append(slack_webhook.make_payload_attachments(
                action, record_name, address))
        payload["attachments"] = payload_list
        payload["blocks"] = [{
            "type": "section",
            "text": dict(
                type="mrkdwn",
                text="{}件の変更を確認しました。".format(len(change_batch))
            )
        }]
        res = slack_webhook.push_slack_webhook(payload, SLACK_WEBHOOK_URL)
        if res.status_code != 200:
            print("Webhook Error : "+res.text+"[{}]".format(res.status_code))

f_newsaveip = open('./saveip', 'w')
for item in new_saveip:
    f_newsaveip.write('{}={}\n'.format(item, new_saveip[item]))

f_newsaveip.close()

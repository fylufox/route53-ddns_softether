import boto3


def make_create_record(name, ip):
    changes = dict()
    changes['Action'] = 'UPSERT'
    changes['ResourceRecordSet'] = {
        'Name': name,
        'ResourceRecords': [dict(Value=ip)],
        'Type': 'A',
        'TTL': 300,
    }
    return changes


def make_delete_record(name, ip):
    changes = dict()
    changes['Action'] = 'DELETE'
    changes['ResourceRecordSet'] = {
        'Name': name,
        'ResourceRecords': [dict(Value=ip)],
        'Type': 'A',
        'TTL': 300,
    }
    return changes

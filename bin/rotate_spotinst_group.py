#!/usr/bin/python
import json
from time import sleep
import argparse
import os
import requests

group_id, account_id, percentage, grace_period, strategy_action, health_check_type = None, None, None, None, None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--GROUP_ID', required=True, help='SpotInst Group Id')
    parser.add_argument('--ACCOUNT_ID', required=True, help='SpotInst Account Id')
    parser.add_argument('--PERCENTAGE', required=False, default=100, help='Percentage to be replaced in each batch')
    parser.add_argument('--GRACE_PERIOD', required=False, default=300, help='Grace period')
    parser.add_argument('--STRATEGY', required=False, default='REPLACE_SERVER', help='The roll action to perform. valid values: REPLACE_SERVER, RESTART_SERVER')
    parser.add_argument('--HEALTH_CHECK_TYPE', required=False, default='TARGET_GROUP', help='Where health check is set. Values are: ELB, ECS_CLUSTER_INSTANCE, TARGET_GROUP, OPSWORKS, NOMAD_NODE, MULTAI_TARGET_SET, HCS, EC2, NONE')
    args = parser.parse_args()
    global group_id, account_id, percentage, grace_period, strategy_action, health_check_type
    group_id, account_id, percentage, grace_period, strategy_action, health_check_type = args.GROUP_ID, args.ACCOUNT_ID, args.PERCENTAGE, args.GRACE_PERIOD, args.STRATEGY, args.HEALTH_CHECK_TYPE
    print('args:', group_id, account_id, percentage, grace_period, strategy_action, health_check_type)
    rotate()


def rotate():
    payload = get_payload()
    headers = get_headers()
    url = f'https://api.spotinst.io/aws/ec2/group/{group_id}/roll?accountId={account_id}'
    print('request PUT into', url)
    r = requests.put(url, data=json.dumps(payload), headers=headers)
    resp = r.json()
    if r.status_code != requests.codes.ok:
        print(r.text)
        raise Exception(resp['response']['errors'][0]['message'])
    roll_id = resp['response']['items'][0]['id']
    waitTrue(10, 600, _check_rollup_done(roll_id))
    print('Deploy Finished!')


def get_headers():
    spotinst_token = os.getenv('SPOTINST_TOKEN')
    return {
        'content-type': 'application/json',
        'Authorization': f'Bearer {spotinst_token}'
    }


def get_payload():
    return {
        "batchSizePercentage": percentage,
        "gracePeriod": grace_period,
        "healthCheckType": health_check_type,
        "strategy": {
            "action": strategy_action,
            "batchMinHealthyPercentage": 100,
            "onFailure": {
                "actionType": "DETACH_NEW",
                "shouldHandleAllBatches": True,
                "drainingTimeout": 600,
                "shouldDecrementTargetCapacity": True
            }
        }
    }


def waitTrue(interval, timeout, func):
    timespent = 0
    while True:
        if func():
            return
        sleep(interval)
        timespent += interval
        print('wating %s...' % timespent)
        if timespent > timeout:
            print('Timeout reached. Aborting')
            exit(1)


def _check_rollup_done(roll_id):
    def f():
        headers = get_headers()
        r = requests.get(f'https://api.spotinst.io/aws/ec2/group/{group_id}/roll/{roll_id}?accountId={account_id}', headers=headers)
        if r.status_code != requests.codes.ok:
            raise Exception('Error checking rollup')
        resp = r.json()
        deployment_status = resp['response']['items'][-1]['status']
        print(f'Deployment of {roll_id} is {deployment_status}')
        return deployment_status == 'finished'
    return f


if __name__ == '__main__':
    main()
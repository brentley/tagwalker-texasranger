#!/usr/bin/env python3

from __future__ import print_function

import json
import boto3
import sys
import logging
import collections

from collections import OrderedDict
from time import sleep

RETRY_EXCEPTIONS = ('RequestLimitExceeded',
                    'ThrottlingException')
                    
# get list of ec2 regions
from boto3.session import Session
s = Session()
regions = s.get_available_regions('ec2')
#regions = ['us-west-1']

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
    level=logging.WARN,
    #level=logging.DEBUG, # debug here is super verbose
    stream=sys.stdout)

# Really don't need to hear about connections being brought up again after server has closed it
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)

log = logging.getLogger("TagWalker")
log.setLevel('INFO')
#log.setLevel('DEBUG') # debug is good for seeing activity

def tag_check(instance):
    try:
        billing_tag = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Billing']
    except Exception as e:
        if not billing_tag:
            log.info("there is no billing tag set for %s in region %s - we will terminate", instance.id, region)
            log.debug(e)
            instance.terminate(instance.id)
            pass

def set_termination_protection(instance):
    environment_tag = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Environment' and tag['Value'] == 'production']
    if environment_tag and not instance.spot_instance_request_id:
        apiterm = instance.describe_attribute(Attribute='disableApiTermination')
        apiterm = apiterm.get('DisableApiTermination')
        apiterm = apiterm.get('Value')
        if apiterm != True:
            log.info("environment tag is set to production for %s in region %s - we will enable protection", instance.id, region)
            try:
                instance.modify_attribute(DisableApiTermination={'Value':True})
            except Exception as e:
                log.debug(e)
                log.debug("Error when setting termination protection  for %s", instance.id)
                pass

def tag_cleanup(instance, detail):
    tempTags=[]
    v={}
    log.debug("Reading tags for %s in region %s", instance.id, region)
    for t in instance.tags: # Set the important tags that should be written here
        if t['Key'] == 'Name':
            tempTags.append(t)
        elif t['Key'] == 'Billing':
            tempTags.append(t)
        elif t['Key'] == 'Department':
            tempTags.append(t)
        elif t['Key'] == 'Application':
            tempTags.append(t)
        elif t['Key'] == 'Environment':
            tempTags.append(t)
        elif t['Key'] == 'Stack-Name':
            tempTags.append(t)
        elif t['Key'] == 'role':
            tempTags.append(t)
    return(tempTags)

def tagwalk(region):
        log.info("Processing for region %s", region)
        ec2 = boto3.resource('ec2', region_name=str(region))
        instances = ec2.instances.filter(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping']}])
        retries = 0
        for instance in instances:
            try:
                log.debug("Processing instance %s in region %s", instance.id, region)
                tag_check(instance) # check for the Billing tag
                set_termination_protection(instance) # only on production non-spot instances

                for vol in instance.volumes.all():
                    log.debug("Processing volume %s", vol.id)
                    if vol.tags:
                        voltags = collections.OrderedDict(vol.tags)
                    tag = collections.OrderedDict(tag_cleanup(instance, vol.attachments[0]['Device']))
                    if tag == voltags:
                        log.debug("The tags on Volume %s are correct", vol.id)
                    else:
                        log.info("Tagging Volume %s with tags %s", vol.id, str(tag))
                        tag = vol.create_tags(Tags=tag_cleanup(instance, vol.attachments[0]['Device']))

                for interface in instance.network_interfaces:
                    log.debug("Processing ENI %s", interface.id)
                    tagset = collections.OrderedDict(ec2.NetworkInterface(interface.id).tag_set)
                    tags = collections.OrderedDict(tag_cleanup(instance, "eth"+str(interface.attachment['DeviceIndex'])))
                    if tags == tagset:
                        log.debug("The tags on ENI %s are correct", interface.id)
                    else:
                        enitag = interface.create_tags(Tags=tag_cleanup(instance, "eth"+str(interface.attachment['DeviceIndex'])))
                        log.info("Tagging Interface %s with tags %s", interface.id, str(enitag))
            except Exception as e:
                if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                    log.error(e)
                    log.error("Error when processing instance %s in region %s", instance.id, region)
                    pass
                print('We hit the rate limiter... backing off... retries={}'.format(retries))
                #sleep(2 ** retries)
                sleep(5)
                retries += 1

log.info("Tagwalker Starting")
for region in regions:
    tagwalk(region)
log.info("Tagwalker Completed")

# todo:
# tag the vpc
# tag the elb eni
# tag the efs eni
# tag the rds eni
# tag the nat gateway eni

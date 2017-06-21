#!/usr/bin/env python3

from __future__ import print_function

import json
import boto3
import sys
import logging
import collections

from collections import OrderedDict
from time import sleep

PROD_REGIONS = ('us-west-2',
                    'us-east-2')

RETRY_EXCEPTIONS = ('RequestLimitExceeded',
                    'ThrottlingException')

BACKOFF_MAX = 5

# get list of ec2 regions
from boto3.session import Session
s = Session()
regions = s.get_available_regions('ec2')
#regions = ['us-east-2']

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
    if instance.tags is None:
        apiterm = instance.describe_attribute(Attribute='disableApiTermination')
        apiterm = apiterm.get('DisableApiTermination')
        apiterm = apiterm.get('Value')
        if apiterm == True and region not in PROD_REGIONS:
            try:
                log.info("there are no tags set for %s and termination protection is enabled in region %s - we will disable protection", instance.id, region)
                instance.modify_attribute(DisableApiTermination={'Value':False})
            except Exception as e:
                if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                    log.error(e)
                    log.error("Error when removing termination protection for %s", instance.id)
                    pass
                else:
                    sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                    log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                    sleep(sleepvalue)
                    retries += 1
        log.info("there are no tags set for %s in region %s - we will terminate", instance.id, region)
        instance.terminate(instance.id)
        return
    else:
        billing_tag = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Billing']
        if not billing_tag:
            apiterm = instance.describe_attribute(Attribute='disableApiTermination')
            apiterm = apiterm.get('DisableApiTermination')
            apiterm = apiterm.get('Value')
            if apiterm == True and region not in PROD_REGIONS:
                try:
                    log.info("there is no billing tag set for %s and termination protection is enabled in region %s - we will disable protection", instance.id, region)
                    instance.modify_attribute(DisableApiTermination={'Value':False})
                except Exception as e:
                    if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                        log.error(e)
                        log.error("Error when removing termination protection for %s", instance.id)
                        pass
                    else:
                        sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                        log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                        sleep(sleepvalue)
                        retries += 1
            try:
                log.info("there is no billing tag set for %s in region %s - we will terminate", instance.id, region)
                instance.terminate(instance.id)
                return
            except Exception as e:
                if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                    log.error(e)
                    log.error("Error when terminating %s", instance.id)
                    pass
                else:
                    sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                    log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                    sleep(sleepvalue)
                    retries += 1

def set_termination_protection(instance):
    if instance.tags is None:
        log.info("there are no tags set for %s in region %s", instance.id, region)
        return
    else:
        environment_tag = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Environment' and tag['Value'] == 'production']
        if environment_tag and not instance.spot_instance_request_id:
            apiterm = instance.describe_attribute(Attribute='disableApiTermination')
            apiterm = apiterm.get('DisableApiTermination')
            apiterm = apiterm.get('Value')
            if apiterm != True:
                try:
                    log.info("environment tag is set to production for %s in region %s - we will enable protection", instance.id, region)
                    instance.modify_attribute(DisableApiTermination={'Value':True})
                except Exception as e:
                    if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                        log.error(e)
                        log.error("Error when setting termination protection  for %s", instance.id)
                        pass
                    else:
                        sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                        log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                        sleep(sleepvalue)
                        retries += 1

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

def terminator(region):
        log.info("Processing for region %s", region)
        ec2 = boto3.resource('ec2', region_name=str(region))
        instances = ec2.instances.filter(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping']}])
        retries = 0
        instance_count = 0
        for instance in instances:
            log.debug("Processing instance %s in region %s", instance.id, region)
            instance_count += 1
            try:
                tag_check(instance) # check for the Billing tag
            except Exception as e:
                if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                    log.error(e)
                    log.error("Error when processing instance %s in region %s", instance.id, region)
                    pass
                else:
                    sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                    log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                    sleep(sleepvalue)
                    retries += 1

            try:
                set_termination_protection(instance) # only on production non-spot instances
            except Exception as e:
                if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                    log.error(e)
                    log.error("Error when processing instance %s in region %s", instance.id, region)
                    pass
                else:
                    sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                    log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                    sleep(sleepvalue)
                    retries += 1
        log.info("Processed %s instances total", instance_count)

def tagwalk(region):
        log.info("Processing for region %s", region)
        ec2 = boto3.resource('ec2', region_name=str(region))
        instances = ec2.instances.filter(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping']}])
        retries = 0
        instance_count = 0
        for instance in instances:
            log.debug("Processing instance %s in region %s", instance.id, region)
            instance_count += 1
            if instance.tags is None:
                log.info("there are no tags set for %s in region %s", instance.id, region)
                return
            else:
                try:
                    for vol in instance.volumes.all():
                        log.debug("Processing volume %s", vol.id)
                        if vol.tags is None:
                                tag = vol.create_tags(Tags=tag_cleanup(instance, vol.attachments[0]['Device']))
                                log.info("Tagging Volume %s with tags %s", vol.id, str(tag))
                        else:
                            voltags = collections.OrderedDict(vol.tags)
                            tag = collections.OrderedDict(tag_cleanup(instance, vol.attachments[0]['Device']))
                            if tag == voltags:
                                log.debug("The tags on Volume %s are correct", vol.id)
                            else:
                                tag = vol.create_tags(Tags=tag_cleanup(instance, vol.attachments[0]['Device']))
                                log.info("Tagging Volume %s with tags %s", vol.id, str(tag))
                except Exception as e:
                    if e.response['Error']['Code'] not in RETRY_EXCEPTIONS:
                        log.error(e)
                        log.error("Error when processing instance %s in region %s", instance.id, region)
                        pass
                    else:
                        sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                        log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                        sleep(sleepvalue)
                        retries += 1

                try:
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
                    else:
                        sleepvalue = (2 ** min(retries, BACKOFF_MAX))
                        log.warning("We hit the rate limiter on instance %s, %s instances processed so far... sleeping for %s seconds, retries=%s", instance.id, instance_count, sleepvalue, retries)
                        sleep(sleepvalue)
                        retries += 1
        log.info("Processed %s instances total", instance_count)

log.info("Tagwalker Starting terminations")

for region in regions:
    terminator(region)

log.info("Tagwalker Starting copying tags")

for region in regions:
    tagwalk(region)

log.info("Tagwalker Completed")

# todo:
# tag the vpc
# tag the elb eni
# tag the efs eni
# tag the rds eni
# tag the nat gateway eni

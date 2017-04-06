#!/usr/bin/env python3

from __future__ import print_function

import json
import boto3
import logging
from tenacity import retry

# get list of ec2 regions

from boto3.session import Session
s = Session()
regions = s.get_available_regions('ec2')
#regions = ['us-west-1']
#print(str(regions))

logging.basicConfig(format='%(asctime)s %(message)s')

log = logging.getLogger("TagWalker")
log.setLevel(logging.WARN)

@retry

def tag_check(instance):
    terminate=True
    for tags in instance.tags:
        if tags["Key"] == 'Billing':
            terminate=False

    if terminate == True:
        log.warn("there is no billing tag set for %s in region %s - we will terminate", instance.id, region)
        instance.terminate(instance.id)

def set_termination_protection(instance):
    protect=False
    for tags in instance.tags:
        if tags["Key"] == 'Environment':
            if tags["Value"] == 'production':
                log.info("Environment tag is set to %s - we will enable termination protection", tags["Value"])
                protect=True

    if protect == True:
        try:
            log.warn("Enabling termination protection for %s in region %s", instance.id, region)
            instance.modify_attribute(DisableApiTermination={'Value':True})
        except:
            print("unable to enable termination protection for %s", instance.id)

def tag_cleanup(instance, detail):
    tempTags=[]
    v={}

    for t in instance.tags:
        #pull the name tag
        if t['Key'] == 'Name':
            v['Value'] = t['Value'] + " - " + str(detail)
            v['Key'] = 'Name'
            tempTags.append(v)
        #Set the important tags that should be written here
        elif t['Key'] == 'Billing':
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

for region in regions:
    ec2 = boto3.resource('ec2', region_name=str(region))
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping']}])

    for instance in instances:

        log.info("Processing instance %s in region %s", instance.id, region)

        # enable termination protection
        set_termination_protection(instance)

        # check for the Billing tag
        tag_check(instance)

        # tag the volumes
        for vol in instance.volumes.all():
            try:
                tag = vol.create_tags(Tags=tag_cleanup(instance, vol.attachments[0]['Device']))
                log.info("Tagging Volume %s with tags %s", vol.id, str(tag))
            except:
                raise Exception

        # tag the eni
        for eni in instance.network_interfaces:
            try:
                tag = eni.create_tags(Tags=tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex'])))
                log.info("Tagging Interface %s with tags %s", eni.id, str(tag))
            except:
                raise Exception


        # tag the vpc
#        for vpc in instance.vpc_id:
#            if noop == True:
#                print("[DEBUG] " + str(vpc))
#                tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex']))
#            else:
#                tag = eni.create_tags(Tags=tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex'])))
#                print("[INFO]: " + str(tag))

# tag the elb eni

# tag the efs eni

# tag the rds eni

# tag the nat gateway eni

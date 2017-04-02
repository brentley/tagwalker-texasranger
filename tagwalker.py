#!/usr/bin/env python3

from __future__ import print_function

import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# get list of ec2 regions

from boto3.session import Session
s = Session()
regions = s.get_available_regions('ec2')

boto3.NumberRetries = 0
boto3.Debug = 2
# True will make the run a noop run.
noop = False

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
            print("[INFO]: Billing Tag " + str(t))
            tempTags.append(t)
        elif t['Key'] == 'Application':
            print("[INFO]: Application Tag " + str(t))
            tempTags.append(t)
        elif t['Key'] == 'Environment':
            print("[INFO]: Environment Tag " + str(t))
            tempTags.append(t)
        elif t['Key'] == 'Stack-Name':
            print("[INFO]: Stack-Name Tag " + str(t))
            tempTags.append(t)
        elif t['Key'] == 'role':
            print("[INFO]: role Tag " + str(t))
            tempTags.append(t)
        else:
            print("[INFO]: Skip Tag - " + str(t))

    print("[INFO] " + str(tempTags))
    return(tempTags)

for region in regions:
    ec2 = boto3.resource('ec2', region_name=str(region))
    instances = ec2.instances.all()

    for instance in instances:

        # tag the volumes
        for vol in instance.volumes.all():
            if noop == True:
                print("[DEBUG] " + str(vol))
                tag_cleanup(instance, vol.attachments[0]['Device'])
            else:
                tag = vol.create_tags(Tags=tag_cleanup(instance, vol.attachments[0]['Device']))
                print("[INFO]: " + str(tag))

        # tag the eni
        for eni in instance.network_interfaces:
            if noop == True:
                print("[DEBUG] " + str(eni))
                tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex']))
            else:
                tag = eni.create_tags(Tags=tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex'])))
                print("[INFO]: " + str(tag))

        # tag the vpc
        for vpc in instance.vpc_id:
            if noop == True:
                print("[DEBUG] " + str(vpc))
                tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex']))
            else:
                tag = eni.create_tags(Tags=tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex'])))
                print("[INFO]: " + str(tag))

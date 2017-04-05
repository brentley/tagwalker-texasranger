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
#regions = ['us-west-1']
print(str(regions))

boto3.NumberRetries = 0
boto3.Debug = 2
# True will make the run a noop run.
noop = False

def tag_check(instance):
    terminate=True
    for tags in instance.tags:
        if tags["Key"] == 'Billing':
            terminate=False

    if terminate == True:
        print("There is no billing tag set for", instance.id, "we will terminate")
        instance.terminate(instance.id)

def set_termination_protection(instance):
    protect=False
    for tags in instance.tags:
        if tags["Key"] == 'Environment':
            if tags["Value"] == 'production':
                print("Environment tag is set to", tags["Value"], "we will enable termination protection")
                protect=True
    if protect == True:
        try:
            print("Enabling termination protection for", instance.id)
            instance.modify_attribute(DisableApiTermination={'Value':True})
        except:
            print("unable to enable termination protection for", instance.id)

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

    print("[INFO]: " + str(tempTags))
    return(tempTags)

for region in regions:
    ec2 = boto3.resource('ec2', region_name=str(region))
    instances = ec2.instances.all()

    for instance in instances:

        print("Processing instance", instance.id, "in region", region)

        # enable termination protection
        set_termination_protection(instance)

        # check for the Billing tag
        tag_check(instance)

        # tag the volumes
        for vol in instance.volumes.all():
            if noop == True:
                print("[DEBUG] " + str(vol))
                try:
                    tag_cleanup(instance, vol.attachments[0]['Device'])
                except:
                    raise Exception
            else:
                try:
                    tag = vol.create_tags(Tags=tag_cleanup(instance, vol.attachments[0]['Device']))
                    print("[INFO]: " + str(tag))
                except:
                    raise Exception

        # tag the eni
        for eni in instance.network_interfaces:
            if noop == True:
                print("[DEBUG] " + str(eni))
                try:
                    tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex']))
                except:
                    raise Exception
            else:
                try:
                    tag = eni.create_tags(Tags=tag_cleanup(instance, "eth"+str(eni.attachment['DeviceIndex'])))
                    print("[INFO]: " + str(tag))
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

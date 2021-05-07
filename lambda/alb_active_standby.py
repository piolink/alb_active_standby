# Import the SDK and required libraries
import boto3
import json
import os
import logging
import sys
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Configure the SNS topic which you want to use for sending notifications
sns_arn = os.environ['SNS_TOPIC']
alarm_name_prefix = os.environ['ALARM_NAME']
region = os.environ["AWS_REGION"]

lb_listener = os.environ['LB_LISTENER_ARN']
tg_arn_active = os.environ['TARGETGROUP_ARN_ACTIVE'].strip()
tg_arn_backup = os.environ['TARGETGROUP_ARN_BACKUP'].strip()


def lambda_handler(event, context):
	"""
	Main Lambda handler
	"""
	logger.info("Received event: " + json.dumps(event, indent=2))
	message = event['Records'][0]['Sns']['Message']
	
	global sns_client
	global elbv2_client

	try:
		sns_client = boto3.client('sns')
	except ClientError as e:
		logger.error(e.response['Error']['Message'])

	try:
		elbv2_client = boto3.client('elbv2')
	except ClientError as e:
		logger.error(e.response['Error']['Message'])

	if not "AlarmName" in message:
		logger.error('No Alarmname in event message')
		return
	
	json_message = json.loads(message)
	alarm_name = str(json_message['AlarmName'])
	alarm_trigger = str(json_message['NewStateValue'])
	timestamp = str(json_message['StateChangeTime'])
	
	if not alarm_name.startswith(alarm_name_prefix):
		logger.error('Invalid alarm_name {}'.format(alarm_name))
		return
	
	if alarm_name.startswith(alarm_name_prefix + '-dead'):
		is_active_dead = True
	elif alarm_name.startswith(alarm_name_prefix + '-alive'):
		is_active_dead = False
	else:
		logger.error('Invalid alarm_name musst be {}-deat or {}-alive'.format(alarm_name_prefix, alarm_name_prefix))
		return
	
	if alarm_trigger != 'ALARM':
		logger.info('no alarm just return')
		return
	
	for entity in json_message['Trigger']['Dimensions']:
			if entity['name'] == "LoadBalancer":
				elb_name = str(entity['value'])
				
		
	change_weight_in_lb_rule(elb_name, is_active_dead)
	send_sns(elb_name, region, timestamp, alarm_name)
	
	
def send_sns(elb_name, region, timestamp, alarm_name):
	"""
	Send notification to SNS topic subscribers of unhealthy instances/targets
	"""
	message = "Timestamp: {} \nRegion: {} \nELB: {} \nAlarm Name: {}".format(timestamp, region, elb_name, alarm_name)
	
	try:
		sns_client.publish(
			TopicArn=sns_arn,
			Message=message,
			Subject=region.upper() + ' Alarm: Healthcheck state changed ' + elb_name,
			MessageStructure='string'
		)
	except ClientError as e:
		logger.error(e.response['Error']['Message'])


def change_weight_in_lb_rule(elb_name, is_active_dead):
	target_weight_active = 0 if is_active_dead else 1
	target_weight_backup = 1 if is_active_dead else 0
	
	try:
		response = elbv2_client.modify_listener(ListenerArn=lb_listener,
			DefaultActions = [ 
			{	'Type': 'forward',
				'ForwardConfig': {
            		'TargetGroups': [
                    	{
                        	'TargetGroupArn': tg_arn_active,
                        	'Weight': target_weight_active
                    	},
                    	{
                    		'TargetGroupArn': tg_arn_backup,
                        	'Weight': target_weight_backup
                    	}
                	] 
				}
			}])
		 
	except ClientError as e:
		logger.error(e.response['Error']['Message'], response)
	
	logger.info('Set target weight: {} => {}, {} => {}'.format(
		tg_arn_active, target_weight_active, tg_arn_backup, target_weight_backup))

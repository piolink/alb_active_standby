
# AWS Serverlesss Implementation for supporting of AWS ALB Active Standby 


## Overview 

This is a AWS serverless implemention of ALB active standby which is composed of
- CloudWatch Alarm for checking healty LB target host 
- SNS for notification of CloudWatch alarm trigger and email notification for Alarm event
- Lambda for alarm event handing that modify Rule of LB Listener to redirect traffic to backup target group

## User Guide
### Requirements
- Pre existing Load Balancer Settings
   - ALB (Application Load Balancer)
   - Two LB Target groups: Active and Backup
      - If at least one host in active target group is healthy, LB redirect all traffic to active target group.
      - Otherwise if all hosts in active target group is unhealthy, LB redirect all traffic traffic to backup target group 
   - ALB Listener Rule
      - Forward to active group (intial weight: 1) and backup group (initial weight: 0) as followings
        -  | IF(all match)                  |     THEN          |
           | ------------------------------ | ----------------- |
           | Requests otherwise not routed  | 1. Forward to     | 
           |                                |  active: 1 (100%) |
           |                                |  backup: 0        |
           |                                |  Group-level stickiness: Off |
 
### Cloudformation Parameters
- LoadBalancerName:
   -  Enter your existing load balancer name. e.g app/lbname/d665cae1604417d
- LBListenerArn:
   - Enter your existing LB Listerner ARN. e.g.arn:aws:elasticloadbalancing:ap-northeast-2:1111:listener/app/lb/22222/333333
- TargetGroupARNActive:
   - Enter your existing ACTIVE target group ARN. e.g.arn:aws:elasticloadbalancing:ap-northeast-2:1111:targetgroup/my-tg/aaaaa
- TargetGroupARNBackup:
   - Enter your existing Backup target group ARN. e.g.arn:aws:elasticloadbalancing:ap-northeast-2:1111:targetgroup/my-tg/bbbbb
- CloudWatchAlarmName:
   - Enter a new CloudWatch Alarm name that you want to create for monitoring LB target 
- Email:
   - Enter a Email address to be notified when the CloudWatch alarm is triggered

## Developer Guide
### Control Flows
1. Healthchecking for active and standby target group in ALB 
1. Updateing LB Healthy Host Count Metric in CloudWatch
1. Alarm of LB Healcheck state change in CloudWatch Alarm 
1. Triggering AWS SNS for CloudWatch Alarm
1. Calling AWS Lambda handler for AWS SNS event
1. Modifying the weight of actvie and backup group in LB Listener Rule 

## Bug Report or Feature Request
- All the bug report or feature request is welcome, please report to [github repoistory's Issues](https://github.com/piolink/alb_active_standby/issues)

## License
- &copy; 2021 [PIOLINK](https://www.piolink.com). This project is licensed under the terms of the MIT license.

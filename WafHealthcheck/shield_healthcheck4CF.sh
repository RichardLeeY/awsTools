# this script will create health check for shield protection
# It assume that you have create cloudfront distribution and create shield protection on this distribution.
# This script will create alarm for 5xxErrorRate and create health check for shield protection.
# example: ./shield_healthcheck4CF.sh  E3FVLTLHTOU77K
# add -h for help
if [ "$1" == "-h" ]
then
  echo "Usage: ./shield_healthcheck4CF.sh E3FVLTLHTOU77K"
   exit 1
fi
if [ -z "$1" ]
then
  echo "No CloudFront distribution ID supplied"
  echo "Usage: ./shield_healthcheck4CF.sh E3FVLTLHTOU77K"
  exit 1
fi

distributionid=$1
echo "distributionid:'$distributionid'"
alarmname="5xxErrorRate-$1"
echo "alarmname:'$alarmname'"

# 1. create alarm for 5xxErrorRate
# by default ,This alarm create for global region. It checks health status every 60 seconds. 
# In 20 minutes, if the health status is not in a healthy state, the alarm triggers.
# You can change the period and evaluation-periods to adjust the time of the alarm.
# The threshold is 2.0, which means that the 5xxErrorRate is greater than or equal to 2.0%.
aws cloudwatch put-metric-alarm \
--alarm-name $alarmname \
--metric-name 5xxErrorRate \
--namespace AWS/CloudFront \
--statistic Average \
--dimensions Name=Region,Value=Global Name=DistributionId,Value=$1 \
--period 60 \
--evaluation-periods 20 \
--datapoints-to-alarm 1 \
--threshold 2.0 \
--comparison-operator GreaterThanOrEqualToThreshold \
--region us-east-1

# get current time with yyyy-mm-dd-mi-ss format
# example: 2020-01-01-00-00-00
currenttime=`date +%Y-%m-%d-%H-%M-%S`
echo "caller-reference:"$currenttime

# 2. create health check
healthid=`aws route53 create-health-check \
--caller-reference $currenttime \
--health-check-config '{
    "Type": "CLOUDWATCH_METRIC",
    "Inverted": false,
    "Disabled": false,
    "AlarmIdentifier": {
        "Region": "us-east-1",
        "Name": "'$alarmname'"
    },
    "InsufficientDataHealthStatus": "LastKnownStatus"
}' | jq -r '.HealthCheck.Id' `
echo "healthid:'$healthid'"
# list shield protection and find protectionid that ResourceArn like  distributionid


protectionid=` aws shield list-protections | jq -r '.Protections[] | select(.ResourceArn|contains("'${distributionid}'"))|.Id' `
echo "protectionid:'$protectionid'"
# 3. associate health check with Shield protection.
healthcheckArn='arn:aws:route53:::healthcheck/'$healthid
echo "healthcheckArn:'$healthcheckArn'"
aws shield associate-health-check --protection-id  $protectionid --health-check-arn $healthcheckArn

# Common class representing application autoscaling for SageMaker
import boto3
import sys
import argparse
client = boto3.client('application-autoscaling') 
cw_client = boto3.client('cloudwatch')
sagemaker_client  = boto3.client('sagemaker')

# This is the format in which application autoscaling references the endpoint
alarm_name_suffix = 'StepScalingAlarm'

def clearPolicy(endpoint_name,resource_id):
    # Delete the step scaling policy
    response = client.delete_scaling_policy(
        PolicyName='HasBacklogWithoutCapacity-ScalingPolicy',
        ServiceNamespace='sagemaker',
        ResourceId=resource_id,
        ScalableDimension='sagemaker:variant:DesiredInstanceCount'
    )
    # Delete the target tracking policy
    response = client.delete_scaling_policy(
        PolicyName='scale-endpoint-variant',
        ServiceNamespace='sagemaker',
        ResourceId=resource_id,
        ScalableDimension='sagemaker:variant:DesiredInstanceCount'
    )
    step_scaling_policy_alarm_name = endpoint_name + "-" + alarm_name_suffix
    # Delete the alarm
    response = cw_client.delete_alarms(
        AlarmNames=[step_scaling_policy_alarm_name]
    )
    
    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpointname', required=True, help='Sagemaker Endpoint name')
    args = parser.parse_args()
    endpoint_name = args.endpointname
    endpoint = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
    endpointConfig = sagemaker_client.describe_endpoint_config(EndpointConfigName=endpoint['EndpointConfigName'])
    variant_name = endpointConfig['ProductionVariants'][0]['VariantName']
    resource_id='endpoint/' + endpoint_name + '/variant/' + variant_name
    clearPolicy(endpoint_name,resource_id)

if __name__ == '__main__':
    main()
    

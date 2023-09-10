# Common class representing application autoscaling for SageMaker
import boto3
import sys
import argparse
client = boto3.client('application-autoscaling') 
sagemaker_client  = boto3.client('sagemaker')
cw_client = boto3.client('cloudwatch')




# This is the format in which application autoscaling references the endpoint
alarm_name_suffix = 'StepScalingAlarm'

def addscalePolicyZERO(endpoint_name,resource_id):
    Configuration={
            'TargetValue': 5.0, # The target value for the metric. Here the metric is: ApproximateBacklogSizePerInstance
            'CustomizedMetricSpecification': {
                'MetricName': 'ApproximateBacklogSizePerInstance',
                'Namespace': 'AWS/SageMaker',
                'Dimensions': [
                    {'Name': 'EndpointName', 'Value': endpoint_name }
                ],
                'Statistic': 'Average',
            }
        }   
    # Register scalable sagemaker target
    response = client.register_scalable_target(
        ServiceNamespace='sagemaker',
        ResourceId=resource_id,
        ScalableDimension='sagemaker:variant:DesiredInstanceCount',
        MinCapacity=0,
        MaxCapacity=10
    )
        
    # Define and register your endpoint variant
    response = client.put_scaling_policy(
        PolicyName='scale-endpoint-variant',
        ServiceNamespace='sagemaker',
        ResourceId=resource_id,
        ScalableDimension='sagemaker:variant:DesiredInstanceCount',
        PolicyType='TargetTrackingScaling',
        TargetTrackingScalingPolicyConfiguration=Configuration)
    # Create a scaling policy that defines the desired behavior, which is to scale up your endpoint 
    # when it’s at zero instances but has requests in the queue.
    response = client.put_scaling_policy(
        PolicyName="HasBacklogWithoutCapacity-ScalingPolicy",
        ServiceNamespace="sagemaker",  # The namespace of the service that provides the resource.
        ResourceId=resource_id,  # Endpoint name
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",  # SageMaker supports only Instance Count
        PolicyType="StepScaling",  # 'StepScaling' or 'TargetTrackingScaling'
        StepScalingPolicyConfiguration={
            "AdjustmentType": "ChangeInCapacity", # Specifies whether the ScalingAdjustment value in the StepAdjustment property is an absolute number or a percentage of the current capacity. 
            "MetricAggregationType": "Average", # The aggregation type for the CloudWatch metrics.
            "Cooldown": 300, # The amount of time, in seconds, to wait for a previous scaling activity to take effect. 
            "StepAdjustments": # A set of adjustments that enable you to scale based on the size of the alarm breach.
            [ 
                {
                "MetricIntervalLowerBound": 0,
                "ScalingAdjustment": 1
                }
            ]
        },    
    )
    scalePolicyARN = response['PolicyARN']
    step_scaling_policy_alarm_name = endpoint_name + "-" + alarm_name_suffix
    # Create a CloudWatch alarm that triggers when the HasBacklogWithoutCapacity metric exceeds the threshold.
    response = cw_client.put_metric_alarm(
        AlarmName=step_scaling_policy_alarm_name,
        MetricName='HasBacklogWithoutCapacity',
        Namespace='AWS/SageMaker',
        Statistic='Average',
        EvaluationPeriods= 2,
        DatapointsToAlarm= 2,
        Threshold= 1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Dimensions=[
            { 'Name':'EndpointName', 'Value':endpoint_name },
        ],
        Period= 60,
        AlarmActions=[scalePolicyARN]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpointname', required=True, help='SageMaker Endpoint name')
    args = parser.parse_args()
    endpoint_name = args.endpointname
    # get sagemaker endpoint configuration by endpoint name

    endpoint = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
    endpointConfig = sagemaker_client.describe_endpoint_config(EndpointConfigName=endpoint['EndpointConfigName'])
    variant_name = endpointConfig['ProductionVariants'][0]['VariantName']
    resource_id='endpoint/' + endpoint_name + '/variant/' + variant_name
    print(resource_id)
    addscalePolicyZERO(endpoint_name,resource_id)
    
if __name__ == '__main__':
    main()
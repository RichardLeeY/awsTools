## Sagemaker Endpoint Auto Scaling

This tool help you add scaling policy on a sagemaker realtime inference endpoint. If you have one or many sagemaker inference endpoints. Sometime you need the endpoint  auto scale-in when there are not many inference request and sale-out when there are more requests on this endpoint.

You can change scaling policy detail configuration in (attachScalePolicy2SagemakerEndpoint.py)[https://github.com/RichardLeeY/awsTools/blob/main/sageMakerAutoScaling/attachScalePolicy2SagemakerEndpoint.py]. I recommend you check from (here)[https://docs.aws.amazon.com/sagemaker/latest/dg/endpoint-auto-scaling.html]
This is a generic tool to build auto scaling policy for sagemaker realtime inference endpoint and easy to use. These scripts are tested in The AWS SDK for Python Boto3 1.24.6 version.

### create scaling policy for endpoint 
    
```
python attachScalePolicy2SagemakerEndpoint.py --endpointname huggingface-inference-eb
```
### clear scaling policy and alarms for endpoint

```
python clearPolicy.py --endpointname huggingface-inference-eb

```


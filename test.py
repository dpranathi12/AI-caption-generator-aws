import boto3

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

try:
    bedrock.list_custom_models()
    print("Bedrock is working!")
except Exception as e:
    print("ERROR ↓↓↓")
    print(e)



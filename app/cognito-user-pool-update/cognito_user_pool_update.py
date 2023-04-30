import boto3
import json
import os

def lambda_handler(event, context):

    cognito_client = boto3.client("cognito-idp")
    url = os.environ["API_GATEWAY_URL"]
    user_pool_id = os.environ["COGNITO_USER_POOL_ID"]
    client_id = os.environ["COGNITO_CLIENT_ID"]
    update_user_pool_client_response = cognito_client.update_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=client_id,
        CallbackURLs=[f"{url}qs-self-service-reporting"],
        LogoutURLs=[f"{url}qs-self-service-reporting"]
        )

    parsed = json.dumps(update_user_pool_client_response,indent=4, default=str)
    print(parsed)
    return parsed
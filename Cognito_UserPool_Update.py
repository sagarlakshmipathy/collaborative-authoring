import boto3

import os

import json

 

def lambda_handler(event, context):

    cognito_client = boto3.client("cognito-idp")

    url = os.environ["API_GATEWAY_URL"]

    user_pool_id = os.environ["COGNITO_USER_POOL_ID"]

    client_id = os.environ["COGNITO_CLIENT_ID"]

    update_user_pool_client_response = cognito_client.update_user_pool_client(

        UserPoolId=user_pool_id,

        ClientId=client_id,

        CallbackURLs=[

            f"{url}qs-aac-analysis-api",

            f"{url}qs-aac-sheet-api",

            f"{url}qs-aac-visual-api"

            ],

        LogoutURLs=[

            f"{url}qs-aac-analysis-api",

            f"{url}qs-aac-sheet-api",

            f"{url}qs-aac-visual-api"

            ]

        )

    parsed = json.dumps(update_user_pool_client_response,indent=4, default=str)

    print(parsed)

    return parsed
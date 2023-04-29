import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    triggers as triggers,
    Stack
)

from constructs import Construct

class CognitoUpdateStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # import ApiGateway Invoke Url from BackendStack
        url = cdk.Fn.import_value("ApiGatewayUrl")
        
        # import Cognito User Pool Id from AuthenticationStack
        user_pool_id = cdk.Fn.import_value("UserPoolId")
        
        # import Cognito Client Id from AuthenticationStack
        client_id = cdk.Fn.import_value("UserPoolClientId")
        
        cognito_update_function = _lambda.Function(
            self, "CognitoUpdateFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("./app/cognito-user-pool-update"),
            handler="cognito_user_pool_update.lambda_handler",
            timeout=cdk.Duration.minutes(1),
            function_name='cognito-user-pool-update-function',
            environment={
                "API_GATEWAY_URL": url,
                "COGNITO_USER_POOL_ID": user_pool_id,
                "COGNITO_CLIENT_ID": client_id
                }
            )
        
        # Grant permissions to invoke the function
        cognito_update_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=['cognito-idp:UpdateUserPoolClient'],
                resources=[f"arn:aws:cognito-idp:{self.region}:{self.account}:userpool/{user_pool_id}"]
                )
            )
        
        # trigger the function after deployment
        triggers.Trigger(
            self, "CognitoUpdateTrigger",
            handler=cognito_update_function,
            )
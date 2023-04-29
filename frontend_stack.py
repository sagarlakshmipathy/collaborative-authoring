import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    Stack
)

from constructs import Construct

class FrontendStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # import the api gateway invoke url from the backend stack
        invoke_url = cdk.Fn.import_value('ApiGatewayUrl')

        # create a role and policy for the lambda function
        lambda_iam_role = iam.Role(
            self,
            'CADashboardDeploymentRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
        )
        
        iam.Policy(
            self,
            'CADashboardDeploymentPolicy',
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'quicksight:*',
                        'logs:*'
                        ],
                    resources=['*']
                    )
                ],
            roles=[lambda_iam_role]
        )

        # create the lambda function to deploy the merger dashboard
        _lambda.Function(
            self,
            'CADashboardDeploymentFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='quicksight-ui-function',
            code=_lambda.Code.from_asset('./app/quicksight-aac-ui'),
            handler='lambda_function.lambda_handler',
            role=lambda_iam_role,
            timeout=cdk.Duration.minutes(1),
            environment={
                'ACCOUNT_ID': self.account,
                'NAMESPACE': 'default',
                'REGION': self.region,
                'USER_NAME': '<Enter user name here>',
                'API_GATEWAY_URL': invoke_url
                }
            )

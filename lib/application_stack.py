import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    Stack
)
from constructs import Construct

class ApplicationStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # create a role and policy for the lambda function
        lambda_iam_role = iam.Role(
            self, 'LambdaCollaborativeAuthoringRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            )
        
        iam.ManagedPolicy(
            self, 'LambdaCollaborativeAuthoringPolicy',
            managed_policy_name='LambdaCollaborativeAuthoringPolicy',
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
        
        # define the lambda functions
        analysis_merge = _lambda.Function(
            self, 'CollaborativeAuthoringFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='analysis-merge-function',
            code=_lambda.Code.from_asset('./app'),
            handler='lambda_function.lambda_handler',
            role=lambda_iam_role,
            timeout=cdk.Duration.minutes(1),
            environment={
                'REGION': '<Enter region here>',
                'ACCOUNT_ID': '<Enter QuickSight account ID here>',
                'USER_NAME': '<Enter QuickSight user name here>',
                'FIRST_ANALYSIS_ID': '<Enter first analysis ID here>',
                'SECOND_ANALYSIS_ID': '<Enter second analysis ID here>',
                'SOURCE_ANALYSIS_ID': '<Enter source analysis ID here>',
                'TARGET_ANALYSIS_NAME': '<Enter target analysis name here>',
                'TARGET_ANALYSIS_ID': '<Enter target analysis ID here>',
                'ACTION': '<Enter action here>'
                }
            )
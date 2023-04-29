import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    Stack
)
from constructs import Construct

class BackendStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # import the cognito user pool client id from AuthenticationStack
        user_pool_client_id = cdk.Fn.import_value('UserPoolClientId')
        
        # import the cognito user pool domain from AuthenticationStack
        domain_name = cdk.Fn.import_value('UserPoolDomainUrl')

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
            code=_lambda.Code.from_asset('./app/quicksight-aac-analysis'),
            handler='lambda_function.lambda_handler',
            role=lambda_iam_role,
            timeout=cdk.Duration.minutes(1),
            environment={
                'CognitoClientId': user_pool_client_id,
                'CognitoDomainUrl': f"https://{domain_name}.auth.us-east-1.amazoncognito.com"
                }
            )
        
        sheet_merge = _lambda.Function(
            self, 'SheetMergeFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='sheet-merge-function',
            code=_lambda.Code.from_asset('./app/quicksight-aac-sheet'),
            handler='lambda_function.lambda_handler',
            role=lambda_iam_role,
            timeout=cdk.Duration.minutes(1),
            environment={
                'CognitoClientId': user_pool_client_id,
                'CognitoDomainUrl': f"https://{domain_name}.auth.us-east-1.amazoncognito.com"
                }
            )
        
        visual_merge = _lambda.Function(
            self, 'VisualMergeFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name='visual-merge-function',
            code=_lambda.Code.from_asset('./app/quicksight-aac-visual'),
            handler='lambda_function.lambda_handler',
            role=lambda_iam_role,
            timeout=cdk.Duration.minutes(1),
            environment={
                'CognitoClientId': user_pool_client_id,
                'CognitoDomainUrl': f"https://{domain_name}.auth.us-east-1.amazoncognito.com"
                }
            )
        
        # create the API Gateway
        api = apigw.RestApi(
            self, 'ApiGateway',
            rest_api_name='cdk-automation-api-gateway',
            description='This is the gateway to trigger the merge functions in QuickSight',
            deploy_options={
                'stage_name': 'Dev'
                },
            )
        
        # add analysis merge resource to the API Gateway
        analysis_merge_resource = api.root.add_resource('qs-aac-analysis-api')
        
        # add the GET method to the analysis merge resource
        analysis_get_method = analysis_merge_resource.add_method(
            'GET',
            apigw.LambdaIntegration(
                analysis_merge,
                proxy=True,
                allow_test_invoke=False,
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code='200',
                        response_templates={
                            'application/json': 'Empty'
                            },
                        response_parameters={
                            'method.response.header.Access-Control-Allow-Origin': "'*'"
                            }
                        )
                    ]
                ),
            )
        
        analysis_get_method.add_method_response(
            status_code='200',
            response_models={
                'application/json': apigw.Model.EMPTY_MODEL
                },
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True,
                }
            )
        
        # add sheet merge resource to the API Gateway
        sheet_merge_resource = api.root.add_resource('qs-aac-sheet-api')
        
        # add the GET method to the sheet merge resource
        sheet_get_method = sheet_merge_resource.add_method(
            'GET',
            apigw.LambdaIntegration(
                sheet_merge,
                proxy=True,
                allow_test_invoke=False,
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code='200',
                        response_templates={
                            'application/json': 'Empty'
                            },
                        response_parameters={
                            'method.response.header.Access-Control-Allow-Origin': "'*'"
                            }
                        ),
                    ]
                )
            )
        
        sheet_get_method.add_method_response(
            status_code='200',
            response_models={
                'application/json': apigw.Model.EMPTY_MODEL
                },
            response_parameters={   
                'method.response.header.Access-Control-Allow-Origin': True,
                }
            )
        
        # add visual merge resource to the API Gateway
        visual_merge_resource = api.root.add_resource('qs-aac-visual-api')
        
        # add the GET method to the visual merge resource
        visual_get_method = visual_merge_resource.add_method(
            'GET',
            apigw.LambdaIntegration(
                visual_merge,
                proxy=True,
                allow_test_invoke=False,
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code='200',
                        response_templates={
                            'application/json': 'Empty'
                            },
                        response_parameters={
                            'method.response.header.Access-Control-Allow-Origin': "'*'"
                            }
                        ),
                    ]
                )
            )
        
        visual_get_method.add_method_response(
            status_code='200',
            response_models={
                'application/json': apigw.Model.EMPTY_MODEL
                },
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True,
                }
            )
        
        # export the API Gateway URL
        cdk.CfnOutput(
            self, 'ApiGatewayUrl',
            value=api.url,
            export_name='ApiGatewayUrl'
            )
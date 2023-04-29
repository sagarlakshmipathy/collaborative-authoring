import aws_cdk as cdk
from aws_cdk import (
    aws_cognito as cognito,
    Stack
)
from constructs import Construct

class AuthenticationStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # create the Cognito User Pool
        user_pool = cognito.UserPool(
            self, 'UserPool',
            sign_in_aliases={
                'email': True
                },
            auto_verify={
                'email': True
                }
            )
        
        # create the Cognito User Pool Client
        cognito_user_pool_client = user_pool.add_client(
            'UserPoolClient',
            generate_secret=True,
            auth_flows={
                "admin_user_password": True,
                "user_srp": True,
                "custom": True
                }
            )
        
        # create the Cognito User Pool Domain
        cognito_user_pool_domain = user_pool.add_domain(
            'UserPoolDomain',
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"collaborative-authoring-domain-{self.account}"
                )
            )
        
        # export cognito user pool client id
        cdk.CfnOutput(
            self, 'UserPoolClientId',
            value=cognito_user_pool_client.user_pool_client_id,
            export_name="UserPoolClientId"
            )
        
        # export cognito user pool domain url
        cdk.CfnOutput(
            self, 'UserPoolDomainUrl',
            value=cognito_user_pool_domain.domain_name,
            export_name="UserPoolDomainUrl"
            )

        # export cognito user pool id
        cdk.CfnOutput(
            self, 'UserPoolId',
            value=user_pool.user_pool_id,
            export_name="UserPoolId"
            )
#!/usr/bin/env python3
import aws_cdk as cdk

from lib.backend_stack import BackendStack
from lib.frontend_stack import FrontendStack
from lib.authentication_stack import AuthenticationStack
from lib.cognito_update_stack import CognitoUpdateStack

app = cdk.App()
AuthenticationStack(app, "AuthenticationStack")
BackendStack(app, "BackendStack")
FrontendStack(app, "FrontendStack")
CognitoUpdateStack(app, "CognitoUpdateStack")

app.synth()

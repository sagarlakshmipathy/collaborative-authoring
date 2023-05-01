#!/usr/bin/env python3
import aws_cdk as cdk

from lib.application_stack import ApplicationStack

app = cdk.App()
ApplicationStack(app, "ApplicationStack")

app.synth()

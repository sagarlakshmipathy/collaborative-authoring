import boto3
import json
import time

def lambda_handler(event, context):

    qs_client = boto3.client('quicksight')
    account_id = event['ACCOUNT_ID']
    namespace = event['NAMESPACE']
    user_name = event['USER_NAME']
    api_gateway_url = event['API_GATEWAY_URL']
    dashboard_name = 'Quicksight Self Service Reporting Dashboard'
    dashboard_id = 'quicksight-self-service-reporting-dashboard'
    with open('dashboard.json', 'r') as f:
        dashboard_definition = json.load(f)


    # create the dashboard
    qs_client.create_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboard_id,
        Name=dashboard_name,
        Definition=dashboard_definition,
        Permissions=[
            {
                'Principal': f"arn:aws:quicksight:us-east-1:{namespace}/{user_name}",
                'Actions': [
                    'quicksight:DescribeDashboard',
                    'quicksight:ListDashboardVersions',
                    'quicksight:UpdateDashboardPermissions',
                    'quicksight:QueryDashboard',
                    'quicksight:UpdateDashboard',
                    'quicksight:DeleteDashboard',
                    'quicksight:DescribeDashboardPermissions',
                    'quicksight:UpdateDashboardPublishedVersion',
                    'quicksight:DescribeDashboardVersions',
                    'quicksight:CreateDashboardPermission',
                ]
            },
        ],
    )

    time.sleep(2)

    describe_dashboard_response = qs_client.describe_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboard_id
    )

    if describe_dashboard_response['Status'] == 200:
        print('Dashboard created successfully')

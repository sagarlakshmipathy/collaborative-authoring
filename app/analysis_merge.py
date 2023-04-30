import boto3
import json
import os


def lambda_handler(event, context):
    # Quicksight config
    identity_region = os.environ['REGION']
    qs_client = boto3.client("quicksight", region_name=identity_region)

    # variables
    account_id = os.environ['ACCOUNT_ID']
    user_name = os.environ['USER_NAME']
    first_analysis_id = os.environ['FIRST_ANALYSIS_ID']
    second_analysis_id = os.environ['SECOND_ANALYSIS_ID']
    source_analysis_id = os.environ['SOURCE_ANALYSIS_ID']
    target_analysis_name = os.environ['TARGET_ANALYSIS_NAME']
    target_analysis_id = os.environ['TARGET_ANALYSIS_ID']
    action = os.environ['ACTION']

    # qualify the update call
    if action == 'Update':
        try:
            describe_response = qs_client.describe_analysis(
                AnalysisId=target_analysis_id, AwsAccountId=account_id)
            if describe_response['Analysis']['AnalysisId'] == target_analysis_id:
                response = merge_analyses_update(
                    account_id=account_id,
                    source_analysis_id=source_analysis_id,
                    target_analysis_id=target_analysis_id,
                    target_analysis_name=target_analysis_name,
                    qs_client=qs_client
                )
                print(response)
                return response
            else:
                print(f"Target Analysis ID can only be {target_analysis_id}")
                return f"Target Analysis ID can only be {target_analysis_id}"
        except Exception as e:
            print(json.loads(json.dumps(e, indent=4, default=str)))
            return json.loads(json.dumps(e, indent=4, default=str))
    else:
        response = merge_analyses_create(
            account_id=account_id,
            first_analysis_id=first_analysis_id,
            second_analysis_id=second_analysis_id,
            target_analysis_id=target_analysis_id,
            target_analysis_name=target_analysis_name,
            user_name=user_name,
            namespace='default',
            qs_client=qs_client
        )
        print(response)
        return response


def merge_analyses_create(account_id, first_analysis_id, second_analysis_id, target_analysis_id, target_analysis_name, user_name, namespace, qs_client):
    """Merges the first sheet to the target analysis and
            brings filters, calculated fields and visuals with it

    Args:
        account_id (int): AWS account ID
        first_analysis_id (str): Analysis ID of the first analysis
        first_sheet_id (str): Sheet ID that needs to be merged to the target analysis
        target_analysis_id (str): Analysis ID of the target analysis
        identity_region (str): QuickSight Region
    """

    # definition of the target analysis
    target_analysis_definition = {
        'Definition': {
            'DataSetIdentifierDeclarations': [],
            'Sheets': [
            ],
            'CalculatedFields': [],
            'ParameterDeclarations': [],
            'FilterGroups': [],
            'ColumnConfigurations': [],
            'AnalysisDefaults': {
                'DefaultNewSheetConfiguration': {
                    'InteractiveLayoutConfiguration': {
                        'Grid': {
                            'CanvasSizeOptions': {
                                'ScreenCanvasSizeOptions': {
                                    'ResizeOption': 'FIXED',
                                    'OptimizedViewPortWidth': '1600px'
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # get the definition of the first analysis
    first_analysis_definition = qs_client.describe_analysis_definition(
        AwsAccountId=account_id,
        AnalysisId=first_analysis_id
    )

    # get the definition of the second analysis
    second_analysis_definition = qs_client.describe_analysis_definition(
        AwsAccountId=account_id,
        AnalysisId=second_analysis_id
    )

    # write the first analysis definition
    # with open('first_analysis_definition.json', 'w') as outfile:
    #     json.dump(first_analysis_definition, outfile)

    # write the second analysis definition
    # with open('second_analysis_definition.json', 'w') as outfile:
    #     json.dump(second_analysis_definition, outfile)

    class DuplicateParameterNameException(Exception):
        """Exception raised when a duplicate parameter name is found"""
        pass

    class DuplicateCalculatedFieldException(Exception):
        """Exception raised when a duplicate calculated field is found"""
        pass

    def get_dataset_identifier(dataset_arn, datasets):
        """Gets the dataset identifier for a given dataset arn

        Args:
            dataset_arn (str): dataset arn
            datasets (list): list of datasets

        Returns:
            str: dataset identifier
        """
        for dataset in datasets:
            if dataset['DataSetArn'] == dataset_arn:
                return dataset['Identifier']

    def get_dataset_arn(dataset_identifier, datasets):
        """Gets the dataset arn for a given dataset identifier

        Args:
            dataset_identifier (str): dataset identifier
            datasets (list): list of datasets

        Returns:
            str: dataset arn
        """
        for datasetnum in range(len(datasets)):
            if datasets[datasetnum]['Identifier'] == dataset_identifier:
                return datasets[datasetnum]['DataSetArn']

    def update_dataset_identifier(dataset_identifier):
        """Updates the dataset identifier with a new value

        Args:
            dataset_identifier (str): dataset identifier

        Returns:
            str: new dataset identifier
        """
        if dataset_identifier[-1] in '1234567890' and dataset_identifier[-2] == '-':
            identifier_updated = int(dataset_identifier[-1]) + 1
        else:
            identifier_updated = dataset_identifier + '-1'
        return identifier_updated

    def update_nested_dict(in_dict, key, value, match_value=None):
        """Replaces the existing value of the key with a new value

        Args:
            in_dict(dict): dictionary to be executed
            key (str): key to search for ; example 'DataSetIdentifier' or 'Identifier'...
            value (str): value to replace with ; example 'NewValue'

        Returns:
            doesn't return anything but updates the dictionary in place
        """
        for k, v in in_dict.items():
            if key == k and v == match_value:
                in_dict[k] = value
            elif isinstance(v, dict):
                update_nested_dict(v, key, value, match_value)
            elif isinstance(v, list):
                for o in v:
                    if isinstance(o, dict):
                        update_nested_dict(o, key, value, match_value)

    # variable definitions
    target_dataset_arns = set()
    target_dataset_identifiers = set()

    first_analysis_datasets = first_analysis_definition['Definition']['DataSetIdentifierDeclarations']
    first_analysis_parameters = first_analysis_definition['Definition']['ParameterDeclarations']
    first_analysis_filter_groups = first_analysis_definition['Definition']['FilterGroups']
    first_analysis_calculated_fields = first_analysis_definition['Definition']['CalculatedFields']
    first_analysis_sheets = first_analysis_definition['Definition']['Sheets']
    try:
        first_analysis_theme = first_analysis_definition['ThemeArn']
    except KeyError:
        first_analysis_theme = None

    second_analysis_datasets = second_analysis_definition[
        'Definition']['DataSetIdentifierDeclarations']
    second_analysis_dataset_identifiers = set()
    second_analysis_sheets = second_analysis_definition['Definition']['Sheets']
    second_analysis_parameters = second_analysis_definition['Definition']['ParameterDeclarations']
    second_analysis_filter_groups = second_analysis_definition['Definition']['FilterGroups']
    second_analysis_calculated_fields = second_analysis_definition[
        'Definition']['CalculatedFields']

    target_datasets = target_analysis_definition['Definition']['DataSetIdentifierDeclarations']
    target_sheets = target_analysis_definition['Definition']['Sheets']
    target_parameters = target_analysis_definition['Definition']['ParameterDeclarations']
    target_filters = target_analysis_definition['Definition']['FilterGroups']
    target_calculated_fields = target_analysis_definition['Definition']['CalculatedFields']

    # copy parameters from first analysis to target
    for parameter in first_analysis_parameters:
        target_parameters.append(parameter)

    try:
        first_analysis_parameter_names = []
        for parameter in first_analysis_parameters:
            parameter_type = next(iter(parameter))
            parameter_name = parameter[parameter_type]['Name']
            first_analysis_parameter_names.append(parameter_name)

        # collect the second analysis' parameter names
        second_analysis_parameter_names = []
        for parameter in second_analysis_parameters:
            parameter_type = next(iter(parameter))
            parameter_name = parameter[parameter_type]['Name']
            second_analysis_parameter_names.append(parameter_name)

        # decide whether or not to copy the second analysis' parameters to target
        for parameter in second_analysis_parameters:
            parameter_type = next(iter(parameter))
            parameter_name = parameter[parameter_type]['Name']
            if parameter in first_analysis_parameters:
                continue
            elif parameter_name in first_analysis_parameter_names:
                raise DuplicateParameterNameException(
                    f"Parameter: {parameter_name} exists in both the analyses, change the name of the parameter in one of the analyses and retry")
            else:
                target_parameters.append(parameter)

    except DuplicateParameterNameException as e:
        return json.loads(json.dumps(e, indent=4, default=str))

    # dataset section
    # copy all datasets from first analysis to target
    for dataset in first_analysis_datasets:
        target_dataset_arns.add(dataset['DataSetArn'])
        target_datasets.append(dataset)

    # find out the common dataset arns in source and target
    second_analysis_dataset_arns = set()
    for dataset in target_datasets:
        target_dataset_arns.add(dataset['DataSetArn'])
        target_dataset_identifiers.add(dataset['Identifier'])
    for dataset in second_analysis_datasets:
        second_analysis_dataset_arns.add(dataset['DataSetArn'])
        second_analysis_dataset_identifiers.add(dataset['Identifier'])
    common_arns = set.intersection(
        target_dataset_arns, second_analysis_dataset_arns)
    common_identifiers = set.intersection(
        target_dataset_identifiers, second_analysis_dataset_identifiers)

    # check if the dataset identifiers are different in source and target
    dataset_arns_that_need_identifier_replacement = set()
    dataset_identifiers_that_needs_update = set()
    same_dataset_arn_different_identifier = False
    same_dataset_identifier_different_arn = False

    if common_arns:
        for arn in common_arns:
            target_dataset_identifier = get_dataset_identifier(
                arn, target_datasets)
            second_analysis_dataset_identifier = get_dataset_identifier(
                arn, second_analysis_datasets)
            if target_dataset_identifier != second_analysis_dataset_identifier:
                dataset_arns_that_need_identifier_replacement.add(arn)
                same_dataset_arn_different_identifier = True

    # source identifiers for arn replacement list
    if same_dataset_arn_different_identifier:
        second_analysis_identifiers_for_common_arns = []
        target_identifiers_for_common_arns = []
        for arn in common_arns:
            second_analysis_identifiers_for_common_arns.append(
                get_dataset_identifier(arn, second_analysis_datasets))
            target_identifiers_for_common_arns.append(
                get_dataset_identifier(arn, target_datasets))

    if common_identifiers:
        for identifier in common_identifiers:
            target_dataset_arn = get_dataset_arn(identifier, target_datasets)
            second_analysis_dataset_arn = get_dataset_arn(
                identifier, second_analysis_datasets)
            if target_dataset_arn != second_analysis_dataset_arn:
                dataset_identifiers_that_needs_update.add(identifier)
                same_dataset_identifier_different_arn = True

    # copy datasets from second analysis if not present already in target
    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for dataset in second_analysis_datasets:
                if dataset['Identifier'] == dataset_identifier:
                    update_nested_dict(dataset, 'Identifier',
                                       updated_dataset_identifier, dataset_identifier)

    if same_dataset_arn_different_identifier:
        for dataset_arn in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_arn, second_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_arn, target_datasets)
            for dataset in second_analysis_datasets:
                if dataset['DataSetArn'] == dataset_arn:
                    update_nested_dict(dataset, 'Identifier',
                                       target_dataset_identifier, source_dataset_identifier)

    for dataset in second_analysis_datasets:
        if dataset not in target_datasets:
            target_datasets.append(dataset)

    # sheets section
    # copy all sheets from first analysis to target
    for sheet in first_analysis_sheets:
        target_sheets.append(sheet)

    # copy sheets from second analysis which are not present already in target
    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for sheet in second_analysis_sheets:
                update_nested_dict(sheet, 'DataSetIdentifier',
                                   updated_dataset_identifier, dataset_identifier)

    if same_dataset_arn_different_identifier:
        for dataset_identifier in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_identifier, second_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_identifier, target_datasets)
            for sheet in second_analysis_sheets:
                update_nested_dict(sheet, 'DataSetIdentifier',
                                   target_dataset_identifier, source_dataset_identifier)

    for sheet in second_analysis_sheets:
        if sheet not in target_sheets:
            target_sheets.append(sheet)

    # filters section
    # copy all filters from first analysis to target
    for filter_group in first_analysis_filter_groups:
        target_filters.append(filter_group)

    # copy filters from second analysis which are not present already in target
    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for filter_group in second_analysis_filter_groups:
                update_nested_dict(filter_group, 'DataSetIdentifier',
                                   updated_dataset_identifier, dataset_identifier)

    if same_dataset_arn_different_identifier:
        for dataset_identifier in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_identifier, second_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_identifier, target_datasets)
            update_nested_dict(filter_group, 'DataSetIdentifier',
                               target_dataset_identifier, source_dataset_identifier)

    for filter_group in second_analysis_filter_groups:
        if filter_group not in target_filters:
            target_filters.append(filter_group)

    # copy the calculated fields in source to target
    temp_second_analysis_calculated_fields = []
    for calculated_field in first_analysis_calculated_fields:
        target_calculated_fields.append(calculated_field)

    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for calculated_field in second_analysis_calculated_fields:
                update_nested_dict(calculated_field, 'DataSetIdentifier',
                                   updated_dataset_identifier, dataset_identifier)
                if calculated_field not in temp_second_analysis_calculated_fields:
                    temp_second_analysis_calculated_fields.append(
                        calculated_field)

    if same_dataset_arn_different_identifier:
        for dataset_identifier in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_identifier, second_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_identifier, target_datasets)
            update_nested_dict(calculated_field, 'DataSetIdentifier',
                               target_dataset_identifier, source_dataset_identifier)

    try:
        target_calculated_field_identifiers = []
        for calculated_field in target_calculated_fields:
            calculated_field_identifier = f"{calculated_field['Name']}->{calculated_field['DataSetIdentifier']}"
            target_calculated_field_identifiers.append(
                calculated_field_identifier)

        for calculated_field in temp_second_analysis_calculated_fields:
            calculated_field_identifier = f"{calculated_field['Name']}->{calculated_field['DataSetIdentifier']}"
            if calculated_field in target_calculated_fields:
                continue
            elif calculated_field_identifier in target_calculated_field_identifiers:
                raise DuplicateCalculatedFieldException(
                    f"Calculated field: {calculated_field['Name']} exists in both the analyses, change the name of the calculated field in one of the analyses and retry")
            else:
                target_calculated_fields.append(calculated_field)

    except DuplicateCalculatedFieldException as e:
        return json.loads(json.dumps(e, indent=4, default=str))

    # write the target analysis definition to a json file
    json_object = json.dumps(
        target_analysis_definition, indent=4, default=str)
    with open("./target_analysis_definition_analysis_merge.json", "w") as outfile:
        outfile.write(json_object)

    # delete the analysis if it already exists
    try:
        qs_client.delete_analysis(
            AwsAccountId=account_id, AnalysisId=target_analysis_id)
    except:
        pass

    try:
        if first_analysis_theme:
            qs_client.create_analysis(
                AwsAccountId=account_id,
                AnalysisId=target_analysis_id,
                Name=target_analysis_name,
                Definition=target_analysis_definition['Definition'],
                Permissions=[
                    {
                        'Principal': 'arn:aws:quicksight:us-east-1:{}:user/{}/{}'
                        .format(account_id, namespace, user_name),
                        'Actions': ['quicksight:RestoreAnalysis',
                                    'quicksight:UpdateAnalysisPermissions',
                                    'quicksight:DeleteAnalysis',
                                    'quicksight:QueryAnalysis',
                                    'quicksight:DescribeAnalysisPermissions',
                                    'quicksight:DescribeAnalysis',
                                    'quicksight:UpdateAnalysis'
                                    ]
                    }
                ],
                ThemeArn=first_analysis_theme
            )
            return f"Analysis {target_analysis_name} created successfully"
        else:
            qs_client.create_analysis(
                AwsAccountId=account_id,
                AnalysisId=target_analysis_id,
                Name=target_analysis_name,
                Definition=target_analysis_definition['Definition'],
                Permissions=[
                    {
                        'Principal': 'arn:aws:quicksight:us-east-1:{}:user/{}/{}'
                        .format(account_id, namespace, user_name),
                        'Actions': ['quicksight:RestoreAnalysis',
                                    'quicksight:UpdateAnalysisPermissions',
                                    'quicksight:DeleteAnalysis',
                                    'quicksight:QueryAnalysis',
                                    'quicksight:DescribeAnalysisPermissions',
                                    'quicksight:DescribeAnalysis',
                                    'quicksight:UpdateAnalysis'
                                    ]
                    }
                ]
            )
            return f"Analysis {target_analysis_name} created successfully"

    except Exception as e:
        return json.loads(json.dumps(e, indent=4, default=str))


def merge_analyses_update(account_id, source_analysis_id, target_analysis_id, target_analysis_name, qs_client):
    """Merges the target sheet to the target analysis and
            brings filters, calculated fields and visuals with it

    Args:
        account_id (int): AWS account ID
        target_analysis_id (str): Analysis ID of the target analysis
        target_sheet_id (str): Sheet ID that needs to be merged to the target analysis
        target_analysis_id (str): Analysis ID of the target analysis
        identity_region (str): QuickSight Region
    """

    # definition of the target analysis
    target_analysis_definition = qs_client.describe_analysis_definition(
        AwsAccountId=account_id,
        AnalysisId=target_analysis_id)

    # definition of the source analysis
    source_analysis_definition = qs_client.describe_analysis_definition(
        AwsAccountId=account_id,
        AnalysisId=source_analysis_id
    )

    # write the target analysis definition
    # json_object = json.dumps(
    #     source_analysis_definition, indent=4, default=str)
    # with open("./source_analysis_definition.json", "w") as outfile:
    #     outfile.write(json_object)

    # write the source analysis definition
    # json_object = json.dumps(
    #     target_analysis_definition, indent=4, default=str)
    # with open("./target_analysis_definition_initial.json", "w") as outfile:
    #     outfile.write(json_object)

    class DuplicateParameterNameException(Exception):
        """Exception raised when a duplicate parameter name is found"""
        pass

    class DuplicateCalculatedFieldException(Exception):
        """Exception raised when a duplicate calculated field is found"""
        pass

    def get_dataset_identifier(dataset_arn, datasets):
        """Gets the dataset identifier for a given dataset arn

        Args:
            dataset_arn (str): dataset arn
            datasets (list): list of datasets

        Returns:
            str: dataset identifier
        """
        for dataset in datasets:
            if dataset['DataSetArn'] == dataset_arn:
                return dataset['Identifier']

    def get_dataset_arn(dataset_identifier, datasets):
        """Gets the dataset arn for a given dataset identifier

        Args:
            dataset_identifier (str): dataset identifier
            datasets (list): list of datasets

        Returns:
            str: dataset arn
        """
        for datasetnum in range(len(datasets)):
            if datasets[datasetnum]['Identifier'] == dataset_identifier:
                return datasets[datasetnum]['DataSetArn']

    def update_dataset_identifier(dataset_identifier):
        """Updates the dataset identifier with a new value

        Args:
            dataset_identifier (str): dataset identifier

        Returns:
            str: new dataset identifier
        """
        if dataset_identifier[-1] in '1234567890' and dataset_identifier[-2] == '-':
            identifier_updated = int(dataset_identifier[-1]) + 1
        else:
            identifier_updated = dataset_identifier + '-1'
        return identifier_updated

    def update_nested_dict(in_dict, key, value, match_value=None):
        """Replaces the existing value of the key with a new value

        Args:
            in_dict(dict): dictionary to be executed
            key (str): key to search for ; example 'DataSetIdentifier' or 'Identifier'...
            value (str): value to replace with ; example 'NewValue'

        Returns:
            doesn't return anything but updates the dictionary in place
        """
        for k, v in in_dict.items():
            if key == k and v == match_value:
                in_dict[k] = value
            elif isinstance(v, dict):
                update_nested_dict(v, key, value, match_value)
            elif isinstance(v, list):
                for o in v:
                    if isinstance(o, dict):
                        update_nested_dict(o, key, value, match_value)

    # variable definitions
    target_analysis_dataset_arns = set()
    target_analysis_dataset_identifiers = set()
    target_analysis_datasets = target_analysis_definition[
        'Definition']['DataSetIdentifierDeclarations']
    target_analysis_parameters = target_analysis_definition['Definition']['ParameterDeclarations']
    target_analysis_filter_groups = target_analysis_definition['Definition']['FilterGroups']
    target_analysis_calculated_fields = target_analysis_definition[
        'Definition']['CalculatedFields']
    target_analysis_sheets = target_analysis_definition['Definition']['Sheets']
    try:
        target_analysis_theme = target_analysis_definition['ThemeArn']
    except KeyError:
        target_analysis_theme = None

    source_analysis_dataset_arns = set()
    source_analysis_dataset_identifiers = set()
    source_analysis_datasets = source_analysis_definition[
        'Definition']['DataSetIdentifierDeclarations']
    source_analysis_sheets = source_analysis_definition['Definition']['Sheets']
    source_analysis_parameters = source_analysis_definition['Definition']['ParameterDeclarations']
    source_analysis_filter_groups = source_analysis_definition['Definition']['FilterGroups']
    source_analysis_calculated_fields = source_analysis_definition[
        'Definition']['CalculatedFields']

    # append parameters from source analysis to target
    try:
        target_analysis_parameter_names = []
        for parameter in target_analysis_parameters:
            parameter_type = next(iter(parameter))
            parameter_name = parameter[parameter_type]['Name']
            target_analysis_parameter_names.append(parameter_name)

        # collect the source analysis' parameter names
        source_analysis_parameter_names = []
        for parameter in source_analysis_parameters:
            parameter_type = next(iter(parameter))
            parameter_name = parameter[parameter_type]['Name']
            source_analysis_parameter_names.append(parameter_name)

        # decide whether or not to copy the source analysis' parameters to target
        for parameter in source_analysis_parameters:
            parameter_type = next(iter(parameter))
            parameter_name = parameter[parameter_type]['Name']
            if parameter in target_analysis_parameters:
                continue
            elif parameter_name in target_analysis_parameter_names:
                raise DuplicateParameterNameException(
                    f"Parameter: {parameter_name} exists in both the analyses, change the name of the parameter in one of the analyses and retry")
            else:
                target_analysis_parameters.append(parameter)

    except DuplicateParameterNameException as e:
        return json.loads(json.dumps(e, indent=4, default=str))

    # dataset section
    # find out the common dataset arns in source and target
    for dataset in target_analysis_datasets:
        target_analysis_dataset_arns.add(dataset['DataSetArn'])
        target_analysis_dataset_identifiers.add(dataset['Identifier'])
    for dataset in source_analysis_datasets:
        source_analysis_dataset_arns.add(dataset['DataSetArn'])
        source_analysis_dataset_identifiers.add(dataset['Identifier'])
    common_arns = set.intersection(
        target_analysis_dataset_arns, source_analysis_dataset_arns)
    common_identifiers = set.intersection(
        target_analysis_dataset_identifiers, source_analysis_dataset_identifiers)

    # check if the dataset identifiers are different in source and target
    dataset_arns_that_need_identifier_replacement = set()
    dataset_identifiers_that_needs_update = set()
    same_dataset_arn_different_identifier = False
    same_dataset_identifier_different_arn = False

    if common_arns:
        for arn in common_arns:
            target_dataset_identifier = get_dataset_identifier(
                arn, target_analysis_datasets)
            source_analysis_dataset_identifier = get_dataset_identifier(
                arn, source_analysis_datasets)
            if target_dataset_identifier != source_analysis_dataset_identifier:
                dataset_arns_that_need_identifier_replacement.add(arn)
                same_dataset_arn_different_identifier = True

    # source identifiers for arn replacement list
    if same_dataset_arn_different_identifier:
        source_analysis_identifiers_for_common_arns = []
        target_identifiers_for_common_arns = []
        for arn in common_arns:
            source_analysis_identifiers_for_common_arns.append(
                get_dataset_identifier(arn, source_analysis_datasets))
            target_identifiers_for_common_arns.append(
                get_dataset_identifier(arn, target_analysis_datasets))

    if common_identifiers:
        for identifier in common_identifiers:
            target_dataset_arn = get_dataset_arn(
                identifier, target_analysis_datasets)
            source_analysis_dataset_arn = get_dataset_arn(
                identifier, source_analysis_datasets)
            if target_dataset_arn != source_analysis_dataset_arn:
                dataset_identifiers_that_needs_update.add(identifier)
                same_dataset_identifier_different_arn = True

    # copy datasets from source analysis if not present already in target
    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for dataset in source_analysis_datasets:
                if dataset['Identifier'] == dataset_identifier:
                    update_nested_dict(dataset, 'Identifier',
                                       updated_dataset_identifier, dataset_identifier)

    if same_dataset_arn_different_identifier:
        for dataset_arn in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_arn, source_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_arn, target_analysis_datasets)
            for dataset in source_analysis_datasets:
                if dataset['DataSetArn'] == dataset_arn:
                    update_nested_dict(dataset, 'Identifier',
                                       target_dataset_identifier, source_dataset_identifier)

    for dataset in source_analysis_datasets:
        if dataset not in target_analysis_datasets:
            target_analysis_datasets.append(dataset)

    # sheets section
    # copy sheets from source analysis which are not present already in target
    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for sheet in source_analysis_sheets:
                update_nested_dict(sheet, 'DataSetIdentifier',
                                   updated_dataset_identifier, dataset_identifier)

    if same_dataset_arn_different_identifier:
        for dataset_identifier in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_identifier, source_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_identifier, target_analysis_datasets)
            for sheet in source_analysis_sheets:
                update_nested_dict(sheet, 'DataSetIdentifier',
                                   target_dataset_identifier, source_dataset_identifier)

    for sheet in source_analysis_sheets:
        if sheet not in target_analysis_sheets:
            target_analysis_sheets.append(sheet)

    # filters section
    # copy filters from source analysis which are not present already in target
    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for filter_group in source_analysis_filter_groups:
                update_nested_dict(filter_group, 'DataSetIdentifier',
                                   updated_dataset_identifier, dataset_identifier)

    if same_dataset_arn_different_identifier:
        for dataset_identifier in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_identifier, source_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_identifier, target_analysis_datasets)
            update_nested_dict(filter_group, 'DataSetIdentifier',
                               target_dataset_identifier, source_dataset_identifier)

    for filter_group in source_analysis_filter_groups:
        if filter_group not in target_analysis_filter_groups:
            target_analysis_filter_groups.append(filter_group)

    # copy the calculated fields in source to target
    temp_source_analysis_calculated_fields = []

    if same_dataset_identifier_different_arn:
        for dataset_identifier in dataset_identifiers_that_needs_update:
            updated_dataset_identifier = update_dataset_identifier(
                dataset_identifier)
            for calculated_field in source_analysis_calculated_fields:
                update_nested_dict(calculated_field, 'DataSetIdentifier',
                                   updated_dataset_identifier, dataset_identifier)
                if calculated_field not in temp_source_analysis_calculated_fields:
                    temp_source_analysis_calculated_fields.append(
                        calculated_field)

    if same_dataset_arn_different_identifier:
        for dataset_identifier in dataset_arns_that_need_identifier_replacement:
            source_dataset_identifier = get_dataset_identifier(
                dataset_identifier, source_analysis_datasets)
            target_dataset_identifier = get_dataset_identifier(
                dataset_identifier, target_analysis_datasets)
            update_nested_dict(calculated_field, 'DataSetIdentifier',
                               target_dataset_identifier, source_dataset_identifier)
            if calculated_field not in temp_source_analysis_calculated_fields:
                temp_source_analysis_calculated_fields.append(
                    calculated_field)

    if not same_dataset_arn_different_identifier and not same_dataset_identifier_different_arn:
        temp_source_analysis_calculated_fields = source_analysis_calculated_fields

    try:
        target_calculated_field_identifiers = []
        for calculated_field in target_analysis_calculated_fields:
            calculated_field_identifier = f"{calculated_field['Name']}->{calculated_field['DataSetIdentifier']}"
            target_calculated_field_identifiers.append(
                calculated_field_identifier)

        for calculated_field in temp_source_analysis_calculated_fields:
            calculated_field_identifier = f"{calculated_field['Name']}->{calculated_field['DataSetIdentifier']}"
            if calculated_field in target_analysis_calculated_fields:
                continue
            elif calculated_field_identifier in target_calculated_field_identifiers:
                raise DuplicateCalculatedFieldException(
                    f"Calculated field: {calculated_field['Name']} exists in both the analyses, change the name of the calculated field in one of the analyses and retry")
            else:
                target_analysis_calculated_fields.append(calculated_field)

    except DuplicateCalculatedFieldException as e:
        return json.loads(json.dumps(e, indent=4, default=str))

    # write the target analysis definition to a json file
    # json_object = json.dumps(
    #     target_analysis_definition, indent=4, default=str)
    # with open("./target_analysis_definition_analysis_merge.json", "w") as outfile:
    #     outfile.write(json_object)

    try:
        if target_analysis_theme:
            qs_client.update_analysis(
                AwsAccountId=account_id,
                AnalysisId=target_analysis_id,
                Name=target_analysis_name,
                Definition=target_analysis_definition['Definition'],
                ThemeArn=target_analysis_theme
            )
            return f"Analysis {target_analysis_name} updated successfully"
        else:
            qs_client.update_analysis(
                AwsAccountId=account_id,
                AnalysisId=target_analysis_id,
                Name=target_analysis_name,
                Definition=target_analysis_definition['Definition']
            )
            return f"Analysis {target_analysis_name} updated successfully"

    except Exception as e:
        return json.loads(json.dumps(e, indent=4, default=str))

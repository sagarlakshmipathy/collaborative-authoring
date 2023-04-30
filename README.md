
# Collaborative Authoring in Amazon QuickSight!

## About the project
Today authors cannot merge two analyses together to create a new analysis in QuickSight. Traditionally, they would replicate all the visual from first analysis in the second one. 
1. What if there are 100 visuals in the each analyses? 
2. What if there are two authors who want to collaborate and complete one dashboard soon? 

This tool can help the authors to merge the analyses after creating them. This tool replicates the datasets, sheets, visuals, parameters, and even calculated fields. Wherever there are conflicts, i.e. if there are two calculated fields with the same name in both of them but different expressions then it will throw an exception; it follows a similar behavior for parameters as well.

Here's an example:
Use case: A user wants to merge `analysis-id-1` with `analysis-id-2` along with all the calculated fields, parameters and sheets.

Steps:
1. Login to AWS Lambda console and choose the `analysis-merge-function`
2. Navigate to `Configuration` tab and choose `Environment Variables`
3. Pass the variables as below:
        `REGION`: us-east-1 
        `ACCOUNT_ID`: 0123456789
        `USER_NAME`: user-name
        `FIRST_ANALYSIS_ID`: analysis-id-1
        `SECOND_ANALYSIS_ID`: analysis-id-2
        `TARGET_ANALYSIS_NAME`: Merged Analysis
        `TARGET_ANALYSIS_ID`: merged-analysis-id
        `ACTION`: Create
4. Create a sample test event
5. Hit test and voila! You should see a message saying `Analysis merged-analysis-id created successfully.`


Here is the high level overview of the architecture:

<img width="317" alt="image" src="https://user-images.githubusercontent.com/30472234/235339232-b8e5bbc4-93c6-4a43-ba3a-559031424913.png">



## Deployment steps

This repoository helps admins setup self service reporting capability for their readers.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

Once you have installed the requirements.txt file, you need to verify if you have the pre-requisite packages for CDK

```
$ node -v
$ cdk --version
$ python --version
```

If need be, install

```
$ sudo yum install npm
```
```
$ nvm install 16
```
```
$ npm install -g aws-cdk
```
```
$ curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
$ unzip awscliv2.zip
$ sudo ./aws/install
```

At this point you can now synthesize the CloudFormation template for this code. CDK CLI requires you to be in the same folder as cdk.json is present.

```
$ cdk synth
```

```
$ cdk bootstrap
```
```
$ cdk deploy --all
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

### Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

 Enjoy!

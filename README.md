<img src="https://static.mparticle.com/sdk/logo.svg" width="280">

## Redshift Ip Whitelist Tool

This repo contains Python code for a AWS Lambda function that can be used to manage IP whitelist on a Redshift cluster. mParticle clients can set up a Lambda function that will automatically make sure all IP's mParticle servers uses are whitelisted so that data can be loaded into Redshift without interruptions.

### Instructions

Please follow these steps to set up a AWS Lambda function.

1. Create a new VPC security group and note the security group Id and the aws region. Leave the inbound rules empty as they will be managed by the Lambda function.
2. Clone this repo to your machine, and zip the conent of the repo directory, which you will upload to AWS in the next step. 
    - **Important**: make sure you zip the directory content, not the directory, i.e., the client.py file is at the root of the zip.
4. Create a new AWS Lambda function. 
 - You don't need to pick any template. 
 - Set the runtime of the Lambda function to Python, upload the zipped file, and set the Lambda function handler to `client.lambda_handler`. 
 - Create a new role for the Lambda function.
 - Set the timeout value to 1 min to give enough time for the function to run. 
5. Create a new AWS policy, paste in the following json, and attach it to the new role. Make sure you replace the `[aws-region]`, `[accountid-here]`, and `[sg-securitygroupid-here]` with your AWS account Id and the security group Id from setp 1.

    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Stmt1463090293000",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstanceAttribute",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeInstances",
                    "ec2:DescribeNetworkAcls",
                    "ec2:DescribeSecurityGroups"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Sid": "Stmt1463090293001",
                "Effect": "Allow",
                "Action": [
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:RevokeSecurityGroupIngress"
                ],
                "Resource": [
                    "arn:aws:ec2:[aws-region]:[accountid-here]:security-group/[sg-securitygroupid-here]"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }
        ]
    }
    ```

6. Finally, we need to configure a trigger to call the Lambda function on a regular basis. Go to CloudWatch and create a new rule (under Events > Rules section accessible from the left panel). We suggest that you use a schedule of a fixed rate of 12 hours as the event selector for the rule. The target of the rule should be the Lambda function created above. In the configure input section, pick "Constant (JSON text)", and put in the following JSON with proper values populated. The "security_group_id" is the security group Id created in step 1, the "redshift_port" is that redshift port of your cluster, and the "is_vpc" represents if your cluster is in VPC or not.
    ```
    {
        "security_group_id": "security group id created in step 1", 
        "redshift_port": 5439, 
        "is_vpc": true,
        "aws_region": "aws region noted in step 1"
    }
    ```


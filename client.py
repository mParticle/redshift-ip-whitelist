import boto3, botocore, requests

def lambda_handler(event, context):
	# **** Set this Security Group in input json.  It must be dedicated to mParticle.
    destination_security_group_id = event['security_group_id'] 
	# **** Set the redshift port in input json
    redshift_port = event['redshift_port']
	# **** Indicate whether your redshift cluster is in VPC or not in input json.
    is_vpc = event['is_vpc']
    
    r = requests.get('https://2g26abvcj4.execute-api.us-east-1.amazonaws.com/prod/redshift-ips')
    payload = r.json()
    
    if (is_vpc):
        ec2 = boto3.resource('ec2')
        security_group = ec2.SecurityGroup(destination_security_group_id)
        ip_permissions = []
        
        for ip in payload['trusted_ips']:
            try:
                response = security_group.authorize_ingress(IpProtocol="tcp",FromPort=redshift_port, ToPort=redshift_port, CidrIp=ip)
                print response 
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                    print 'Entry Already Exists'
                    continue
                else:
                    print e.response['Error']['Code']
    else:
        client = boto3.client('redshift')
        i = 0
        for ip in payload['trusted_ips']:
            i += 1
            csgName = 'mparticle-redshift-' + str(i//20 + 1)
            create_csg(csgName)
            try:
                response = client.authorize_cluster_security_group_ingress(ClusterSecurityGroupName=csgName, CIDRIP=ip)
                print response
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                    print 'Entry Already Exists'
                    continue
                else:
                    print e.response['Error']['Code']

def create_csg(csgName):
    client = boto3.client('redshift')
    try:
        response = client.describe_cluster_security_groups(ClusterSecurityGroupName=csgName)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ClusterSecurityGroupNotFound':
            print "Creating Security Group: " + csgName
            try:
                response = client.create_cluster_security_group(ClusterSecurityGroupName=csgName,Description=csgName,
                                                    Tags=[{'Key': 'Vendor',
                                                           'Value': 'mParticle'}
                                                         ]
                                                    )
            except botocore.exceptions.ClientError as e:
                 print e.response['Error']['Code']

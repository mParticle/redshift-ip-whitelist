import boto3, botocore, requests

def lambda_handler(event, context):
	# **** Set this Security Group in input json.  It must be dedicated to mParticle.
    destination_security_group_id = event['security_group_id'] 
	# **** Set the redshift port in input json
    redshift_port = event['redshift_port']
	# **** Indicate whether your redshift cluster is in VPC or not in input json.
    is_vpc = event['is_vpc']
    # **** set the aws region of the security group.
    aws_region = event['aws_region']

    r = requests.get('https://2g26abvcj4.execute-api.us-east-1.amazonaws.com/prod/redshift-ips')
    payload = r.json()

    trusted_ips = payload['trusted_ips']

    if (is_vpc):
        ec2 = boto3.resource('ec2', region_name = aws_region)
        security_group = ec2.SecurityGroup(destination_security_group_id)

        existing_ips = []
        try:
            for rule in security_group.ip_permissions:
                if rule['FromPort'] == redshift_port and rule['ToPort'] == redshift_port and rule['IpProtocol'] == 'tcp':
                    existing_ips.extend([x['CidrIp'] for x in rule['IpRanges']])
        except Exception as e:
            print 'Fail to get existing IPs and will proceed with an empty list. The error is ' + str(e)

        ips_to_delete = [x for x in existing_ips if x not in trusted_ips]
        for ip in ips_to_delete:
            try:
                response = security_group.revoke_ingress(IpProtocol='tcp', FromPort=redshift_port, ToPort=redshift_port, CidrIp=ip)
                print "Deleted IP " + str(ip) + " with response: " + str(response)
            except botocore.exceptions.ClientError as e:
                print e.response['Error']['Code']

        ips_to_add = [x for x in trusted_ips if x not in existing_ips]
        for ip in ips_to_add:
            try:
                response = security_group.authorize_ingress(IpProtocol='tcp',FromPort=redshift_port, ToPort=redshift_port, CidrIp=ip)
                print "Added IP " + str(ip) + " with response: " + str(response)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
                    print 'Entry Already Exists'
                else:
                    print e.response['Error']['Code']

    else:
        client = boto3.client('redshift')
        i = 0
        for ip in trusted_ips:
            i += 1
            csgName = 'mparticle-redshift-' + str(i//20 + 1)
            create_csg(csgName)
            try:
                response = client.authorize_cluster_security_group_ingress(ClusterSecurityGroupName=csgName, CIDRIP=ip)
                print "Added IP " + str(ip) + " with response: " + str(response)
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

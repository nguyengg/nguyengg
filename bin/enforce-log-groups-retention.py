#!/usr/bin/env python3

# A variant of https://robgodfrey.net/posts/2020/10/27/ensure-cw-logs-are-not-retained-forever/ that adds the ability
# to update log group retention for more than one AWS account. Can be run locally passing in a list of profiles
# (or reading from ~/.aws/credentials), or as an AWS Lambda handler.

import argparse
import boto3


def handler(event, *_):
    """
    Lambda handler to enforce log group retention for several AWS accounts.

    Input must be in format:

     .. code-block:: json
    {
        "role_arns": [
            "arn:aws:iam::1234:role/EnforceLogGroupRetention",
            "arn:aws:iam::2345:role/EnforceLogGroupRetention",
        ]
    }

    That role should trust the role that is executing the Lambda, and must allow these actions:

     .. code-block:: json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeRegions",
                    "logs:DescribeLogGroups",
                    "logs:PutRetentionPolicy"
                ],
                "Resource": "*"
            }
        ]
    }

    """
    # do first for my own AWS account, then do for other AWS accounts via role assumption
    # comment this out if you only ever need the Lambda to update log groups' retention for other AWS accounts.
    enforce_for_aws_account(None)
    for role_arn in event["role_arns"]:
        enforce_for_aws_account(role_arn)


def main():
    import os
    import pathlib

    parser = argparse.ArgumentParser(
        prog="enforce-log-groups-retention.py",
        description="Enforce that all log groups in all accessible regions have a retention policy. If not explicitly "
                    "given a list of AWS profiles, read from ~/.aws/credentials (can be overridden with environment "
                    "variable AWS_SHARED_CREDENTIALS_FILE) to retrieve that list instead.",
        epilog="Requires AWS CLI to be available in order to use the CodeCommit credential helper."
    )

    parser.add_argument('-d', '--retention-in-days', default=7, type=int,
                        help="The number of retention days to set, default to 7")
    parser.add_argument('--no-use-shared-credentials-file', action='store_true', dest='no_use_shared_credentials_file',
                        help="""If specified, will not load the default shared AWS credentials file even if no profiles
                         are provided. Useful when credentials are provided via environment variables.""")
    parser.add_argument('profiles', nargs='*', metavar="profile",
                        help="The profiles to create the AWS CloudWatch Logs client. If none are given, will read from "
                             "the shared credential file to populate the list of profiles")
    args = parser.parse_args()
    profiles = args.profiles
    if len(profiles) == 0:
        if args.no_use_shared_credentials_file:
            profiles=[None]
        else:
            with open(os.getenv("AWS_SHARED_CREDENTIALS_FILE", os.path.join(pathlib.Path.home(), ".aws/credentials")),
                      'r') as file:
                while line := file.readline():
                    line = line.rstrip()
                    if line.startswith('[') and line.endswith(']'):
                        profiles.append(line[1:-1])
    profiles = list(dict.fromkeys(profiles, None).keys())

    for profile in profiles:
        session = boto3.Session(profile_name=profile)
        regions = all_regions(session.client('ec2'))
        logs_clients = [(session.client('logs', region_name=region_name), region_name) for region_name in regions]

        for (logs_client, region_name) in logs_clients:
            update_retention_period_for_never_expiring_log_groups(logs_client, region_name, profile,
                                                                  retention_in_days=args.retention_in_days)


def enforce_for_aws_account(role_arn):
    if not role_arn:
        regions = all_regions(boto3.client('ec2'))
        logs_clients = [(boto3.client("logs", region_name=region_name), region_name) for region_name in regions]
    else:
        sts_client = boto3.client('sts')
        response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="EnforceLogGroupsRetention")
        credentials = response['Credentials']
        regions = all_regions(boto3.client('ec2',
                                           aws_access_key_id=credentials['AccessKeyId'],
                                           aws_secret_access_key=credentials['SecretAccessKey'],
                                           aws_session_token=credentials['SessionToken']))
        logs_clients = [
            (boto3.client('logs',
                          region_name=region_name,
                          aws_access_key_id=credentials['AccessKeyId'],
                          aws_secret_access_key=credentials['SecretAccessKey'],
                          aws_session_token=credentials['SessionToken']),
             region_name) for region_name in regions]

    for (logs_client, region_name) in logs_clients:
        update_retention_period_for_never_expiring_log_groups(logs_client, region_name, role_arn)


def update_retention_period_for_never_expiring_log_groups(logs_client, region_name, prefix="own", retention_in_days=7):
    print(f"[{prefix}] [{region_name}] processing log groups")

    for log_group in all_log_groups(logs_client):
        if "retentionInDays" not in log_group:
            update_log_group_retention_setting(logs_client, log_group["logGroupName"], region_name, prefix,
                                               retention_in_days)

    print(f"[{prefix}] [{region_name}] processed all log groups")


def update_log_group_retention_setting(logs_client, log_group_name, region_name, prefix, retention_in_days):
    logs_client.put_retention_policy(logGroupName=log_group_name, retentionInDays=retention_in_days)
    print(f"[{prefix}] [{region_name}] {log_group_name} => {retention_in_days} days")


def all_regions(ec2_client):
    response = ec2_client.describe_regions()
    return [region["RegionName"] for region in response["Regions"]]


def all_log_groups(logs_client):
    log_groups = []
    paginator = logs_client.get_paginator("describe_log_groups")

    for page in paginator.paginate():
        log_groups.extend(page["logGroups"])

    return log_groups


if __name__ == "__main__":
    main()

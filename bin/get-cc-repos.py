#!/usr/bin/env python3

import argparse
import boto3
import os
import pathlib
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="get-cc-repos.py",
        description="Check out all available CodeCommit repos. If not explicitly given a list of AWS profiles, read "
                    "from ~/.aws/credentials (can be overridden with environment variable AWS_SHARED_CREDENTIALS_FILE) "
                    "to retrieve that list instead.",
        epilog="Requires AWS CLI to be available in order to use the CodeCommit credential helper."
    )

    parser.add_argument('profiles', nargs='*', metavar="profile",
                        help="The profiles to checkout CodeCommit repos. If none are given, will read from the shared "
                             "credential file to populate the list of profiles")
    args = parser.parse_args()
    profiles = args.profiles
    if len(profiles) == 0:
        with open(os.getenv("AWS_SHARED_CREDENTIALS_FILE", os.path.join(pathlib.Path.home(), ".aws/credentials")),
                  'r') as file:
            while line := file.readline():
                line = line.rstrip()
                if line.startswith('[') and line.endswith(']'):
                    profiles.append(line[1:-1])
    profiles = list(dict.fromkeys(profiles, None).keys())

    # save the global credential helper in order to revert this setting upon completion.
    previous = subprocess.check_output(
        ['git', 'config', '--global', '--get', '--default', '', 'credential.helper']).decode('utf-8').rstrip()

    try:
        for profile in profiles:
            client = boto3.Session(profile_name=profile).client('codecommit')
            repos = [repo.get('repositoryName') for repo in client.list_repositories().get('repositories')]
            if len(repos) == 0:
                print(f"{profile} has no repos")
                continue

            # set global credential helper to the profile.
            subprocess.run(['git', 'config', '--global', 'credential.helper',
                            f"!aws codecommit --profile {profile} credential-helper $@"])

            for repo in repos:
                p = os.path.join(".", profile, repo)
                if os.path.exists(p):
                    print(f"{repo} already exists at {p}")
                    continue

                print(f"{profile}/{repo}")
                url = client.get_repository(repositoryName=repo).get('repositoryMetadata').get('cloneUrlHttp')
                print(subprocess.check_output(['git', 'clone', url, p]).decode('utf-8').rstrip())
                subprocess.run(['git', '-C', p, 'config', '--local', 'credential.UseHttpPath', 'true'])
                subprocess.run(['git', '-C', p, 'config', '--local', 'credential.helper',
                                f"!aws codecommit --profile {profile} credential-helper $@"])

    finally:
        if not previous:
            subprocess.run(['git', 'config', '--global', '--unset', 'credential.helper'])
        else:
            subprocess.run(['git', 'config', '--global', 'credential.helper', previous])

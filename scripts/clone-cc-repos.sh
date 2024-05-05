#!/bin/bash

# List all CodeCommit repos and check them out using CodeCommit Git Credentials helper.
# Should be run with ./clone-cc-repos.sh profile1 profile2 ...

PREVIOUS=$(git config --global credential.helper)

for profile in "$@"
do
  echo "$profile"
  git config --global credential.helper "!aws codecommit --profile $profile credential-helper \$@"
  for repo in $(aws codecommit list-repositories --profile "$profile" --query 'repositories[*].[repositoryName]' --output text --no-cli-pager)
  do
    url=$(aws codecommit get-repository --profile "$profile" --repository-name --query 'repositoryMetadata.cloneUrlHttp' $repo --output text --no-cli-pager)
    git clone "$url" "$profile"/"$repo"
    git -C "$profile"/"$repo" config --local credential.UseHttpPath true
    git -C "$profile"/"$repo" config --local credential.helper "!aws codecommit --profile $profile credential-helper \$@"
  done
done

if [[ -z "${PREVIOUS}" ]]; then
  git config --global --unset credential.helper
else
  git config --global credential.helper "${PREVIOUS}"
fi

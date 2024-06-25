# Development

To be able to push changes, you need a GitHub Personal Access Token.
```shell
GITHUB_PAT=github_pat_123; git remote set-url origin $(git config --get remote.origin.url | perl -F'github.com' -sanE 'print "https://${token}\@github.com$F[1]"' -- -token=$GITHUB_PAT;)
```

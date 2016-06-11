# github-backup
A simple script to backup all your repositories


## Authentication

### Github API

This script needs to be authenticated to your github account. Firstly, you need to create an access token by following this url : [GitHub - Creating an access token](https://help.github.com/articles/creating-an-access-token-for-command-line-use/)

Then, you have to fill these environment variables:
 * GITHUB_LOGIN
 * GITHUB_PAT

Example:
```bash
export GITHUB_LOGIN="steven-martins"
export GITHUB_PAT="your_personnal_token"
```

### Setup SSH key

Currently, only ssh authentication is supported. You need to setup a ssh key on your github account to use this script.
You can follow this guide : [GitHub - Generating an ssh key](https://help.github.com/articles/generating-an-ssh-key/)


## Launch

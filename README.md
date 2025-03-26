# ReplicatorForGithubProject

This is a simple script that permit you to replicate your tickets on JIRA to your Github project.

## Table of contents
- [Prerequisites](#prerequisites)
- [How to use it](#how-to-use-it)
- [Useful command](#useful-command)
- [.env config](#env-file)

## Prerequisites

- Python 3.6+

## How to use it

TODO

## Useful command

The following command permit you to get the id of a project on Github.

```bash
curl -H "Authorization: bearer YOUR_GITHUB_TOKEN" \
     -X POST \
     -d '{"query": "query { user(login: \"YOUR_GITHUB_USERNAME\") { projectV2(number: NUMBER_OF_YOUR_PROJECT) { id } } }"}' \
     https://api.github.com/graphql | python -c "import sys, json; print(json.load(sys.stdin)['data']['user']['projectV2']['id'])"
```

You need to replace `YOUR_GITHUB_TOKEN` by your Github token that can be generated [here](https://github.com/settings/tokens), with the `repo`, `user` and `project` scopes.

You also need to replace `YOUR_GITHUB_USERNAME` by your Github username.

Finally, you need to replace `NUMBER_OF_YOUR_PROJECT` by the number of the project you want to get the id. For that you need to go on the `https://github.com/users/YOUR_GITHUB_USERNAME/projects/`, page and click on the project board you want to get the id, and at the end of url you will see the number of the project.


## .env file

You need to create a `.env` file at the root of the project with the following content:

```env
# Jira credentials and URL
JIRA_BASE_URL = "YOUR_JIRA_PROJECT_URL"
JIRA_API_ENDPOINT = "YOUR_JIRA_PROJECT_API_ENDPOINT_URL"
JIRA_USER = "YOUR_JIRA_USER_EMAIL"
JIRA_PROJECT_NAME = "YOUR_JIRA_PROJECT_NAME"
JIRA_API_TOKEN = "YOUR_JIRA_API_TOKEN"
JIRA_BOARD_ID = 1 # must be an integer

# GitHub credentials and URL
GITHUB_API_ENDPOINT = "https://api.github.com"
GITHUB_REPO = "YOUR_GITHUB_USERNAME/YOUR_GITHUB_REPO" # You need both of them
GITHUB_TOKEN = "YOUR_GITHUB_API_TOKEN"
GITHUB_PROJECT_ID = "YOUR_GITHUB_PROJECT_ID"
GITHUB_PROJECT_OWNER = "NAME_OF_THE_OWNER_OF_THE_PROJECT"
GITHUB_PROJECT_NAME = "NAME_OF_THE_REPO_THAT_CONTAINS_THE_PROJECT"
GITHUB_PROJECT_NUMBER = 9 # must be an integer

# Github usernames for the assignees
GITHUB_USERNAMES = [{"JIRA_USERNAME": "GITHUB_USERNAME"}, {"JIRA_USERNAME": "GITHUB_USERNAME"}]
```

`YOUR_JIRA_BASE_URL` at this URL: `https://YOUR_JIRA_PROJECT_NAME.atlassian.net/`.

`YOUR_JIRA_API_ENDPOINT` at this URL: `https://YOUR_JIRA_PROJECT_NAME.atlassian.net/rest/api/2/search` .

`YOUR_JIRA_USER` is your JIRA user email that you can find [here](https://id.atlassian.com/manage-profile/profile-and-visibility).

`YOUR_JIRA_PROJECT_NAME` is your JIRA project name as the name say it.

`YOUR_JIRA_API_TOKEN` is your JIRA API token that you can generate [here](https://id.atlassian.com/manage-profile/security/api-tokens), by clicking on the `Create API token` button. (the maximum duration of 1 year is advised)

`YOUR_JIRA_BOARD_ID` is the JIRA board id that you can get by looking at the number in the url of your project, it will be something like : https://my_project.atlassian.net/jira/software/projects/SCRUM/boards/**1**/backlog . And you need to take the number after /boards/ .

`GITHUB_API_ENDPOINT` is `https://api.github.com`

`YOUR_GITHUB_USERNAME/YOUR_GITHUB_REPO` are respectively your Github username and the name of the repository that is linked to your github project.

for the `GITHUB_TOKEN` and `GITHUB_PROJECT_ID` you can use what's [above](#useful-command).

`NAME_OF_THE_OWNER_OF_THE_PROJECT` is the github name of the person that owns the project board.

`NAME_OF_THE_REPO_THAT_CONTAINS_THE_PROJECT` is the name of the repo linked to the project board.

`GITHUB_PROJECT_NUMBER` is the Github board id that you can get by looking at the number in the url of your project, it will be something like : https://github.com/users/my_github_username/projects/**9**/views/1 . And you need to take the number after /projects/ .

`GITHUB_USERNAMES` is a list of object that permit to do the link between your JIRA user and your Github username to assign someone to the task (in the example there is only two object but you need as much object as you have of member in your team).
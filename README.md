# ReplicatorForGithubProject

This is a simple script that permit you to replicate your tickets on JIRA to your Github project.

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
JIRA_API_TOKEN = "YOUR_JIRA_API_TOKEN"

# GitHub credentials and URL
GITHUB_API_ENDPOINT = "https://api.github.com"
GITHUB_REPO = "YOUR_GITHUB_USERNAME/YOUR_GITHUB_REPO" # You need both of them
GITHUB_TOKEN = "YOUR_GITHUB_API_TOKEN"
GITHUB_PROJECT_ID = "YOUR_GITHUB_PROJECT_ID"
```

`YOUR_JIRA_BASE_URL` at this URL: `https://YOUR_JIRA_PROJECT_NAME.atlassian.net/`.

`YOUR_JIRA_API_ENDPOINT` at this URL: `https://YOUR_JIRA_PROJECT_NAME.atlassian.net/rest/api/2/search`

`YOUR_JIRA_USER` is your JIRA user email that you can find [here](https://id.atlassian.com/manage-profile/profile-and-visibility).

`YOUR_JIRA_API_TOKEN` is your JIRA API token that you can generate [here](https://id.atlassian.com/manage-profile/security/api-tokens), by clicking on the `Create API token` button. (the maximum duration of 1 year is advised)

`GITHUB_API_ENDPOINT` is `https://api.github.com`

`YOUR_GITHUB_USERNAME/YOUR_GITHUB_REPO` are respectively your Github username and the name of the repository that is linked to your github project.

for the `GITHUB_TOKEN` and `GITHUB_PROJECT_ID` you can use what's [above](#useful-command).




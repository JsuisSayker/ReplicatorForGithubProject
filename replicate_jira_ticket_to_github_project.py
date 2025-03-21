import requests
import os
import json
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

JIRA_API_ENDPOINT = os.getenv("JIRA_API_ENDPOINT")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_NAME = os.getenv("JIRA_PROJECT_NAME")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")

GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# GitHub Project ID for Projects v2 (GraphQL ID)
GITHUB_PROJECT_ID = os.getenv("GITHUB_PROJECT_ID")
GITHUB_REPO_ID = os.getenv("GITHUB_REPO_ID")
GITHUB_USERNAMES = os.getenv("GITHUB_USERNAMES")
GITHUB_PROJECT_OWNER = os.getenv("GITHUB_PROJECT_OWNER")
GITHUB_PROJECT_NAME = os.getenv("GITHUB_PROJECT_NAME")


def fetch_jira_issues(jql_query=f"project={JIRA_PROJECT_NAME}"):
    headers = {"Accept": "application/json"}
    params = {"jql": jql_query, "maxResults": 100}
    response = requests.get(
        JIRA_API_ENDPOINT,
        headers=headers,
        params=params,
        auth=HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN),
    )
    response.raise_for_status()
    return response.json()["issues"]


def create_repository_issue(title, body):
    """
    Creates an issue in the repository using GraphQL and returns its node ID.
    """
    query = """
    mutation CreateIssue($input: CreateIssueInput!) {
      createIssue(input: $input) {
        issue {
          id
          number
          url
        }
      }
    }
    """
    variables = {
        "input": {
            "repositoryId": GITHUB_REPO_ID,
            "title": title,
            "body": body
        }
    }
    result = run_graphql(query, variables)
    issue = result["data"]["createIssue"]["issue"]
    return issue["id"], issue["number"]


def add_issue_to_project(issue_node_id):
    """
    Adds an existing repository issue (by its node ID) to a GitHub Projects v2 board.
    """
    query = """
    mutation AddIssueToProject($input: AddProjectV2ItemByIdInput!) {
      addProjectV2ItemById(input: $input) {
        item {
          id
        }
      }
    }
    """
    variables = {
        "input": {
            "projectId": GITHUB_PROJECT_ID,
            "contentId": issue_node_id
        }
    }
    result = run_graphql(query, variables)
    return result["data"]["addProjectV2ItemById"]["item"]["id"]


def create_issue_on_board(title, body):
    issue_node_id, issue_number = create_repository_issue(title, body)
    project_item_id = add_issue_to_project(issue_node_id)
    return project_item_id, issue_number


def get_project_details():
    url = "https://api.github.com/graphql"

    headers = {
        "Authorization": f"bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    query = f"""
    query {{
      user(login: "{GITHUB_PROJECT_OWNER}") {{
        projectV2(number: 9) {{
          id
          title
          fields(first: 100) {{
            nodes {{
              ... on ProjectV2Field {{
                id
                name
                dataType
              }}
              ... on ProjectV2IterationField {{
                id
                name
                configuration {{
                  iterations {{
                    id
                    title
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """

    payload = {"query": query}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def run_graphql(query, variables):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.starfox-preview+json"
    }
    response = requests.post(url, json={
        "query": query, "variables": variables}, headers=headers)
    print(response.json())
    response.raise_for_status()
    return response.json()


def add_assignees_to_issue(assignable_id, assignee_ids):
    """
    Adds assignees to a GitHub issue using the GraphQL API.

    Parameters:
      assignable_id (str): The global node ID of the issue.
      assignee_ids (list): A list of global node IDs for the users to be assigned.
      token (str): Your GitHub personal access token.

    Returns:
      dict: The JSON response from the GraphQL API.
    """
    url = "https://api.github.com/graphql"
    query = """
    mutation AddAssignees($input: AddAssigneesToAssignableInput!) {
      addAssigneesToAssignable(input: $input) {
        assignable {
          ... on Issue {
            id
            title
            assignees(first: 10) {
              nodes {
                id
                login
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "input": {
            "assignableId": assignable_id,
            "assigneeIds": assignee_ids
        }
    }
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.starfox-preview+json"
    }
    response = requests.post(url, headers=headers, json={
        "query": query, "variables": variables})
    response.raise_for_status()
    return response.json()


def update_infos(issue_node_id, side_infos_dict, items_id, user_id, issue_id):
    for field_name in items_id["data"]["user"]["projectV2"]["fields"]["nodes"]:
        # Verifies if the field name is not empty (jsust that {})
        if field_name:
            if field_name["name"] in side_infos_dict:
                if field_name["name"] != "Sprint":
                    print(field_name["dataType"])
                    sent_value = side_infos_dict[field_name["name"]]
                    key = field_name["dataType"].lower()
                    if field_name["dataType"] == "ASSIGNEES":
                        add_assignees_to_issue(issue_id, [user_id])
                    else:
                        query = """
                        mutation UpdateField($input: UpdateProjectV2ItemFieldValueInput!) {
                        updateProjectV2ItemFieldValue(input: $input) {
                            projectV2Item {
                            id
                            }
                        }
                        }
                        """
                        variables = {
                            "input": {
                                "projectId": GITHUB_PROJECT_ID,
                                "itemId": issue_node_id,
                                "fieldId": field_name["id"],
                                "value": {key: sent_value},
                            }
                        }
                        run_graphql(query, variables)


def get_user_node_id(username):
    url = "https://api.github.com/graphql"
    query = """
    query GetUserId($login: String!) {
      user(login: $login) {
        id
      }
    }
    """
    variables = {"login": username}
    headers = {
        "Authorization": f"bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={
        "query": query, "variables": variables}, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["data"]["user"]["id"]


def get_github_issue(issue_number):
    url = f"https://api.github.com/repos/{GITHUB_PROJECT_OWNER}/{GITHUB_PROJECT_NAME}/issues/{issue_number}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch issue: {response.status_code}, {response.text}")


def replicate_jira_to_github():
    issues = fetch_jira_issues()
    for issue in issues:
        fields = issue.get("fields", {})

        # Basic fields
        column = fields.get("status", {}).get("name", "Not set")
        title = fields.get("summary", "No summary provided")
        description = fields.get("description", "No description provided")
        jira_url = f"{JIRA_BASE_URL}/browse/{issue['key']}"

        start_date = fields.get("customfield_10015", "Not set")
        due_date = fields.get("duedate", "Not set")
        story_points = fields.get("customfield_10016", "Not set")
        sprint = fields.get("customfield_10020", "Not set")
        if isinstance(sprint, list):
            sprint = ", ".join([s["name"] for s in sprint])
        print(sprint)
        assignee = fields.get("assignee", {})
        assignee_name = assignee.get("displayName", "Unassigned")
        labels = fields.get("labels", [])
        labels_str = ", ".join(labels) if labels else "None"
        priority = fields.get("priority", {}).get("name", "Not set")

        parent = fields.get("parent")
        parent_info = parent.get("key") if parent else "No parent"

        mapped_username = json.loads(GITHUB_USERNAMES)
        for user in mapped_username:
            if user.get(assignee_name) is not None:
                for key, value in user.items():
                    assignee_name = value
        user_id = get_user_node_id(assignee_name)

        side_infos_dict = {
            "Start Date": start_date,
            "End Date": due_date,
            "Story point": story_points,
            "Sprint": sprint,
            "Assignees": assignee_name,
            "Labels": labels_str,
        }

        # Build the GitHub issue body
        body = (
            f"**Jira Ticket:** [{issue['key']}]({jira_url})\n\n"
            f"**Column:** {column}\n\n"
            f"**Title:** {title}\n\n"
            f"**Description:**\n{description}\n\n"
            f"**Story Points:** {story_points}\n\n"
            f"**Sprint:** {sprint}\n\n"
            f"**Assignee:** {assignee_name}\n\n"
            f"**Labels:** {labels_str}\n\n"
            f"**Priority:** {priority}\n\n"
            f"**Start Date:** {start_date}\n\n"
            f"**Due Date:** {due_date}\n\n"
            f"**Parent Ticket:** {parent_info}\n"
        )

        # Create the GitHub issue

        issue_node_id, issue_number = create_issue_on_board(title, body)
        issue_id = get_github_issue(issue_number)["node_id"]

        items_id = get_project_details()
        # print(items_id)

        update_infos(issue_node_id,
                     side_infos_dict, items_id, user_id, issue_id)


if __name__ == "__main__":
    replicate_jira_to_github()

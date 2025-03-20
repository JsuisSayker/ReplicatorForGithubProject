import requests
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

JIRA_API_ENDPOINT = os.getenv("JIRA_API_ENDPOINT")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")

GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# GitHub Project ID for Projects v2 (GraphQL ID)
GITHUB_PROJECT_ID = os.getenv("GITHUB_PROJECT_ID")


def fetch_jira_issues(jql_query="project=Pikselite"):
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


def create_github_issue(title, body):
    url = f"{GITHUB_API_ENDPOINT}/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    data = {"title": title, "body": body}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def add_issue_to_project(project_id, issue_node_id):
    """
    Uses GitHub GraphQL API to add an issue (by its node_id) to a GitHub Project v2 board.
    """
    url = "https://api.github.com/graphql"
    query = """
    mutation AddIssueToProject($input: AddProjectV2ItemByIdInput!) {
      addProjectV2ItemById(input: $input) {
        item {
          id
        }
      }
    }
    """
    variables = {"input": {"projectId": project_id, "contentId": issue_node_id}
                 }
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.starfox-preview+json",
    }
    response = requests.post(
        url, json={"query": query, "variables": variables}, headers=headers
    )
    response.raise_for_status()
    return response.json()


def replicate_jira_to_github():
    issues = fetch_jira_issues()
    for issue in issues:
        fields = issue.get("fields", {})

        # Basic fields
        title = fields.get("summary", "No summary provided")
        description = fields.get("description", "No description provided")
        jira_url = f"{JIRA_BASE_URL}/browse/{issue['key']}"

        story_points = fields.get("customfield_10016", "Not set")
        sprint = fields.get("customfield_10007", "Not set")
        if isinstance(sprint, list):
            sprint = ", ".join(sprint)
        assignee = fields.get("assignee", {})
        assignee_name = assignee.get("displayName", "Unassigned")
        labels = fields.get("labels", [])
        labels_str = ", ".join(labels) if labels else "None"
        priority = fields.get("priority", {}).get("name", "Not set")
        start_date = fields.get("startDate", "Not set")
        due_date = fields.get("duedate", "Not set")
        parent = fields.get("parent")
        parent_info = parent.get("key") if parent else "No parent"

        # Build the GitHub issue body
        body = (
            f"**Jira Ticket:** [{issue['key']}]({jira_url})\n\n"
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
        github_issue = create_github_issue(title, body)
        print(f"Created GitHub Issue #{github_issue['number']} for Jira {issue['key']}")

        # Add the newly created issue to the specified GitHub Project board
        # Ensure that the created issue's JSON contains the 'node_id' field
        issue_node_id = github_issue.get("node_id")
        if issue_node_id and GITHUB_PROJECT_ID:
            add_issue_to_project(GITHUB_PROJECT_ID, issue_node_id)
            print(
                f"Added issue {github_issue['number']} to GitHub Project {GITHUB_PROJECT_ID}"
            )
        else:
            print(
                "Missing GitHub issue node_id or project ID; cannot add to project board."
            )


if __name__ == "__main__":
    replicate_jira_to_github()

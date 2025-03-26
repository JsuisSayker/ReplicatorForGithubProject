#!/usr/bin/env python3

import requests
import os
import json
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from jira import JIRA

# Load environment variables from .env file
load_dotenv()

JIRA_API_ENDPOINT = os.getenv("JIRA_API_ENDPOINT")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_NAME = os.getenv("JIRA_PROJECT_NAME")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_BOARD_ID = os.getenv("JIRA_BOARD_ID")

GITHUB_API_ENDPOINT = os.getenv("GITHUB_API_ENDPOINT")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# GitHub Project ID for Projects v2 (GraphQL ID)
GITHUB_PROJECT_ID = os.getenv("GITHUB_PROJECT_ID")
GITHUB_USERNAMES = os.getenv("GITHUB_USERNAMES")
GITHUB_PROJECT_OWNER = os.getenv("GITHUB_PROJECT_OWNER")
GITHUB_PROJECT_NAME = os.getenv("GITHUB_PROJECT_NAME")
GITHUB_PROJECT_NUMBER = os.getenv("GITHUB_PROJECT_NUMBER")


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
    issues = response.json()["issues"]

    sprints = []
    start_at = 0
    max_results = 50  # Jira default page size for sprints

    jira_instance = JIRA(server=JIRA_BASE_URL, basic_auth=(JIRA_USER, JIRA_API_TOKEN))

    board_id = int(JIRA_BOARD_ID)
    sprints_page = jira_instance.sprints(
        board_id, startAt=start_at, maxResults=max_results, state="active,closed,future"
    )
    while True:
        # Retrieve a page of sprints

        if not sprints_page:
            break
        for sprint in sprints_page:
            detail = {
                "id": sprint.id,
                "name": sprint.name,
                "goal": getattr(sprint, "goal", None),
                "startDate": getattr(sprint, "startDate", None),
                "endDate": getattr(sprint, "endDate", None),
                "state": getattr(sprint, "state", None)
            }
            sprints.append(detail)

        if len(sprints_page) < max_results:
            break
        start_at += max_results

    return {"issues": issues, "sprints": sprints}


def create_repository_issue(title, body, repo_id):

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
            "repositoryId": repo_id,
            "title": title,
            "body": body
        }
    }
    result = run_graphql(query, variables)
    issue = result["data"]["createIssue"]["issue"]
    return issue["id"], issue["number"]


def add_issue_to_project(issue_node_id):

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


def get_repository_id(owner, repository):

    url = "https://api.github.com/graphql"
    query = """
    query {
      repository(owner: "%s", name: "%s") {
        id
      }
    }
    """ % (owner, repository)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"query": query}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["data"]["repository"]["id"]


def create_issue_on_board(title, body):
    repo_id = get_repository_id(GITHUB_PROJECT_OWNER, GITHUB_PROJECT_NAME)
    issue_node_id, issue_number = create_repository_issue(title, body, repo_id)
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
        projectV2(number: {GITHUB_PROJECT_NUMBER}) {{
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
              ... on ProjectV2SingleSelectField {{
                id
                name
                dataType
                options {{
                  id
                  name
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
    response.raise_for_status()
    return response.json()


def add_assignees_to_issue(assignable_id, assignee_ids):

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


def label_exists(label_name):

    url = f"https://api.github.com/repos/{GITHUB_PROJECT_OWNER}/{GITHUB_PROJECT_NAME}/labels/{label_name}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def create_label(label_name, color, description):

    url = f"https://api.github.com/repos/{GITHUB_PROJECT_OWNER}/{GITHUB_PROJECT_NAME}/labels"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
    }
    data = {
        "name": label_name,
        "color": color,
        "description": description
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def create_label_if_not_exists(labels_name):

    for label in labels_name:
        if label_exists(label):
            print(f"Label '{label}' already exists.")
        else:
            print(f"Label '{label}' not found. Creating it...")
            color = input(f"Enter the color for the label in the following format (#eb0dbc) '{label}': ")
            description = input(f"Enter the description for the label '{label}': ")
            create_label(label, color, description)


def add_labels_to_issue(issue_number, labels):
    url = f"https://api.github.com/repos/{GITHUB_PROJECT_OWNER}/{GITHUB_PROJECT_NAME}/issues/{issue_number}/labels"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.post(url, headers=headers, json=labels)
    response.raise_for_status()
    return response.json()


def assign_iteration_to_issue(issue_node_id, field_name, side_infos_dict):

    query = """
    mutation UpdateIterationField($input: UpdateProjectV2ItemFieldValueInput!) {
      updateProjectV2ItemFieldValue(input: $input) {
        projectV2Item {
          id
        }
      }
    }
    """
    iteration_option_id = ""
    field_id = field_name["id"]
    for current_iteration in field_name["configuration"]["iterations"]:
        if iteration_option_id != "":
            break
        for active_iteration in side_infos_dict["Sprint"]:
            if iteration_option_id != "":
                break
            if (current_iteration["title"] == active_iteration["name"]) and active_iteration["state"] == "active":
                iteration_option_id = current_iteration["id"]

    variables = {
        "input": {
            "projectId": GITHUB_PROJECT_ID,
            "itemId": issue_node_id,
            "fieldId": field_id,
            "value": {"iterationId": iteration_option_id}
        }
    }
    run_graphql(query, variables)


def update_status_field(issue_node_id, field_name, actual_status):

    query = """
    mutation UpdateStatusField($input: UpdateProjectV2ItemFieldValueInput!) {
      updateProjectV2ItemFieldValue(input: $input) {
        projectV2Item {
          id
        }
      }
    }
    """
    field_id = field_name["id"]
    comparative_status = actual_status.replace(" ", "").lower()

    for current_status in field_name["options"]:
        if (current_status["name"].replace(" ", "").lower()) == comparative_status:
            option_node_id = current_status["id"]
            break

    variables = {
        "input": {
            "projectId": GITHUB_PROJECT_ID,
            "itemId": issue_node_id,
            "fieldId": field_id,
            "value": {"singleSelectOptionId": option_node_id}
        }
    }
    run_graphql(query, variables)


def update_infos(issue_node_id, side_infos_dict, items_id, user_id, issue_id, issue_number, created_sprint):
    sprint_found = False
    for field_name in items_id["data"]["user"]["projectV2"]["fields"]["nodes"]:
        if field_name:
            if field_name["name"] in side_infos_dict:
                sent_value = side_infos_dict[field_name["name"]]
                if field_name["name"] == "Sprint":
                    assign_iteration_to_issue(issue_node_id, field_name, side_infos_dict)
                    sprint_found = True
                    continue
                key = field_name["dataType"].lower()
                if field_name["dataType"] == "LABELS":
                    add_labels_to_issue(issue_number, [sent_value])
                    continue
                if field_name["dataType"] == "SINGLE_SELECT":
                    update_status_field(issue_node_id, field_name, side_infos_dict["Status"])
                    continue
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
    if sprint_found is False:
        assign_iteration_to_issue(issue_node_id, created_sprint, side_infos_dict)


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


def sprint_found_in_github(items_id):
    for item in items_id["data"]["user"]["projectV2"]["fields"]["nodes"]:
        if item:
            if item["name"] == "Sprint":
                return True
    return False


def sprint_field_is_already_existing(items_id, sprints, creation_date):
    final_dict = {}

    sprint_found = sprint_found_in_github(items_id)
    if not sprint_found:
        for sprint in sprints:
            start_date = sprint["startDate"]
            end_date = sprint["endDate"]
            complete_start_date = start_date.split("T")[0]

            if final_dict == {}:
                final_dict = {creation_date: {"iterations": []}}
                day_start_date = start_date.split("-")[2].split("T")[0]
                day_end_date = end_date.split("-")[2].split("T")[0]
                day_difference = int(day_end_date) - int(day_start_date)

            object_to_insert = {
                "title": sprint["name"],
                "startDate": complete_start_date,
                "duration": day_difference
                }

            final_dict[creation_date]["iterations"].append(object_to_insert)
        return False, final_dict
    return True, final_dict


def create_iteration_field(fields_name, creation_date):

    mutation = """
    mutation CreateIterationField($input: CreateProjectV2FieldInput!) {
      createProjectV2Field(input: $input) {
        projectV2Field {
          ... on ProjectV2IterationField {
            id
            name
            dataType
            configuration {
              iterations {
                id
                title
                startDate
                duration
              }
            }
          }
        }
      }
    }
    """
    iteration_config = {
        "startDate": creation_date,
        "duration": fields_name[creation_date]["iterations"][0]["duration"],
        "iterations": fields_name[creation_date]["iterations"]

    }
    variables = {
        "input": {
            "projectId": GITHUB_PROJECT_ID,
            "name": "Sprint",
            "dataType": "ITERATION",
            "iterationConfiguration": iteration_config
        }
    }
    result = run_graphql(mutation, variables)
    created_field = result["data"]["createProjectV2Field"]["projectV2Field"]
    return created_field


def replicate_jira_to_github():
    fetched_values = fetch_jira_issues()

    for issue in fetched_values["issues"]:
        fields = issue.get("fields", {})

        # Basic fields
        column = fields.get("status", {}).get("name", "Not set")
        title = fields.get("summary", "No summary provided")
        description = fields.get("description", "No description provided")
        # jira_url = f"{JIRA_BASE_URL}/browse/{issue['key']}"

        start_date = fields.get("customfield_10015", "Not set")
        due_date = fields.get("duedate", "Not set")
        story_points = fields.get("customfield_10016", "Not set")
        creation_date = fields.get("created", "Not Set").split("T")[0]
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
            "Sprint": fetched_values["sprints"],
            "Assignees": assignee_name,
            "Status": column,
            "Labels": labels_str,
        }

        # Build the GitHub issue body
        body = (
            f"{description}\n\n"
        )

        # Create label if it doesn't exist
        create_label_if_not_exists(labels)

        # Create the GitHub issue
        issue_node_id, issue_number = create_issue_on_board(title, body)
        issue_id = get_github_issue(issue_number)["node_id"]

        items_id = get_project_details()
        # print(items_id)

        existing_sprint, fields_name = sprint_field_is_already_existing(
            items_id, fetched_values["sprints"], creation_date)
        created_sprint = {}
        if existing_sprint is False:
            created_sprint = create_iteration_field(fields_name, creation_date)

        update_infos(issue_node_id,
                     side_infos_dict, items_id,
                     user_id, issue_id, issue_number, created_sprint)


if __name__ == "__main__":
    replicate_jira_to_github()

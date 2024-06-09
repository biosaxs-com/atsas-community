#
# This is heavily based on:
#   https://gist.github.com/ruanbekker/946dac18fca09c25a5c09bcc63c70c92
#

import json, requests

personal_access_token = "fill-in-your-own" 

repository_owner = "biosaxs-com"
repository_name = "atsas-community"



def get_repository_id(token = personal_access_token, owner = repository_owner, name = repository_name):
    """
    Get the GitHub repository ID using the GraphQL API.
    Parameters:
    - token (str): Personal Access Token (PAT).
    - owner (str): Owner of the repository.
    - name (str): Name of the repository.
    """
    url = "https://api.github.com/graphql"
    query = """
    query($name: String!, $owner: String!) {
      repository(name: $name, owner: $owner) {
        id
      }
    }
    """
    variables = {"name": name, "owner": owner}
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['repository']['id']
    else:
        print(f"Error fetching repository ID. Status code: {response.status_code}, Response: {response.text}")
        return None


def get_discussion_categories(token = personal_access_token, owner = repository_owner, name = repository_name):
    """
    Fetch discussion categories for a repository using the GraphQL API.
    Parameters:
    - token (str): Personal Access Token (PAT) with permissions to access the repository.
    - repo_owner (str): Owner of the repository (username or organization).
    - repo_name (str): Name of the repository.
    """
    url = "https://api.github.com/graphql"
    query = """
    query RepositoryDiscussionCategories($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        discussionCategories(first: 100) {
          nodes {
            id
            name
          }
        }
      }
    }
    """
    variables = {"owner": owner, "name": name}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps({"query": query, "variables": variables}))
    if response.status_code == 200:
        categories = {}
        for category in response.json()['data']['repository']['discussionCategories']['nodes']:
            categories[category['name']] = category['id']
        return categories

    else:
        print(f"Failed to fetch discussion categories. Status code: {response.status_code}, Response: {response.text}")
        return None


def create_discussion(repository_id, category_id, title, body, token = personal_access_token):
    """
    Create a discussion in a GitHub repository using the GraphQL API.
    Parameters:
    - repository_id (str): The ID of the repository.
    - category_id (str): The ID of the discussion category.
    - title (str): Title of the discussion.
    - body (str): Body content of the discussion.
    - token (str): Personal Access Token (PAT) with permissions to access the repository.
    """
    
    # GraphQL endpoint
    url = "https://api.github.com/graphql"

    # GraphQL query. Note: This is a mutation, not a query.
    query = """
    mutation($input: CreateDiscussionInput!) {
      createDiscussion(input: $input) {
        discussion {
          id,
          url
        }
      }
    }
    """

    # Variables for the mutation
    variables = {
        "input": {
            "repositoryId": repository_id,
            "categoryId": category_id,
            "title": title,
            "body": body
        }
    }

    # Request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Make the POST request
    response = None
    while not response:
      try:
        response = requests.post(url, headers=headers, data=json.dumps({"query": query, "variables": variables}), timeout=5)

        if response.status_code == 200 and 'errors' in response.json():
          response = None

        if response.status_code != 200:
          response = None

      except requests.Timeout as e:
        print(f"equests.post timeout add discussion: {e}")
      except requests.ConnectionError:
        print(f"equests.post connection error add discussion: {e}")

    if response.status_code == 200:
        response_data = response.json()
        if 'errors' in response_data:
            print("Failed to create discussion:", response_data['errors'])
            return None
        else:
            return (response_data['data']['createDiscussion']['discussion']['id'], response_data['data']['createDiscussion']['discussion']['url'])
    else:
        print(f"Failed to create discussion. Status code: {response.status_code}, Response: {response.text}")
        return None


def add_comment(discussion_id, body, token = personal_access_token):
    """
    Create a discussion in a GitHub repository using the GraphQL API.
    Parameters:
    - discussion_id (str): The ID of the discussion.
    - body (str): Body content of the discussion.
    - token (str): Personal Access Token (PAT) with permissions to access the repository.
    """
    
    # GraphQL endpoint
    url = "https://api.github.com/graphql"

    # GraphQL query. Note: This is a mutation, not a query.
    query = """
    mutation($input: AddDiscussionCommentInput!) {
      addDiscussionComment(input: $input) {
        comment {
          id,
          url
        }
      }
    }
    """

    # Variables for the mutation
    variables = {
        "input": {
            "discussionId": discussion_id,
            "body": body
        }
    }

    # Request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Make the POST request
    response = None
    while not response:
      try:
        response = requests.post(url, headers=headers, data=json.dumps({"query": query, "variables": variables}), timeout=5)

        # observed:
        # Failed to create comment: [{'message': 'Something went wrong while executing your query. Please include `DC84:223683:1C480E6:1C68BEF:665CC1DB` when reporting this issue.'}]
        if response.status_code == 200 and 'errors' in response.json():
          response = None

        if response.status_code != 200:
          response = None

      except requests.Timeout as e:
        print(f"equests.post timeout creating comment: {e}")
      except requests.ConnectionError:
        print(f"equests.post connection error creating comment: {e}")

    if response.status_code == 200:
        response_data = response.json()
        if 'errors' in response_data:
            print("Failed to create comment:", response_data['errors'])
            return None
        else:
            print("Comment created successfully. URL:", response_data['data']['addDiscussionComment']['comment']['url'])
            return (response_data['data']['addDiscussionComment']['comment']['id'], response_data['data']['addDiscussionComment']['comment']['url'])
    else:
        print(f"Failed to create comment. Status code: {response.status_code}, Response: {response.text}")
        return None
    

def lock_discussion(discussion_id, token = personal_access_token):
    """
    https://docs.github.com/en/graphql/reference/mutations#locklockable

    Lock a discussion.
    Parameters:
    - discussion_id (str): The ID of the discussion.
    - token (str): Personal Access Token (PAT) with permissions to access the repository.
    """
    
    # GraphQL endpoint
    url = "https://api.github.com/graphql"

    # GraphQL query. Note: This is a mutation, not a query.
    query = """
    mutation($input: LockLockableInput!) {
      lockLockable(input: $input) {
        clientMutationId
      }
    }
    """

    # Variables for the mutation
    variables = {
        "input": {
            "lockableId": discussion_id
        }
    }

    # Request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Make the POST request
    response = None
    while not response:
      try:
        response = requests.post(url, headers=headers, data=json.dumps({"query": query, "variables": variables}), timeout=5)
      except requests.Timeout as e:
        print(f"equests.post timeout locking discusssion: {e}")
      except requests.ConnectionError:
        print(f"equests.post connection error locking discussion: {e}")

    if response.status_code == 200:
        response_data = response.json()
        if 'errors' in response_data:
            print("Failed to lock discussion:", response_data['errors'])
        else:
            print("Locked discssion.")
    else:
        print(f"Failed to lock discussion. Status code: {response.status_code}, Response: {response.text}")


def get_labels(token = personal_access_token, owner = repository_owner, name = repository_name):
    """
    Fetch labels for a repository using the GraphQL API.
    Parameters:
    - token (str): Personal Access Token (PAT) with permissions to access the repository.
    - repo_owner (str): Owner of the repository (username or organization).
    - repo_name (str): Name of the repository.
    """
    url = "https://api.github.com/graphql"
    query = """
    query RepositoryLabels($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        labels(first: 100) {
          nodes {
            name
            id
          }
        }
      }
    }
    """
    variables = {"owner": owner, "name": name}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps({"query": query, "variables": variables}))
    if response.status_code == 200:
        labels = {}
        for label in response.json()['data']['repository']['labels']['nodes']:
          labels[label['name']] = label['id']
        return labels

    else:
        print(f"Failed to fetch labels. Status code: {response.status_code}, Response: {response.text}")
        return None


def create_label(repository_id, label_name, label_color, label_description, token = personal_access_token):
    """
    https://docs.github.com/en/graphql/reference/mutations#createlabel

    Create a label in a GitHub repository using the GraphQL API.
    Parameters:
    - repository_id (str): The ID of the repository.

    - token (str): Personal Access Token (PAT) with permissions to access the repository.
    """
    
    # GraphQL endpoint
    url = "https://api.github.com/graphql"

    # GraphQL query. Note: This is a mutation, not a query.
    query = """
    mutation($input: CreateLabelInput!) {
      createLabel(input: $input) {
        label {
          id
        }
      }
    }
    """

    # Variables for the mutation
    variables = {
        "input": {
            "repositoryId": repository_id,
            "name": label_name,
            "color": label_color,
            "description": label_description
        }
    }

    # Request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps({"query": query, "variables": variables}))

    if response.status_code == 200:
        response_data = response.json()
        if 'errors' in response_data:
            print("Failed to create label:", response_data['errors'])
            return None
        else:
            print(f"Created label {label_name}: ", response_data)
            return response_data['data']['createLabel']['label']['id']
    else:
        print(f"Failed to create label. Status code: {response.status_code}, Response: {response.text}")
        return None


def add_label(discussion_id, label_id, token = personal_access_token):
    """
    https://docs.github.com/en/graphql/reference/mutations#addlabelstolabelable

    Add a label to a discussion.
    Parameters:
    - discussion_id (str): The ID of the discussion.
    - label (str): The ID of the label.
    - token (str): Personal Access Token (PAT) with permissions to access the repository.
    """
    
    # GraphQL endpoint
    url = "https://api.github.com/graphql"

    # GraphQL query. Note: This is a mutation, not a query.
    query = """
    mutation($input: AddLabelsToLabelableInput!) {
      addLabelsToLabelable(input: $input) {
        clientMutationId
      }
    }
    """

    # Variables for the mutation
    variables = {
        "input": {
            "labelableId": discussion_id,
            "labelIds": [ label_id ]
        }
    }

    # Request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Make the POST request
    response = None
    while not response:
      try:
        response = requests.post(url, headers=headers, data=json.dumps({"query": query, "variables": variables}), timeout=5)
      except requests.Timeout as e:
        print(f"equests.post timeout add label: {e}")
      except requests.ConnectionError:
        print(f"equests.post connection error add label: {e}")

    if response.status_code == 200:
        response_data = response.json()
        if 'errors' in response_data:
            print("Failed to add label to discussion:", response_data['errors'])
        else:
            print("Added label to discssion.")
    else:
        print(f"Failed add label to discussion. Status code: {response.status_code}, Response: {response.text}")

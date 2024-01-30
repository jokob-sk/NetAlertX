import os
import requests
import base64
from datetime import datetime

def fetch_sponsors():
    global headers

    graphql_url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {os.environ.get('GH_TOKEN')}",
        "Accept": "application/vnd.github.v4+json",
    }

    # GraphQL query to fetch sponsors
    graphql_query = """
    {
        user(login: "jokob-sk") {
            sponsorshipsAsMaintainer(first: 100, orderBy: {field: CREATED_AT, direction: ASC}, includePrivate: true) {
            totalCount
            pageInfo {
                endCursor
            }
            nodes {
                sponsorEntity {
                ... on User {
                    name
                    login
                    url
                }
                ... on Organization {
                    name
                    url
                    login
                }
                }
                createdAt
                privacyLevel
                tier {
                monthlyPriceInCents
                }
            }
            }
        }
    }
    """

    response = requests.post(graphql_url, json={"query": graphql_query}, headers=headers)
    data = response.json()


    print(f"Debug GraphQL query result: {data}")

    if "errors" in data:
        print(f"GraphQL query failed: {data['errors']}")
        return {"sponsors": []}

    sponsorships = data["data"]["user"]["sponsorshipsAsMaintainer"]["nodes"]
    sponsors = []

    for sponsorship in sponsorships:
        sponsor_entity = sponsorship["sponsorEntity"]
        created_at = datetime.strptime(sponsorship["createdAt"], "%Y-%m-%dT%H:%M:%SZ")
        privacy_level = sponsorship["privacyLevel"]
        monthly_price = sponsorship["tier"]["monthlyPriceInCents"]

        sponsor = {
            "name": sponsor_entity.get("name"),
            "login": sponsor_entity["login"],
            "url": sponsor_entity["url"],
            "created_at": created_at,
            "privacy_level": privacy_level,
            "monthly_price": monthly_price,
        }

        sponsors.append(sponsor)

    print("All Sponsors:")
    print(sponsors)

    return {"sponsors": sponsors}

def generate_sponsors_table(sponsors):
    sponsors_table = "| All Sponsors |\n|---|\n"
    for sponsor in sponsors:
        sponsors_table += f"| [{sponsor['name'] or sponsor['login']}]({sponsor['url']}) |\n"

    return sponsors_table


def update_readme(sponsors_table):
    global headers
    repo_owner = "jokob-sk"
    repo_name = "Pi.Alert"

    # Update the README.md file in the GitHub repository
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/README.md"

    # Fetch the current content of the README.md file
    response = requests.get(api_url, headers=headers)
    readme_data = response.json()

    # Extract content from the dictionary
    readme_content = base64.b64decode(readme_data['content']).decode()

    # Find the start and end markers
    start_marker = "<!-- SPONSORS-LIST DO NOT MODIFY BELOW -->"
    end_marker = "<!-- SPONSORS-LIST DO NOT MODIFY ABOVE -->"

    # Replace the content between markers with the generated sponsors table
    start_index = readme_content.find(start_marker)
    end_index = readme_content.find(end_marker, start_index + len(start_marker))
    if start_index != -1 and end_index != -1:
        updated_readme = (
            readme_content[:start_index + len(start_marker)]
            + "\n"
            + sponsors_table
            + "\n"
            + readme_content[end_index:]
        )
    else:
        print("Markers not found in README.md. Make sure they are correctly placed.")
        return

    updated_content_base64 = base64.b64encode(updated_readme.encode()).decode()

    # Create a commit to update the README.md file
    commit_message = "[🤖Automation] Update README with sponsors information"
    commit_data = {
        "message": commit_message,
        "content": updated_content_base64,
        "sha": readme_data["sha"],
        "branch": "main",  # Update the branch name as needed
    }

    commit_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/README.md"
    commit_response = requests.put(commit_url, headers=headers, json=commit_data)

    if commit_response.status_code == 200:
        print("README.md updated successfully in the GitHub repository.")
    else:
        print(f"Failed to update README.md. Status code: {commit_response.status_code}")
        print(commit_response.json())

    print("README.md updated successfully with the sponsors table.")

def main():
    sponsors_data = fetch_sponsors()
    sponsors = sponsors_data.get("sponsors", [])

    sponsors_table = generate_sponsors_table(sponsors)
    update_readme(sponsors_table)

if __name__ == "__main__":
    main()

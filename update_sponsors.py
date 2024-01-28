import os
import requests
import base64

def fetch_sponsors():
    graphql_url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {os.environ.get('GH_TOKEN')}",
        "Accept": "application/vnd.github.v4+json",
    }

    # GraphQL query to fetch sponsors
    graphql_query = """
    {
      viewer {
        login
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

    if "errors" in data:
        print(f"GraphQL query failed: {data['errors']}")
        return {"current_sponsors": [], "past_sponsors": []}

    sponsorships = data["data"]["viewer"]["sponsorshipsAsMaintainer"]["nodes"]
    current_sponsors = []
    past_sponsors = []

    for sponsorship in sponsorships:
        sponsor_entity = sponsorship["sponsorEntity"]
        created_at = sponsorship["createdAt"]
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

        if created_at == sponsorship["createdAt"]:
            past_sponsors.append(sponsor)
        else:
            current_sponsors.append(sponsor)

    return {"current_sponsors": current_sponsors, "past_sponsors": past_sponsors}

def generate_sponsors_table(current_sponsors, past_sponsors):
    current_table = "| Current Sponsors |\n|---|\n"
    for sponsor in current_sponsors:
        current_table += f"| [{sponsor['name'] or sponsor['login']}]({sponsor['url']}) - ${sponsor['monthly_price'] / 100:.2f} |\n"

    past_table = "| Past Sponsors |\n|---|\n"
    for sponsor in past_sponsors:
        past_table += f"| [{sponsor['name'] or sponsor['login']}]({sponsor['url']}) - ${sponsor['monthly_price'] / 100:.2f} |\n"

    return current_table + "\n" + past_table

def update_readme(sponsors_table):

    repo_owner = "jokob-sk"
    repo_name = "Pi.Alert"    
    readme_path = "README.md"

    with open(readme_path, "r") as readme_file:
        readme_content = readme_file.read()

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


    # Update the README.md file in the GitHub repository
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/README.md"

    updated_content_base64 = base64.b64encode(readme_content.encode()).decode()

    # Create a commit to update the README.md file
    commit_message = "[🤖Automation] Update README with sponsors information"
    commit_data = {
        "message": commit_message,
        "content": updated_content_base64,        
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
    current_sponsors = sponsors_data.get("current_sponsors", [])
    past_sponsors = sponsors_data.get("past_sponsors", [])

    sponsors_table = generate_sponsors_table(current_sponsors, past_sponsors)
    update_readme(sponsors_table)

if __name__ == "__main__":
    main()

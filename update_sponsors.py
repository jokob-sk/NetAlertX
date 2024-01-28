import os
import requests

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
    readme_path = "README.md"
    with open(readme_path, "r") as readme_file:
        readme_content = readme_file.read()

    # Replace the placeholder <!--SPONSORS-LIST--> with the generated sponsors table
    updated_readme = readme_content.replace("<!--SPONSORS-LIST-->", sponsors_table)

    with open(readme_path, "w") as readme_file:
        readme_file.write(updated_readme)

def main():
    sponsors_data = fetch_sponsors()
    current_sponsors = sponsors_data.get("current_sponsors", [])
    past_sponsors = sponsors_data.get("past_sponsors", [])

    sponsors_table = generate_sponsors_table(current_sponsors, past_sponsors)
    update_readme(sponsors_table)

if __name__ == "__main__":
    main()

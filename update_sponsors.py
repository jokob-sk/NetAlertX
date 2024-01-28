import os
import requests

def fetch_sponsors():
    repo_owner = "jokob-sk"
    repo_name = "Pi.Alert"
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/sponsors"

    headers = {
        "Authorization": f"Bearer {os.environ.get('GH_TOKEN')}",
        "Accept": "application/vnd.github.v3+json",
    }

    current_sponsors = []
    past_sponsors = []

    page = 1
    while True:
        params = {"page": page}
        response = requests.get(api_url, headers=headers, params=params)
        data = response.json()

        if not data:
            break

        for sponsor in data:
            if sponsor["sponsorship_created_at"] == sponsor["sponsorship_updated_at"]:
                past_sponsors.append(sponsor)
            else:
                current_sponsors.append(sponsor)

        page += 1

    return {"current_sponsors": current_sponsors, "past_sponsors": past_sponsors}

def generate_sponsors_table(current_sponsors, past_sponsors):
    current_table = "| Current Sponsors |\n|---|\n"
    for sponsor in current_sponsors:
        current_table += f"| [{sponsor['login']}](https://github.com/{sponsor['login']}) |\n"

    past_table = "| Past Sponsors |\n|---|\n"
    for sponsor in past_sponsors:
        past_table += f"| {sponsor['login']} |\n"

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

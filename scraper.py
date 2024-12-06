import requests
import os
import time
import json
import re
from dotenv import load_dotenv

# load env variables
load_dotenv()


GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def fetch_repos_by_query(query, max_repos, per_page):
    """Fetch repositories based on a search query.

        Parameters: 
        query (str): search query to filter repos
        max_repos (int): max number of repos to retrieve
        per_page (int): number of repos to return per page

        Returns:
        List: Returns list of repos matching the query string
    """
    url = f'https://api.github.com/search/repositories?q={query}&sort=stars&order=desc'
    repos = []
    page = 1

    while len(repos) < max_repos:
        params = {'page': page, 'per_page': per_page}
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code == 200:
            data = response.json()
            repos.extend(data.get('items', []))
            page += 1
            # Stop pagination if there are no more repositories
            if len(data.get('items', [])) < per_page:
                break
        else:
            raise Exception(f"Failed to fetch repositories: {response.status_code} {response.text}")
        
        time.sleep(1) 

    return repos[:max_repos]

def fetch_readme(repo):
    """Fetch the README content of a repo

        Parameters:
        repo (dict): dictionary containing information about the repo.

        Returns:    
        str: Return the contents of the readme file, or None if no readme is found
    """
    contents_url = f"https://api.github.com/repos/{repo['full_name']}/contents"
    response = requests.get(contents_url, headers=HEADERS)
    if response.status_code == 200:
        contents = response.json()
        for file in contents:
            if file['name'].lower() == 'readme.md':  # Look for README.md
                readme_response = requests.get(file['download_url'], headers=HEADERS)
                if readme_response.status_code == 200:
                    return clean_readme(readme_response.text) # clean the readme
                else:
                    raise Exception(f"Failed to fetch README: {readme_response.status_code}")
    else:
        raise Exception(f"Failed to fetch contents: {response.status_code} {response.text}")
    return None  # return None if no readme is found in the repo

def clean_readme(readme_text):
    """Remove Markdown tags and clean the README content.

        Parameters:
        readme_text (str): raw readme content

        Returns:
        str: Returns cleaned readme
    """

    # TODO: not working as assumed, work on this later

    readme_text = re.sub(r'!\[.*?\]\(.*?\)', '', readme_text)  # Remove images
    readme_text = re.sub(r'\[.*?\]\(.*?\)', '', readme_text)  # Remove links
    readme_text = re.sub(r'#.*', '', readme_text)  # Remove headings
    readme_text = re.sub(r'(```[\s\S]*?```)', '', readme_text)  # Remove code blocks
    readme_text = re.sub(r'[-*+]\s+', '', readme_text)  # Remove unordered list markers
    readme_text = re.sub(r'\d+\.\s+', '', readme_text)  # Remove ordered list numbers
    readme_text = readme_text.strip()  # Remove extra whitespace
    return readme_text

def fetch_all_readmes(query, max_repos, per_page):
    """Fetch README files for the repositories based on a search query.
    
        Parameters:
        query (str): search query to filter repos
        max_repos (int): max number of repos to rezurn
        per_page (int): number of repos to return per page

        Returns:
        list: Returns list of readmes(each as a dict)
    """
    repos = fetch_repos_by_query(query, max_repos, per_page)
    readmes = []
    for repo in repos:
        print(f"Fetching README from {repo['full_name']}...")
        try:
            readme = fetch_readme(repo)
            if readme:
                readmes.append({"repo": repo['full_name'], "readme": readme})
                print(f"Successfully fetched README from {repo['full_name']}.")
            else:
                print(f"No README found in {repo['full_name']}.")
        except Exception as e:
            print(f"Error fetching README from {repo['full_name']}: {e}")

        time.sleep(1) 

    return readmes


def append_to_json_file(file_name, data):
    """Append the fetched README data to a JSON file.

        Parameters:
        file_name_or_path (str): path to file
        data (list): list of readmes

        Returns: 
        None
    """
    try:
        # Load existing data if the file exists
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        existing_data.extend(data)

        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        print(f"Appended readmes to the file: {file_name}.")
    except Exception as e:
        print(f"Error appending to file {file_name}: {e}")


if __name__ == "__main__":
    try:
        # List of queries
        queries = ['energy', 'climate', 'green+energy', 'bioinformatics', 'distributed+systems', 'engineering', 'health', 'marine', 'space', 'artificial+intelligence', 'research']

        if not os.path.exists("./files/"):
            os.makedirs("./files/")
        
        # for each query, fetch readmes and add readmes to output file
        for query in queries:
            readmes = fetch_all_readmes(query, max_repos=100, per_page=100)
            append_to_json_file('./files/readmes.json', readmes)
        
    except Exception as e:
        print(f"An error occurred: {e}")

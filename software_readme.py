import requests
import logging
import json
from selenium_scraping import get_gitlab_project_id
from scraper import GITHUB_HEADERS, GITLAB_HEADERS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VALID_README_NAMES = [
    'readme.md', 'readme.markdown', 'readme.txt',
    'readme', 'readme.rst', 'readme.html',
    'readme.adoc', 'readme.asciidoc'
]

def fetch_file_content(url, headers):
    """Fetch the content of a file given its URL."""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        logging.error(f"Failed to fetch file from {url} with status code {response.status_code}")
        return None

def get_gitlab_readme_content(gitlab_instance_url, project_id, headers):
    """Fetch the README.md content from a GitLab repository."""
    try:
        repo_tree_url = f"https://{gitlab_instance_url}/api/v4/projects/{project_id}/repository/tree"
        response = requests.get(repo_tree_url, headers=headers)
        logging.info(f"Fetching repository tree: {repo_tree_url}")

        if response.status_code != 200:
            logging.error(f"Error fetching repository tree: {response.status_code}")
            return None

        for file in response.json():
            if file['name'].lower() in VALID_README_NAMES:
                file_url = f"https://{gitlab_instance_url}/api/v4/projects/{project_id}/repository/files/{file['path']}/raw"
                logging.info(f"Found README.md. Fetching content from: {file_url}")
                return fetch_file_content(file_url, headers)

        logging.warning("README.md not found in the repository.")
        return None

    except Exception as e:
        logging.exception("An error occurred while fetching the GitLab README.md content.")
        return None

def get_github_readme_content(repo_full_name, headers):
    """Fetch the README.md content from a GitHub repository."""
    try:
        contents_url = f"https://api.github.com/repos/{repo_full_name}/contents"
        response = requests.get(contents_url, headers=headers)
        logging.info(f"Fetching repository contents: {contents_url}")

        if response.status_code != 200:
            logging.error(f"Failed to fetch contents: {response.status_code} {response.text}")
            return None

        for file in response.json():
            if file['name'].lower() in VALID_README_NAMES:
                logging.info(f"Found README.md. Fetching content from: {file['download_url']}")
                return fetch_file_content(file['download_url'], headers)

        logging.warning("README.md not found in the repository.")
        return None

    except Exception as e:
        logging.exception("An error occurred while fetching the GitHub README.md content.")
        return None

def get_full_name(repo_url):
    """Extract the full repository name from a GitHub URL."""
    if not repo_url.startswith("https://github.com/"):
        logging.error("Invalid GitHub URL")
        return None

    parts = repo_url.split("https://github.com/")[1].split("/")
    if len(parts) < 2:
        logging.error("GitHub URL is malformed: {repo_url}")
        return None
    
    parts = [part for part in parts]

    return f"{parts[0]}/{parts[1]}".strip()

def update_readme_in_json(input_file, output_file, github_headers, gitlab_headers):
    """Update the JSON file with README content from GitHub and GitLab repositories."""
    try:
        with open(input_file, "r", encoding="utf-8") as rf:
            data = json.load(rf)

        for obj in data.get("final_links", []):
            repo_link = obj.get("repo_link")
            if not repo_link:
                logging.warning("No repository link found.")
                obj["readme"] = ""
                continue

            domain = repo_link.split("/")[2]

            if domain == "github.com":
                repo_full_name = get_full_name(repo_link)
                if not repo_full_name:
                    obj["readme"] = ""
                else:
                    obj["readme"] = get_github_readme_content(repo_full_name, github_headers) or ""

            else:
                project_id = get_gitlab_project_id(repo_link)
                if not project_id:
                    obj["readme"] = ""
                    obj["project_id"] = ""
                else:
                    gitlab_instance_url = repo_link.split("/")[2]
                    obj["readme"] = get_gitlab_readme_content(gitlab_instance_url, project_id, gitlab_headers) or ""
                    obj["project_id"] = project_id

        with open(output_file, "w", encoding="utf-8") as wf:
            json.dump(data, wf, ensure_ascii=False, indent=4)

        logging.info(f"Updated JSON file written to {output_file}")

    except Exception as e:
        logging.exception("An error occurred while updating the JSON file.")


update_readme_in_json("./files/software_pages.json", "./files/updated_software_pages.json", GITHUB_HEADERS, GITLAB_HEADERS)

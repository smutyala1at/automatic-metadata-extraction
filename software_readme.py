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

VALID_AUTHORS = [
    'authors', 'authors.txt', 'authors.md', 'authors.rst',
]

VALID_CONTRIBUTORS = [
    'contributors', 'contributors.txt', 'contributors.md', 'contributors.rst'
]

VALID_LICENSES = [
    'LICENSE', 'LICENSE.txt', 'LICENSE.md', 'LICENSE.rst',
]

# List of dependency-related files and lock files
VALID_DEPENDENCIES = [
    "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "Gemfile", "package.json",
    "pom.xml", "build.gradle", "go.mod", "composer.json", "Cargo.toml", "vcpkg.json", "conanfile.txt",
    "CMakeLists.txt", "Spack.yaml", ".csproj", "packages.config", "Package.swift", "Podfile", "pubspec.yaml",
    "DESCRIPTION", "mix.exs", "install.sh", "bootstrap.sh", "cpanfile", "Makefile.PL", "Build.PL", "stack.yaml",
    "cabal.project", "rebar.config", "Project.toml", "Manifest.toml", "build.sbt"
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

    codemeta = {"content": ""}
    readme = {"content": ""}
    dependencies = {"content": ""}
    authors = {"content": ""}
    contributors = {"content": ""}
    licenses = {"content": ""}

    try:
        repo_tree_url = f"https://{gitlab_instance_url}/api/v4/projects/{project_id}/repository/tree"
        response = requests.get(repo_tree_url, headers=headers)
        logging.info(f"Fetching repository tree: {repo_tree_url}")

        if response.status_code != 200:
            logging.error(f"Error fetching repository tree: {response.status_code}")
            return None

        for file in response.json():
            file_url = f"https://{gitlab_instance_url}/api/v4/projects/{project_id}/repository/files/{file['path']}/raw"

            if file['name'].lower() == "codemeta.json":
                """ can get most of the important content here - Authors, Contributors, Description, id """
                codemeta["content"] += f"{file['name']}: {fetch_file_content(file_url, headers)}\n"

            if file['name'].lower() in VALID_README_NAMES:
                """ get readmes for installation and keywords """
                readme["content"] += f"{file['name']}: {fetch_file_content(file_url, headers)}\n"

            if file['name'].lower() in VALID_DEPENDENCIES:
                """ get dependencies from whatever files are available """
                dependencies["content"] += f"{file['name']}: {fetch_file_content(file_url, headers)}\n"

            if file['name'].lower() == VALID_AUTHORS:
                """ authors files are rare to find, try for luck, if not we try to get author from the first contributor from the repo"""
                authors["content"] += f"{file['name']}: {fetch_file_content(file_url, headers)}\n"

            if file['name'].lower() == VALID_CONTRIBUTORS:
                """ get contributors from a file or get it from commit history """
                contributors["content"] += f"{file['name']}: {fetch_file_content(file_url, headers)}\n"
            
            if file['name'].lower() in VALID_LICENSES:
                licenses["content"] += f"{file['name']}: {fetch_file_content(file_url, headers)}\n"


            

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

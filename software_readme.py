import asyncio
import aiohttp
import logging
import json
import os
import urllib.parse
import time
from selenium_scraping import get_gitlab_project_id


GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITLAB_HEADERS = {"PRIVATE-TOKEN": GITLAB_TOKEN} if GITLAB_TOKEN else {}


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VALID_README_NAMES = [
    'readme.md', 'readme.markdown', 'readme.txt',
    'readme', 'readme.rst', 'readme.html',
    'readme.adoc', 'readme.asciidoc'
]

VALID_DEPENDENCIES = [
    "requirements.txt", "pipfile", "pyproject.toml", "setup.py", "gemfile", "package.json",
    "pom.xml", "build.gradle", "go.mod", "composer.json", "cargo.toml", "vcpkg.json", "conanfile.txt",
    "cmakelists.txt", "spack.yaml", ".csproj", "packages.config", "package.swift", "podfile", "pubspec.yaml",
    "description", "mix.exs", "install.sh", "bootstrap.sh", "cpanfile", "makefile.pl", "build.pl", "stack.yaml",
    "cabal.project", "rebar.config", "project.toml", "manifest.toml", "build.sbt"
]

async def fetch_github_file(session, download_url, headers):
    """Fetch file from GitHub using download_url."""
    try:
        async with session.get(download_url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
            logging.error(f"Failed to fetch GitHub file: {response.status}")
            return None
    except Exception as e:
        logging.error(f"Error fetching GitHub file: {e}")
        return None

async def fetch_gitlab_file(session, gitlab_instance_url, project_id, file_path, headers):
    """Fetch file from GitLab using repository/files API."""
    try:
        encoded_path = urllib.parse.quote(file_path, safe='')
        url = f"https://{gitlab_instance_url}/api/v4/projects/{project_id}/repository/files/{encoded_path}/raw"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
            logging.error(f"Failed to fetch GitLab file: {response.status}")
            return None
    except Exception as e:
        logging.error(f"Error fetching GitLab file: {e}")
        return None

# Update the file matching functions in get_gitlab_content
async def get_gitlab_content(session, gitlab_instance_url, project_id, headers):
    """Fetch content from GitLab repository root level."""
    contents = {"codemeta": "", "readme": "", "dependencies": ""}
    try:
        repo_tree_url = f"https://{gitlab_instance_url}/api/v4/projects/{project_id}/repository/tree"
        logging.info(f"Fetching from {repo_tree_url}")
        
        async with session.get(repo_tree_url, headers=headers) as response:
            response_text = await response.text()
            if response.status != 200:
                logging.error(f"Failed to fetch repository tree: {response.status}, Response: {response_text}")
                return contents

            try:
                files = json.loads(response_text)
                logging.info(f"Found {len(files)} files in repository")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                return contents

            tasks = []
            file_categories = []

            # Log all files found
            for file in files:
                logging.info(f"Found file: {file.get('name', 'NO_NAME')} of type {file.get('type', 'NO_TYPE')}")

            for file in files:
                if file.get('type', '') != 'blob':
                    continue

                file_name = file['name'].lower()
                file_path = file['path']
                logging.info(f"Processing file: {file_name} at path: {file_path}")

                # Check for codemeta
                if file_name == "codemeta.json":
                    logging.info(f"Found codemeta file: {file_path}")
                    tasks.append(fetch_gitlab_file(session, gitlab_instance_url, project_id, file_path, headers))
                    file_categories.append('codemeta')
                
                # Check for readme
                for valid_readme in VALID_README_NAMES:
                    if file_name == valid_readme.lower():
                        logging.info(f"Found readme file: {file_path}")
                        tasks.append(fetch_gitlab_file(session, gitlab_instance_url, project_id, file_path, headers))
                        file_categories.append('readme')
                        break
                
                # Check for dependencies
                for valid_dep in VALID_DEPENDENCIES:
                    if file_name == valid_dep.lower():
                        logging.info(f"Found dependency file: {file_path}")
                        tasks.append(fetch_gitlab_file(session, gitlab_instance_url, project_id, file_path, headers))
                        file_categories.append('dependencies')
                        break

            if tasks:
                logging.info(f"Fetching content for {len(tasks)} files")
                results = await asyncio.gather(*tasks)
                for category, content in zip(file_categories, results):
                    if content:
                        contents[category] += f"{content}\n"
                        logging.info(f"Successfully fetched content for {category}")
                    else:
                        logging.error(f"Failed to fetch content for {category}")

            else:
                logging.warning("No matching files found to fetch")

    except Exception as e:
        logging.error(f"Error fetching GitLab content: {e}", exc_info=True)

    return contents

async def get_github_content(session, repo_full_name, headers):
    """Fetch content from GitHub repository root level."""
    contents = {"codemeta": "", "readme": "", "dependencies": ""}
    try:
        contents_url = f"https://api.github.com/repos/{repo_full_name}/contents"
        logging.info(f"Fetching from {contents_url}")
        
        async with session.get(contents_url, headers=headers) as response:
            response_text = await response.text()
            if response.status != 200:
                logging.error(f"Failed to fetch repository contents: {response.status}, Response: {response_text}")
                return contents

            try:
                files = json.loads(response_text)
                logging.info(f"Found {len(files)} files in repository")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                return contents

            tasks = []
            file_categories = []

            # Log all files found
            for file in files:
                logging.info(f"Found file: {file.get('name', 'NO_NAME')} of type {file.get('type', 'NO_TYPE')}")

            for file in files:
                if file['type'] != 'file':
                    continue

                file_name = file['name'].lower()
                logging.info(f"Processing file: {file_name}")

                # Check for codemeta
                if file_name == "codemeta.json":
                    logging.info(f"Found codemeta file: {file_name}")
                    tasks.append(fetch_github_file(session, file["download_url"], headers))
                    file_categories.append('codemeta')
                
                # Check for readme
                for valid_readme in VALID_README_NAMES:
                    if file_name == valid_readme.lower():
                        logging.info(f"Found readme file: {file_name}")
                        tasks.append(fetch_github_file(session, file["download_url"], headers))
                        file_categories.append('readme')
                        break
                
                # Check for dependencies
                for valid_dep in VALID_DEPENDENCIES:
                    if file_name == valid_dep.lower():
                        logging.info(f"Found dependency file: {file_name}")
                        tasks.append(fetch_github_file(session, file["download_url"], headers))
                        file_categories.append('dependencies')
                        break

            if tasks:
                logging.info(f"Fetching content for {len(tasks)} files")
                results = await asyncio.gather(*tasks)
                for category, content in zip(file_categories, results):
                    if content:
                        contents[category] += f"{content}\n"
                        logging.info(f"Successfully fetched content for {category}")
                    else:
                        logging.error(f"Failed to fetch content for {category}")

            else:
                logging.warning("No matching files found to fetch")

    except Exception as e:
        logging.error(f"Error fetching GitHub content: {e}", exc_info=True)

    return contents

async def get_full_name(repo_url):
    """Extract the full repository name from a GitHub URL."""
    if not repo_url.startswith("https://github.com/"):
        logging.error(f"Invalid GitHub URL: {repo_url}")
        return None

    parts = repo_url[len("https://github.com/"):].split("/")
    if len(parts) < 2:
        logging.error(f"GitHub URL is malformed: {repo_url}")
        return None

    return f"{parts[0]}/{parts[1]}".strip()

async def update_readme_in_json(input_file, output_file):
    """Update the JSON file with content from GitHub and GitLab repositories."""
    try:
        with open(input_file, "r", encoding="utf-8") as rf:
            data = json.load(rf)

        async with aiohttp.ClientSession() as session:
            tasks = []

            for obj in data.get("final_links", []):
                repo_link = obj.get("repo_link", "")
                if not repo_link:
                    logging.warning("No repository link found.")
                    obj["content"] = {}
                    continue

                domain = repo_link.split("/")[2]

                # For the GitHub section
                if domain == "github.com":
                    repo_full_name = await get_full_name(repo_link)  # Make sure this is async
                    if repo_full_name:
                        task = await get_github_content(session, repo_full_name, GITHUB_HEADERS)
                        tasks.append((obj, task))
                    else:
                        obj["content"] = {}

                else:
                    project_id = await get_gitlab_project_id(repo_link)
                    time.sleep(1)
                    if project_id:
                        gitlab_instance_url = repo_link.split("/")[2]
                        print(f"Project ID: {project_id}")
                        task = get_gitlab_content(session, gitlab_instance_url, project_id, GITLAB_HEADERS)
                        tasks.append((obj, task))
                    else:
                        obj["content"] = {}

            results = await asyncio.gather(*[task for obj, task in tasks])

            for (obj, _), content in zip(tasks, results):
                obj["content"] = content

        with open(output_file, "w", encoding="utf-8") as wf:
            json.dump(data, wf, ensure_ascii=False, indent=4)

        logging.info(f"Updated JSON file written to {output_file}")

    except Exception as e:
        logging.error(f"An error occurred while updating the JSON file: {e}")

if __name__ == "__main__":
    asyncio.run(
        update_readme_in_json(
            "./files/software_pages.json",
            "./files/updated_software_pages.json",
        )
    )

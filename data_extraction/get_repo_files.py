import asyncio
import aiohttp
import logging
import json
import os
import urllib.parse
import dotenv
import time
import sys
from scrape_repo_links import get_gitlab_project_id

dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN not set. GitHub API requests will be rate limited.")
    
GITHUB_HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
if not GITLAB_TOKEN:
    print("Warning: GITLAB_TOKEN not set. GitLab API requests may be limited.")
    
GITLAB_HEADERS = {"PRIVATE-TOKEN": GITLAB_TOKEN} if GITLAB_TOKEN else {}


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


def format_json_content(content):
    """Format JSON content by compressing it to a single line with no extra spaces."""
    try:
        parsed_json = json.loads(content)
        compact_json = json.dumps(parsed_json, separators=(',', ':'))
        return compact_json
    except json.JSONDecodeError:
        content = content.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
        while '  ' in content:
            content = content.replace('  ', ' ')
        return content.strip()

def format_markdown_content(content):
    """
    Format Markdown content by cleaning up special characters and replacing newlines with spaces.
    """
    replacements = {
        '\u2018': "'",      # Left single quote
        '\u2019': "'",      # Right single quote
        '\u201c': '"',      # Left double quote
        '\u201d': '"',      # Right double quote
        '\u2013': '-',      # En dash
        '\u2014': '--',     # Em dash
        '\u2026': '...',    # Horizontal ellipsis
        '\u00a0': ' ',      # Non-breaking space
        '\r\n': ' ',        # Windows line endings replaced with space
        '\r': ' ',          # Old Mac line endings replaced with space
        '\n': ' ',          # Unix line endings replaced with space
        '\t': ' ',          # Convert tabs to spaces
        '\u200b': '',       # Zero width space
        '\u200c': '',       # Zero width non-joiner
        '\ufeff': ''        # BOM
    }
    
    cleaned = content
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    while '  ' in cleaned:
        cleaned = cleaned.replace('  ', ' ')
    
    cleaned = cleaned.strip()
    
    return cleaned

def format_dependency_content(content):
    """Format dependency file content by replacing newlines with spaces and normalizing whitespace."""
    content = content.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

    while '  ' in content:
        content = content.replace('  ', ' ')
    
    return content.strip()

def format_file_content(file_path, content):
    """Format the content of a file based on its type."""
    file_path_lower = file_path.lower()
    if file_path_lower.endswith(".json"):
        return format_json_content(content)
    elif any(file_path_lower.endswith(ext) for ext in (".md", ".markdown", ".txt", ".rst", ".html", ".adoc", ".asciidoc")):
        return format_markdown_content(content)
    elif any(file_path_lower.endswith(dep.lower()) for dep in VALID_DEPENDENCIES):
        return format_dependency_content(content)
    else:
        return content

async def fetch_github_file(session, download_url, headers):
    """Fetch file from GitHub using download_url."""
    try:
        async with session.get(download_url, headers=headers) as response:
            if response.status == 200:
                content = await response.text()
                return format_file_content(download_url, content)
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
                content = await response.text()
                return format_file_content(file_path, content)
            logging.error(f"Failed to fetch GitLab file: {response.status}")
            return None
    except Exception as e:
        logging.error(f"Error fetching GitLab file: {e}")
        return None


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


                if file_name == "codemeta.json":
                    logging.info(f"Found codemeta file: {file_path}")
                    tasks.append(fetch_gitlab_file(session, gitlab_instance_url, project_id, file_path, headers))
                    file_categories.append('codemeta')
                

                for valid_readme in VALID_README_NAMES:
                    if file_name == valid_readme.lower():
                        logging.info(f"Found readme file: {file_path}")
                        tasks.append(fetch_gitlab_file(session, gitlab_instance_url, project_id, file_path, headers))
                        file_categories.append('readme')
                        break
                
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


                if file_name == "codemeta.json":
                    logging.info(f"Found codemeta file: {file_name}")
                    tasks.append(fetch_github_file(session, file["download_url"], headers))
                    file_categories.append('codemeta')
                

                for valid_readme in VALID_README_NAMES:
                    if file_name == valid_readme.lower():
                        logging.info(f"Found readme file: {file_name}")
                        tasks.append(fetch_github_file(session, file["download_url"], headers))
                        file_categories.append('readme')
                        break
                

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

async def fetch_repo_content_and_update_json(input_file, output_file):
    """Update the JSON file with content from GitHub and GitLab repositories."""
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            logging.error(f"Input file not found: {input_file}")
            return
            
        with open(input_file, "r", encoding="utf-8") as rf:
            data = json.load(rf)

        # Create a new data structure for the output
        output_data = {"repositories_with_content": []}
        
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
                    repo_full_name = await get_full_name(repo_link) 
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
                        # Call get_gitlab_content with await
                        task = await get_gitlab_content(session, gitlab_instance_url, project_id, GITLAB_HEADERS)
                        tasks.append((obj, task))
                    else:
                        obj["content"] = {}

            for obj, content in tasks:
                obj["content"] = content
                output_data["repositories_with_content"].append(obj)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as wf:
            json.dump(output_data, wf, ensure_ascii=False, indent=4)

        logging.info(f"Updated JSON file written to {output_file}")

    except Exception as e:
        logging.error(f"An error occurred while updating the JSON file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":    
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Root directory: {ROOT_DIR}")

    
    INPUT_FILE = os.path.join(ROOT_DIR, "data_extraction/files", "links.json")
    OUTPUT_FILE = os.path.join(ROOT_DIR, "data_extraction/files", "software_repositories_with_content.json")
    
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        sys.exit(1)
        
    asyncio.run(
        fetch_repo_content_and_update_json(
            INPUT_FILE,
            OUTPUT_FILE,
        )
    )
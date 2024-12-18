import os
import json
import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse
from dotenv import load_dotenv
from selenium.webdriver.chrome.options import Options
import urllib.parse
import requests
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

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

def get_api_url(instance_url):
    return f"https://{instance_url.split("/")[2]}/api/v4"

def format_file_content(file_path, content):
    try:
        if file_path.endswith('.json'):
            return json.loads(content)
        return content
    except json.JSONDecodeError:
        return content

def get_gitlab_project_id(repo_link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(repo_link)
    except Exception as e:
        driver.quit()
        return ""
    
    driver.implicitly_wait(10)

    try: 
        span_element = driver.find_element(By.XPATH, "//span[@itemprop='identifier' and @data-testid='project-id-content']")
        project_id = span_element.text.strip().split(" ")[2]
        driver.quit()
        return project_id
    except NoSuchElementException:
        try:
            alert = driver.find_element(By.CLASS_NAME, "gl-alert-body")
            driver.quit()
            return ""
        except NoSuchElementException:
            driver.quit()
            return ""

async def fetch_repo_info(session, project_id, headers, api_url):
    url = f"{api_url}/projects/{project_id}"
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def get_version(session, project_id, headers, api_url):
    url = f"{api_url}/projects/{project_id}/repository/tags"
    async with session.get(url, headers=headers) as response:
        tags = await response.json()
        if tags:
            return tags[0]["release"]['tag_name']
        return None

async def get_repo_languages(session, project_id, headers, api_url):
    url = f"{api_url}/projects/{project_id}/languages"
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def fetch_file_content_async(session, api_url, project_id, file_path, headers):
    """Asynchronously fetch the content of a file from GitLab."""
    try:
        encoded_path = urllib.parse.quote(file_path, safe='')
        url = f"{api_url}/projects/{project_id}/repository/files/{encoded_path}/raw"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Failed to fetch content from {url}: {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching file content: {e}")
        return None

async def fetch_root_files_async(session, api_url, project_id, headers):
    """Fetch the root level files of a GitLab repository asynchronously."""
    try:
        url = f"{api_url}/projects/{project_id}/repository/tree"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch root files: {response.status}")
                return []
    except Exception as e:
        print(f"An error occurred while fetching the root files: {e}")
        return []

async def get_repo_files(session, api_url, project_id, headers):
    """Fetch and process repository files from GitLab."""
    root_files = await fetch_root_files_async(session, api_url, project_id, headers)

    if not root_files:
        print("Root files are empty")
        return None

    file_paths = {"dependencies": [], "readme": [], "codemeta": []}
    
    for file in root_files:
        file_path = file["path"].lower()
        if file_path in VALID_DEPENDENCIES:
            file_paths["dependencies"].append(file)
        elif file_path in VALID_README_NAMES:
            file_paths["readme"].append(file)
        elif file_path == "codemeta.json":
            file_paths["codemeta"].append(file)

    if not any(file_paths.values()):
        print("No relevant files found")
        return {
            "codemeta": [],
            "dependencies": [],
            "readme": []
        }

    result = {
        "codemeta": [],
        "dependencies": [],
        "readme": []
    }

    for category, files in file_paths.items():
        if files:
            file_contents = await asyncio.gather(*[
                fetch_file_content_async(session, api_url, project_id, file["path"], headers) 
                for file in files
            ])
            result[category] = [
                {"path": file["path"], "content": format_file_content(file["path"], content)}
                for file, content in zip(files, file_contents)
                if content
            ]

    return result

async def get_contributors(session, project_id, headers, api_url):
    url = f"{api_url}/projects/{project_id}/repository/contributors"
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def fetch_license(session, project_id, headers, api_url):
    url = f"{api_url}/projects/{project_id}/repository/files/LICENSE/raw"
    async with session.get(url, headers=headers) as response:
        return await response.text()

async def get_gitlab_repo_data(url):
    project_id = get_gitlab_project_id(url)
    if not project_id:
        print(f"Failed to fetch project ID for {url}")
        return None

    headers = {"Authorization": f"token {GITLAB_TOKEN}"}
    api_url = get_api_url(url)

    async with aiohttp.ClientSession() as session:
        # repo_info, latest_version, languages, other_metadata, contributors = await asyncio.gather(
        #     fetch_repo_info(session, project_id, headers, api_url),
        #     get_version(session, project_id, headers, api_url),
        #     get_repo_languages(session, project_id, headers, api_url),
        #     get_repo_files(session, api_url, project_id, headers),
        #     get_contributors(session, project_id, headers, api_url)
        # )

        other_metadata = await get_repo_files(session, api_url, project_id, headers)

        if other_metadata:
            # license_info = await fetch_license(session, project_id, headers, api_url)
            data = {
                # "name": repo_info["name"],
                # "description": repo_info["description"],
                # "url": repo_info["web_url"],
                # "license": license_info if license_info else None,
                # "latest_version": latest_version,
                # "topics": repo_info.get("topics", []),
                # "languages": languages,
                "other_metadata": other_metadata,
                # "contributors": contributors
            }
            return data
        else:
            print(f"Failed to fetch {url}")
            return None

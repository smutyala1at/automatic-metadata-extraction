import asyncio
import aiohttp
import os
import json
import sys
import argparse
from urllib.parse import urlparse, quote
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load environment variables
load_dotenv()

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_DEFAULT_URL = "https://gitlab.com/api/v4"

VALID_README_NAMES = [
    'readme.md', 'readme.markdown', 'readme.txt',
    'readme', 'readme.rst', 'readme.html',
    'readme.adoc', 'readme.asciidoc'
]

VALID_DEPENDENCIES = [
    "requirements.txt", "Pipfile", "pyproject.toml", "setup.py",
    "package.json", "pom.xml", "build.gradle", "composer.json",
    "Cargo.toml", "go.mod", "Gemfile"
]

def get_api_url(instance_url=None):
    if not instance_url:
        return GITLAB_DEFAULT_URL
    parsed = urlparse(instance_url)
    return f"{parsed.scheme}://{parsed.netloc}/api/v4"

def format_file_content(file_path, content):
    try:
        if file_path.endswith('.json'):
            return json.loads(content)
        return content
    except json.JSONDecodeError:
        return content

async def get_project_id(session, base_url, url, headers):
    """Get GitLab project ID from URL"""
    try:
        encoded_url = quote(urlparse(url).path.lstrip('/'), safe='')
        api_url = f"{base_url}/projects/{encoded_url}"
        
        print(f"Fetching project ID from: {api_url}")
        async with session.get(api_url, headers=headers) as response:
            if response.status == 401:
                print("Authentication failed. Please check your GITLAB_TOKEN")
                return None
            elif response.status != 200:
                print(f"API request failed with status {response.status}")
                return None
                
            project_data = await response.json()
            print(f"Successfully fetched project ID: {project_data['id']}")
            return project_data["id"]
            
    except aiohttp.ClientError as e:
        print(f"Network error: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

async def fetch_gitlab_repo_info(session, base_url, project_id, headers):
    async with session.get(f"{base_url}/projects/{project_id}", headers=headers) as response:
        if response.status == 200:
            return await response.json()
        return None

async def get_gitlab_version(session, base_url, project_id, headers):
    async with session.get(f"{base_url}/projects/{project_id}/releases", headers=headers) as response:
        if response.status == 200:
            releases = await response.json()
            if releases:
                return {
                    "build_number": releases[0]["tag_name"],
                    "patch_summary": releases[0]["description"],
                    "published_at": releases[0]["released_at"]
                }
        return None

async def get_gitlab_languages(session, base_url, project_id, headers):
    async with session.get(f"{base_url}/projects/{project_id}/languages", headers=headers) as response:
        if response.status == 200:
            languages = await response.json()
            return list(languages.keys())
        return None

async def get_gitlab_contributors(session, base_url, project_id, headers):
    url_commits = f"{base_url}/projects/{project_id}/repository/commits"
    contributors = {}
    page = 1
    per_page = 100
    max_pages = 3

    while page <= max_pages:
        params = {"page": page, "per_page": per_page}
        async with session.get(url_commits, headers=headers, params=params) as response:
            if response.status == 200:
                commits = await response.json()
                if not commits:
                    break
                for commit in commits:
                    name = commit["author_name"]
                    email = commit["author_email"]
                    if name and email:
                        key = (name, email)
                        if key not in contributors:
                            contributors[key] = {"name": name, "email": email}
                page += 1
            else:
                break

    return [{"author": {"name": data["name"], "email": data["email"]}} 
            for data in contributors.values()[:5]]

async def fetch_gitlab_root_files(session, base_url, project_id, headers):
    url = f"{base_url}/projects/{project_id}/repository/tree"
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        return []

async def fetch_gitlab_file_content(session, base_url, project_id, file_path, headers):
    encoded_file_path = quote(file_path, safe="")
    url = f"{base_url}/projects/{project_id}/repository/files/{encoded_file_path}/raw"
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.text()
        return None

async def get_gitlab_files(session, base_url, project_id, headers):
    root_files = await fetch_gitlab_root_files(session, base_url, project_id, headers)
    
    result = {
        "codemeta": [],
        "dependencies": [],
        "readme": []
    }

    if not root_files:
        return result

    for file in root_files:
        file_path = file["path"].lower()
        category = None
        if file_path in VALID_DEPENDENCIES:
            category = "dependencies"
        elif file_path in VALID_README_NAMES:
            category = "readme"
        elif file_path == "codemeta.json":
            category = "codemeta"

        if category:
            content = await fetch_gitlab_file_content(
                session, base_url, project_id, file["path"], headers)
            if content:
                result[category].append({
                    "path": file["path"],
                    "content": format_file_content(file["path"], content)
                })

    return result

def get_project_id_selenium(url):
    """Get GitLab project ID using Selenium"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Wait for project-id meta tag
        wait = WebDriverWait(driver, 10)
        meta_tag = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[name="project-id"]'))
        )
        
        project_id = meta_tag.get_attribute('content')
        return project_id
        
    except TimeoutException:
        print("Timeout waiting for project ID")
        return None
    except NoSuchElementException:
        print("Could not find project ID element")
        return None
    except Exception as e:
        print(f"Error getting project ID: {e}")
        return None
    finally:
        driver.quit()


async def get_gitlab_repo_info(url, instance_url=None):
    async with aiohttp.ClientSession() as session:
        print(f"Using token: {GITLAB_TOKEN[:4]}..." if GITLAB_TOKEN else "No token found")
        headers = {
            "PRIVATE-TOKEN": GITLAB_TOKEN,
            "Accept": "application/json"
        }

        base_url = get_api_url(instance_url)
        project_id = await get_project_id(session, base_url, url, headers)
        if not project_id:
            return None

        repo_info, latest_version, languages, other_metadata, contributors = await asyncio.gather(
            fetch_gitlab_repo_info(session, base_url, project_id, headers),
            get_gitlab_version(session, base_url, project_id, headers),
            get_gitlab_languages(session, base_url, project_id, headers),
            get_gitlab_files(session, base_url, project_id, headers),
            get_gitlab_contributors(session, base_url, project_id, headers)
        )

        if repo_info:
            return {
                "name": repo_info["name"],
                "description": repo_info["description"],
                "url": repo_info["web_url"],
                "license": repo_info.get("license", {}).get("name"),
                "latest_version": latest_version,
                "topics": repo_info.get("topics", []),
                "languages": languages,
                "other_metadata": other_metadata,
                "contributors": contributors
            }
        return None

def extract_instance_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

async def get_gitlab_repo_info_main(url):
    instance_url = extract_instance_url(url) if "gitlab.com" not in url else None
    return await get_gitlab_repo_info(url, instance_url)


print(asyncio.run(get_gitlab_repo_info_main("https://gitlab.jsc.fz-juelich.de/CoE-RAISE/FZJ/ai4hpc/ai4hpc")))
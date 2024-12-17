import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")

url = 'https://github.com/OpenEnergyPlatform/oeplatform'

BASE_URL = "https://api.github.com/repos"

# Get repo information asynchronously
async def get_repo_info(url):
    full_name = get_full_name(url)
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with aiohttp.ClientSession() as session:
        repo_info, latest_version, languages, other_metadata, contributors = await asyncio.gather(
            fetch_repo_info(session, full_name, headers),
            get_version(session, full_name, headers),
            get_repo_languages(session, full_name, headers),
            get_repo_files(session, BASE_URL, full_name, headers),
            get_contributors(session, full_name, headers)
        )

        if repo_info:
            data = {
                "name": repo_info["name"],
                "description": repo_info["description"],
                "url": repo_info["html_url"],
                "license": repo_info["license"]["name"] if repo_info["license"] else None,
                "latest_version": latest_version,
                "topics": repo_info.get("topics", []),
                "languages": languages,
                "other_metadata": other_metadata,
                "contributors": contributors
            }
            return data
        else:
            print(f"Failed to fetch {url}")
            return None

async def fetch_repo_info(session, full_name, headers):
    async with session.get(f"{BASE_URL}/{full_name}", headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Failed to fetch repo info: {response.status}")
            return None

# Get latest release data asynchronously
async def get_version(session, full_name, headers):
    async with session.get(f"{BASE_URL}/{full_name}/releases", headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            if data:
                latest_release_data = {
                    "build_number": data[0]["tag_name"],
                    "patch_summary": data[0]["body"],
                    "published_at": data[0]["published_at"],
                }
                return latest_release_data
    return ""

async def get_repo_languages(session, full_name, headers):
    """Fetches the programming languages used in the specified GitHub repository."""
    async with session.get(f"{BASE_URL}/{full_name}/languages", headers=headers) as response:
        if response.status == 200:
            languages = await response.json()
            if languages:
                return list(languages.keys())
        else:
            print(f"Error fetching languages: {response.status}")
        return None

async def get_contributors(session, full_name, headers):
    """Fetches up to the top 5 unique contributors' names and emails from the commits endpoint."""
    url_commits = f"{BASE_URL}/{full_name}/commits"
    contributors = {}
    page = 1
    max_pages = 3  # Limit to first 3 pages
    per_page = 100

    while page <= max_pages:
        params = {"page": page, "per_page": per_page}
        async with session.get(url_commits, headers=headers, params=params) as response:
            if response.status == 200:
                commits = await response.json()
                if not commits:
                    break
                for commit in commits:
                    author_info = commit.get("commit", {}).get("author", {})
                    name = author_info.get("name")
                    email = author_info.get("email")
                    if name and email:
                        key = (name, email)
                        if key not in contributors:
                            contributors[key] = {
                                "name": name,
                                "email": email
                            }
                page += 1
            else:
                print(f"Error fetching commits: {response.status}")
                break

    # Get the top 5 contributors
    top_contributors = list(contributors.values())[:5]
    return [{"author": {"name": data["name"], "email": data["email"]}} for data in top_contributors]

async def fetch_user_details(session, login, headers):
    """Fetch user details (name and email) for a given login."""
    url_user = f"{BASE_URL}/users/{login}"
    try:
        async with session.get(url_user, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error fetching user {login}: {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching user {login}: {e}")
        return None

def get_full_name(repo_url):
    """Extract the full repository name from a GitHub URL."""
    if not repo_url.startswith("https://github.com/"):
        return None

    parts = repo_url.split("https://github.com/")[1].split("/")
    if len(parts) < 2:
        return None

    return f"{parts[0]}/{parts[1]}".strip()

VALID_README_NAMES = [
    'readme.md', 'readme.markdown', 'readme.txt',
    'readme', 'readme.rst', 'readme.html',
    'readme.adoc', 'readme.asciidoc'
]

VALID_DEPENDENCIES = [
    "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "Gemfile", "package.json",
    "pom.xml", "build.gradle", "go.mod", "composer.json", "Cargo.toml", "vcpkg.json", "conanfile.txt",
    "CMakeLists.txt", "Spack.yaml", ".csproj", "packages.config", "Package.swift", "Podfile", "pubspec.yaml",
    "DESCRIPTION", "mix.exs", "install.sh", "bootstrap.sh", "cpanfile", "Makefile.PL", "Build.PL", "stack.yaml",
    "cabal.project", "rebar.config", "Project.toml", "Manifest.toml", "build.sbt"
]

async def fetch_file_content_async(session, download_url, headers):
    """Asynchronously fetch the content of a file given its download URL."""
    try:
        async with session.get(download_url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Failed to fetch content from {download_url}: {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching file content: {e}")
        return None

async def fetch_root_files_async(session, base_url, repo_full_name, headers):
    """Fetch the root level files of a repository asynchronously."""
    try:
        async with session.get(f"{base_url}/{repo_full_name}/contents", headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch root files: {response.status}")
                return []
    except Exception as e:
        print(f"An error occurred while fetching the root files: {e}")
        return []

def process_root_files(root_files):
    """Process root files to find paths for dependencies, README, and codemeta files."""
    file_paths = {"dependencies": [], "readme": [], "codemeta": []}

    for file in root_files:
        file_path = file["path"].lower()
        if file_path in VALID_DEPENDENCIES:
            file_paths["dependencies"].append(file)
        elif file_path in VALID_README_NAMES:
            file_paths["readme"].append(file)
        elif file_path == "codemeta.json":
            file_paths["codemeta"].append(file)

    return file_paths

def format_json_content(content):
    """Format JSON content to be pretty-printed."""
    try:
        return json.dumps(json.loads(content), indent=2)
    except json.JSONDecodeError:
        return content

def format_markdown_content(content):
    """
    Format Markdown content by cleaning up special characters while preserving markdown structure.
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
        '\r\n': '\n',       # Windows line endings
        '\r': '\n',         # Old Mac line endings
        '\t': '    ',       # Convert tabs to spaces
        '\u200b': '',       # Zero width space
        '\u200c': '',       # Zero width non-joiner
        '\ufeff': ''        # BOM
    }
    
    # Replace special characters
    cleaned = content
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    # Normalize line endings while preserving table formatting
    lines = cleaned.splitlines()
    cleaned_lines = []
    for line in lines:
        # Preserve table alignment spaces
        if '|' in line:
            cleaned_lines.append(line)
        else:
            cleaned_lines.append(line.rstrip())
    
    cleaned = '\n'.join(cleaned_lines)
    
    # Ensure single newline at end
    cleaned = cleaned.strip() + '\n'
    
    return cleaned

def format_dependency_content(content):
    """Format dependency file content by stripping unnecessary whitespace."""
    return content.strip()

def format_file_content(file_path, content):
    """Format the content of a file based on its type."""
    if file_path.endswith(".json"):
        return format_json_content(content)
    elif file_path.endswith((".md", ".markdown", ".txt", ".rst", ".html", ".adoc", ".asciidoc")):
        return format_markdown_content(content)
    elif file_path in VALID_DEPENDENCIES:
        return format_dependency_content(content)
    else:
        return content

async def get_repo_files(session, base_url, repo_full_name, headers):
    root_files = await fetch_root_files_async(session, base_url, repo_full_name, headers)

    if not root_files:
        print("Root files are empty")
        return None

    file_paths = process_root_files(root_files)

    if not file_paths:
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
                fetch_file_content_async(session, file["download_url"], headers) for file in files
            ])
            result[category] = [
                {"path": file["path"], "content": format_file_content(file["path"], content)}
                for file, content in zip(files, file_contents)
                if content
            ]

    return result

# Example usage:
print(asyncio.run(get_repo_info(url)))
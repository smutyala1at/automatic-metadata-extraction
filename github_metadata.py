import requests
import re

# url = input('Enter the URL: ')
# GITHUB_TOKEN = input('Enter the personal token: ')
url = 'https://github.com/OpenEnergyPlatform/oeplatform'
GITHUB_TOKEN = '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'
url_parts = url.split("/")

get_owner_or_organization = url_parts[3]
get_repo = url_parts[4]

BASE_URL = "https://api.github.com/repos"

# get repo information
def get_repo_info(url):

    full_name = get_full_name(url)
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
        }
    
    print(get_repo_files(BASE_URL, full_name, headers))
    
    response = requests.get(
        f"{BASE_URL}/{full_name}",
        headers = headers
    )

    if response.status_code == 200:
        repo_info = response.json()
        data = {
            "name": repo_info["name"],
            "description": repo_info["description"],
            "url": repo_info["html_url"],
            "license":repo_info["license"]["name"],
            "latest_version": get_version(full_name, headers),
            "topics": repo_info["topics"],
            "languages": get_repo_languages(full_name, headers),
            # "contributors": get_repo_contributors(full_name, headers),
        }
        return data
    else:
        print(f"Failed to fetch {url}: Status {response.status_code}")
        print(f"Response: {response.text}")
        return None

# get latest release data
def get_version(full_name, headers):

    response = requests.get(
        f"{BASE_URL}/{full_name}/releases",
        headers = headers
    )

    if response.status_code == 200:
        data = response.json()[0]
        latest_release_data = {
            "build_number": data["tag_name"],
            "patch_summary": data["body"],
            "publised_at": data["published_at"],
        }
        return latest_release_data
    else:
        return ""
    


def get_repo_languages(full_name, headers):
    """Fetches the programming languages used in the specified GitHub repository."""
    
    response = requests.get(
        f"{BASE_URL}/{full_name}/languages", 
        headers= headers
    )

    if response.status_code == 200:
        languages = response.json()
        if languages:
            return list(languages.keys())
    else:
        print(f"Error fetching languages: {response.status_code} - {response.json()}")
        return None


def get_repo_contributors(full_name, headers):

    url = f"{BASE_URL}/{full_name}/commits"
    
    params = {
        "per_page": 100,
        "page": 1
    }

    contributors = {}
    
    while True:
        response = requests.get(
            url,
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            commit_data = response.json()
            contributors = parse_data(commit_data, contributors)

            if len(commit_data) < 100:
                break
            else:
                params["page"] += 1
        
        else:
            print(f"Error fetching contributors: {response.status_code} - {response.json()}")
            break

    sorted_contributors = sorted(contributors.values(), key=lambda item:item["contributions"], reverse=True)
    return sorted_contributors


def parse_data(data, contributors):

    # if data is empty return an empty list
    if not data:
        return []
    
    else:
        for commit in data:
            contributor = commit["commit"]["author"]
            contributor_name = contributor["name"]
            contributor_email = contributor["email"]

            contributor_info = {
                "name": contributor_name,
                "email": contributor_email,
                "contributions": 1
            }

            if contributor_email in contributors:
                contributors[contributor_email]["contributions"] =  contributors[contributor_email].get("contributions", 0) + 1
            else:
                contributors[contributor_email] = contributor_info

        return contributors
    


def get_full_name(repo_url):
    """Extract the full repository name from a GitHub URL."""
    if not repo_url.startswith("https://github.com/"):
        return None

    parts = repo_url.split("https://github.com/")[1].split("/")
    if len(parts) < 2:
        return None
    
    parts = [part for part in parts]

    return f"{parts[0]}/{parts[1]}".strip()
    

VALID_README_NAMES = [
    'readme.md', 'readme.markdown', 'readme.txt',
    'readme', 'readme.rst', 'readme.html',
    'readme.adoc', 'readme.asciidoc'
]


# List of dependency-related files and lock files
VALID_DEPENDENCIES = [
    "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "Gemfile", "package.json",
    "pom.xml", "build.gradle", "go.mod", "composer.json", "Cargo.toml", "vcpkg.json", "conanfile.txt",
    "CMakeLists.txt", "Spack.yaml", ".csproj", "packages.config", "Package.swift", "Podfile", "pubspec.yaml",
    "DESCRIPTION", "mix.exs", "install.sh", "bootstrap.sh", "cpanfile", "Makefile.PL", "Build.PL", "stack.yaml",
    "cabal.project", "rebar.config", "Project.toml", "Manifest.toml", "build.sbt"
]

def get_method(url):
    res = requests.get(url)

    if res.status_code == 200:
        return res.json()

# Initialization and calling the function
codemeta = {"files": []}
readme = {"files": []}
dependencies = {"files": []}
    
def fetch_file_tree(base_url, repo_full_name, headers):
    """
    Fetch the recursive file tree of a repository.
    """
    try:
        # Step 1: Get default branch and tree SHA
        repo_details = requests.get(f"{base_url}/{repo_full_name}", headers=headers).json()
        print(f"{base_url}/{repo_full_name}")
        default_branch = repo_details.get("default_branch")

        branch_details = requests.get(f"{base_url}/{repo_full_name}/branches/{default_branch}", headers=headers).json()
        tree_sha = branch_details.get("commit").get("commit").get("tree").get("sha")

        # Step 2: Fetch the recursive tree
        tree_response = requests.get(f"{base_url}/{repo_full_name}/git/trees/{tree_sha}?recursive=true", headers=headers)

        if tree_response.status_code == 200:
            return tree_response.json().get("tree")
        else:
            print(f"Failed to fetch tree: {tree_response.status_code}")
            return []

    except Exception as e:
        print(f"An error occurred while fetching the file tree: {e}")
        return []

def process_tree(file_tree):
    """
    Process the file tree to find paths for dependencies, README, and codemeta files.
    """
    file_paths = {"dependencies": [], "readme": [], "codemeta": []}

    for file in file_tree:
        file_path = file["path"].lower().split("/")
        if file_path[0] in VALID_DEPENDENCIES or file_path[-1] in VALID_DEPENDENCIES:
            file_paths["dependencies"].append(file["path"])
        elif not file_paths["readme"] and (file_path[0] in VALID_README_NAMES or file_path[-1] in VALID_README_NAMES):
            file_paths["readme"].append(file["path"])
        elif file["path"] == "codemeta.json":
            file_paths["codemeta"].append(file["path"])

    return file_paths

def fetch_file_content(base_url, repo_full_name, file_path, headers):
    """
    Fetch the content of a file given its path.
    """
    try:
        file_url = f"{base_url}/{repo_full_name}/contents/{file_path}"
        response = requests.get(file_url, headers=headers)

        if response.status_code == 200:
            content = response.json().get("content")
            return content 
        else:
            print(f"Failed to fetch content for {file_path}: {response.status_code}")
            return None

    except Exception as e:
        print(f"An error occurred while fetching file content: {e}")
        return None

def get_repo_files(base_url, repo_full_name, headers):
    """
    Fetch file paths for dependencies, README, and codemeta files.
    """
    file_tree = fetch_file_tree(base_url, repo_full_name, headers)
    if not file_tree:
        print("File tree is empty")
        return None

    file_paths = process_tree(file_tree)

    if file_paths:
        for category in file_paths:
            for file_path in file_paths[category]:
                content = fetch_file_content(base_url, repo_full_name, file_path, headers)
                if content:
                    print(f"Content of {file_path}:")
                    print(content)
                else:
                    print(f"Failed to fetch content for {file_path}")
    else:
        print("No relevant files found")



data = get_repo_info(url)

""" if data:
    print(data)
 """



# some readmes might contain authors in readmes, also in dependencies for weird reasons!
# use llm to first summarize readme for installation process or link(any of it), keywords, authors, maintainers(if mentioned)
# use llm to get authors, maintainers from dependencies, sometimes it is case, toml files can have authors, maintainers
# try to move to go because of goroutines, then api calling is async, maybe python as it as well

# toml, xml, 

# what is most important at first?
# ["name", "description", "url", "license", "latest_version", "topics", "languages", "readme", "codemeta", "dependencies"]
# from readme get installation process or link if found, and keywords
# dependencies
# if codemeta found, get authors, contributors, id, or represent each attribute of it on frontend


# from readme, dependencies, codemeta ask llm to get installation, keywords, dependencies, authors, contributors, developers, maintainer, funder, doi
# datecreated, published from rest api
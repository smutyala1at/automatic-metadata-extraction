import os
import requests

# Base URLs for GitLab API
GITLAB_BASE_URL = "https://gitlab.com/api/v4/projects"

# List of dependency-related files and lock files
VALID_DEPENDENCIES = [
    "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "Gemfile", "package.json",
    "pom.xml", "build.gradle", "go.mod", "composer.json", "Cargo.toml", "vcpkg.json", "conanfile.txt",
    "CMakeLists.txt", "Spack.yaml", ".csproj", "packages.config", "Package.swift", "Podfile", "pubspec.yaml",
    "DESCRIPTION", "mix.exs", "install.sh", "bootstrap.sh", "cpanfile", "Makefile.PL", "Build.PL", "stack.yaml",
    "cabal.project", "rebar.config", "Project.toml", "Manifest.toml", "build.sbt"
]

VALID_README_NAMES = [
    'readme.md', 'readme.markdown', 'readme.txt',
    'readme', 'readme.rst', 'readme.html',
    'readme.adoc', 'readme.asciidoc'
]

# Get repository information using project ID
def get_gitlab_repo_info(project_id):
    headers = {
        "Authorization": f"Bearer {os.getenv('GITLAB_TOKEN')}"
    }

    repo_info = requests.get(f"{GITLAB_BASE_URL}/{project_id}", headers=headers)

    if repo_info.status_code == 200:
        repo_data = repo_info.json()
        data = {
            "name": repo_data["name"],
            "description": repo_data["description"],
            "url": repo_data["web_url"],
            "license": repo_data.get("license", {}).get("name"),
            "latest_version": get_gitlab_latest_release(project_id, headers),
            "topics": repo_data.get("topics", []),
            "languages": get_gitlab_languages(project_id, headers),
        }
        return data
    else:
        print(f"Failed to fetch project {project_id}: Status {repo_info.status_code}")
        print(f"Response: {repo_info.text}")
        return None

# Get latest release data
def get_gitlab_latest_release(project_id, headers):
    response = requests.get(f"{GITLAB_BASE_URL}/{project_id}/releases", headers=headers)

    if response.status_code == 200 and response.json():
        data = response.json()[0]
        latest_release_data = {
            "build_number": data["tag_name"],
            "patch_summary": data["description"],
            "published_at": data["released_at"],
        }
        return latest_release_data
    else:
        return ""

# Get languages used in the repository
def get_gitlab_languages(project_id, headers):
    response = requests.get(f"{GITLAB_BASE_URL}/{project_id}/languages", headers=headers)

    if response.status_code == 200:
        languages = response.json()
        return list(languages.keys())
    else:
        print(f"Error fetching languages: {response.status_code} - {response.text}")
        return None

# Fetch file tree
def fetch_gitlab_file_tree(project_id, headers):
    try:
        response = requests.get(f"{GITLAB_BASE_URL}/{project_id}/repository/tree?recursive=true", headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch file tree: {response.status_code}")
            return []
    except Exception as e:
        print(f"An error occurred while fetching the file tree: {e}")
        return []

# Process file tree
def process_gitlab_tree(file_tree):
    file_paths = {"dependencies": [], "readme": [], "codemeta": []}

    for file in file_tree:
        file_path = file["path"].lower()
        if file_path.split("/")[-1] in VALID_DEPENDENCIES:
            file_paths["dependencies"].append(file["path"])
        elif file_path.split("/")[-1] in VALID_README_NAMES:
            file_paths["readme"].append(file["path"])
        elif file["path"] == "codemeta.json":
            file_paths["codemeta"].append(file["path"])

    return file_paths

# Fetch file content
def fetch_gitlab_file_content(project_id, file_path, headers):
    try:
        file_url = f"{GITLAB_BASE_URL}/{project_id}/repository/files/{file_path.replace('/', '%2F')}/raw"
        response = requests.get(file_url, headers=headers)

        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch content for {file_path}: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching file content: {e}")
        return None

# Get repository files
def get_gitlab_repo_files(project_id, headers):
    file_tree = fetch_gitlab_file_tree(project_id, headers)
    if not file_tree:
        print("File tree is empty")
        return None

    file_paths = process_gitlab_tree(file_tree)
    files_with_content = []

    if file_paths:
        for category, paths in file_paths.items():
            for file_path in paths:
                content = fetch_gitlab_file_content(project_id, file_path, headers)
                if content:
                    files_with_content.append({"category": category, "path": file_path, "content": content})
                else:
                    print(f"Failed to fetch content for {file_path}")
    else:
        print("No relevant files found")
        return []

    return files_with_content

# Example usage
project_id = '60534780'  # Replace with your GitLab project ID
data = get_gitlab_repo_info(project_id)
print(data)

headers = {
        "Authorization": f"Bearer {os.getenv('GITLAB_TOKEN')}"
}
print(get_gitlab_repo_files(project_id, headers))
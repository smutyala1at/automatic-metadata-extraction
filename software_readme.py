import base64
import json
import requests
from scraper import GITHUB_HEADERS, GITLAB_HEADERS, clean_readme
from selenium_scraping import get_gitlab_project_id

def get_gitlab_readme_content(gitlab_instance_url, project_id):
    url = f"{gitlab_instance_url}/api/v4/projects/{project_id}/repository/tree"
    response = requests.get(url, GITLAB_HEADERS)

    if response.status_code == 200:
        files = response.json()

        for file in files:
            if file['name'] == 'README.md':
                file_url = file['url']
                response = requests.get(file_url, GITLAB_HEADERS)

                if response.status_code == 200:
                    file_content_base64 = response.json()['content']
                    file_content = base64.b64decode(file_content_base64).decode('utf-8')
                    return file_content

        return None  # README not found

    else:
        print(f"Error fetching repository tree: {response.status_code}")
        return None

def get_github_readme_content(repo_full_name):
    contents_url = f"https://api.github.com/repos/{repo_full_name}/contents"
    response = requests.get(contents_url, headers=GITHUB_HEADERS)
    if response.status_code == 200:
        contents = response.json()
        for file in contents:
            if file['name'].lower() == 'readme.md':  # Look for README.md
                readme_response = requests.get(file['download_url'], headers=GITHUB_HEADERS)
                if readme_response.status_code == 200:
                    return clean_readme(readme_response.text) # clean the readme
                else:
                    raise Exception(f"Failed to fetch README: {readme_response.status_code}")
    else:
        raise Exception(f"Failed to fetch contents: {response.status_code} {response.text}")
    return None  # return None if no readme is found in the repo

def get_full_name(url):

    if not url.startswith("https://github.com/"):
        return None

    full_name = url.split("https://github.com/")[1]

    if len(full_name.split("/")) < 2:
        return None
    
    return full_name


with open("./files/software_pages.json", "r", encoding="utf-8") as rf:
    objs = json.load(rf)["final_links"]

    for count, obj in enumerate(objs):
        repo_link = obj["repo_link"]

        if not repo_link:
            continue

        domain = repo_link.split("/")[2]

        if domain == "github.com":
            repo_full_name = get_full_name(repo_link)
            
            if not repo_full_name:
                obj["readme"] = ""
                continue
            else:
                readme = get_github_readme_content(repo_full_name)
                if not readme:
                    obj["readme"] = ""
                else:
                    obj["readme"] = readme
            
        else:
            project_id = get_gitlab_project_id(repo_link)

            if not project_id:
                obj["project_id"] = ""
                obj["readme"] = ""
            else:
                gitlab_instance_url = repo_link.split("/")[2]
                readme = get_gitlab_readme_content(gitlab_instance_url, project_id)

                if not readme:
                    obj["project_id"] = ""
                    obj["readme"] = ""
                else:
                    obj["project_id"] = project_id
                    obj["readme"] = readme
    
    with open("./files/software_pages.json", "w", encoding="utf-8") as wf:
        json.dump(objs, wf, ensure_ascii=False, indent=4)


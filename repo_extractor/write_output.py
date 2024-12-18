import json
import asyncio
import aiohttp
import os
from urllib.parse import urlparse
from gitlab_extractor import get_gitlab_repo_data
from github_extractor import get_repo_info

async def process_repos():
    # Load input JSON
    input_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../files/software_pages.json'))
    with open(input_file_path, 'r') as f:
        data = json.load(f)

    results = []
    
    # Process each repository
    for item in data['final_links']:
        repo_link = item['repo_link']

        if not repo_link:
                results.append({
                    "software_organization": item["software_organization"],
                    "repo_link": repo_link,
                    "metadata": ""
                })
                continue
        
        domain = repo_link.split("/")[2]
        
        try:
            if domain == "github.com":
                repo_data = await get_repo_info(repo_link)
            else:
                repo_data = await get_gitlab_repo_data(repo_link)
                
            if repo_data:
                results.append({
                    "software_organization": item["software_organization"],
                    "repo_link": repo_link,
                    "metadata": repo_data
                })
            
        except Exception as e:
            print(f"Error processing {repo_link}: {str(e)}")
            continue

    # Write results to new JSON file
    with open('repository_metadata.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(process_repos())
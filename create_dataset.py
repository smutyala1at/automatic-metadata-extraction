import pandas as pd
import json
from blablador import Models, ChatCompletions
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

def createDataset(file_path):
    # Read JSON file
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # List to store all content
    all_content = []
    
    # Process each repository
    for repo in data:
        # Skip if no metadata or other_metadata
        if not repo.get('metadata') or not repo['metadata'].get('other_metadata'):
            continue
            
        other_metadata = repo['metadata']['other_metadata']
        
        # Process each category (codemeta, dependencies, readme)
        for category in ['codemeta', 'dependencies', 'readme']:
            # Get list of items in this category
            items = other_metadata.get(category, [])
            
            # Extract content from each item
            for item in items:
                if isinstance(item, dict) and 'content' in item:
                    all_content.append({
                        'software_organization': repo['software_organization'],
                        'repo_link': repo['repo_link'],
                        'category': category,
                        'content': item['content']
                    })
    
    # Create DataFrame
    if all_content:
        return pd.DataFrame(all_content)
    else:
        return pd.DataFrame(columns=['software_organization', 'repo_link', 'category', 'content'])

# Usage
#df = createDataset('repository_metadata.json')
#print(df.head())
#df.to_csv('metadata_dataset.csv', index=False)

async def update_csv_with_api_responses(csv_file_path):
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Add new columns if they don't exist
    if 'api_response' not in df.columns:
        df['api_response'] = None
    if 'input' not in df.columns:
        df['input'] = None

    models = await Models(api_key=API_KEY).get_model_ids()
    completion = ChatCompletions(api_key=API_KEY, model=models[4])
    
    # Process each row
    for index, row in df.iterrows():
        try:
            content = row['content']
            prompt = f"""You are a highly sophisticated metadata extraction and analysis system. Your task is to perform deep content analysis and extract comprehensive, accurate information with a focus on software-related metadata.

                For the following content, perform detailed extraction of these elements when EXPLICITLY MENTIONED:

                1. Dependencies: List ALL package names, versions, and requirements with exact specifications
                2. Installation: Full installation procedure including prerequisites, commands, and environment setup
                3. Authors: Complete author information including names, affiliations, roles, and contact details
                4. Contributors: Comprehensive list of contributors with roles, responsibilities, and contributions
                5. Funding: Complete funding information including grant numbers, organizations, and acknowledgments
                6. DOI: All DOI identifiers, including related publications and datasets
                7. License: Complete license information including version, terms, and any special conditions
                8. Keywords: Extract 10 highly relevant technical keywords, focusing on:
                   - Technology stack and frameworks
                   - Programming languages
                   - Scientific domains
                   - Core functionalities
                   - Technical specifications

                Strict Rules:
                - Extract ONLY explicitly stated information - no inferences
                - Maintain complete accuracy in technical terms
                - Preserve all version numbers and specifications exactly as stated
                - Include ALL relevant technical details from the source
                - Keywords must be specific and technically precise
                - Capture complete context for each extracted element
                - Omit any field where information isn't explicitly present

                Content: {content}

                Return strictly formatted JSON:
                {{
                    "Dependencies": [
                        // Include full dependency specifications
                        // Example: {{"name": "numpy", "version": ">=1.19.2", "requirement_type": "required"}}
                    ],
                    "Installation_Instructions": "",
                    "Authors": [
                        // Include all available author details
                        // Example: {{"name": "", "affiliation": "", "email": "", "role": ""}}
                    ],
                    "Contributors": [
                        // Include all available contributor details
                        // Example: {{"name": "", "role": "", "contribution": ""}}
                    ],
                    "Funding": "",
                    "DOI": "",
                    "License": "",
                    "Keywords": []
                }}"""


            # Store input message
            df.at[index, 'input'] = json.dumps({"role": "user", "content": content})
            response = await completion.get_completion([{"role": "user", "content": prompt}])

            if not response:
                df.at[index, 'api_response'] = ""
                print("no response")
                continue

            if response:
                try:
                    response_data = json.loads(response)  

                    if response_data["object"] == "error":
                        df.at[index, 'api_response'] = ""
                    else:
                        df.at[index, 'api_response'] = response_data["choices"][0]["message"]
                        print(response_data["choices"][0]["message"])
                        print(f"Processed row {index}")
                except json.JSONDecodeError:
                    print(f"Failed to decode response: {response}")
                    df.at[index, 'api_response'] = ""
            
        except Exception as e:
            print(f"Error processing row {index}: {e}")
    
    df.to_csv(csv_file_path, index=False)
    return df


# Call the function with the metadata_dataset.csv file
updated_df = asyncio.run(update_csv_with_api_responses('metadata_dataset.csv'))
print("CSV file has been updated with API responses")

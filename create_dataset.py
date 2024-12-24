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
    print(models)
    print(models[4])
    completion = ChatCompletions(api_key=API_KEY, model=models[4])
    
    # Process each row
    for index, row in df.iterrows():
        try:
            content = row['content']
            prompt = f"""
            You are an advanced, award-winning metadata extraction system specializing in software-related metadata. Your unparalleled expertise enables you to accurately analyze and extract information with exceptional precision. You possess a deep understanding of programming languages, frameworks, dependencies, licenses, installation processes, authorship, funding sources, DOI identifiers, and all technical aspects related to software development. Your capabilities have been recognized globally, earning accolades for your exceptional ability to extract highly accurate metadata from complex software documentation.

            Perform detailed extraction of the following elements when EXPLICITLY MENTIONED:
            1. Dependencies:
            - List all package names, versions, and requirements with exact specifications.
            - Include only explicitly mentioned dependencies from the documentation.

            2. Installation Instructions:
            - Provide the full installation procedure if and only if complete instructions are available.
            - If an installation-related file (e.g., `install.md`, `setup.py`) is mentioned, include its name.
            - Do not fabricate or infer instructions if they are incomplete or missing.

            3. Authors:
            - Extract complete author information, including names, affiliations, roles, and contact details, as explicitly stated.

            4. Contributors:
            - Provide a comprehensive list of contributors with their roles, responsibilities, and contributions as mentioned in the documentation.

            5. Funding:
            - Include all funding information such as grant numbers, funding organizations, and acknowledgments as explicitly stated.

            6. DOI:
            - List all DOI identifiers, including those for related publications, datasets, or other relevant resources.

            7. License:
            - Provide complete license information, including the license name, version, terms, and any special conditions as stated in the documentation.

            8. Keywords:
            - Extract precise and informative keywords that:
                - Describe the core purpose and objectives of the software.
                - Highlight key technologies and methods used.
                - Specify the problem domains being addressed.
                - Indicate performance or quality aspects.
                - Capture unique or innovative approaches or features.
            - Avoid including irrelevant, generic, or dependency-related terms.

            Strict Rules:
            - Do not include unrelated or fabricated information.
            - Avoid misinterpreting or making assumptions about the content.
            - Maintain complete accuracy in technical terms.
            - Preserve all version numbers and specifications exactly as stated.
            - Include ALL relevant technical details from the source.
            - Keywords must be specific and technically precise.
            - Capture complete context for each extracted element.
            - Omit any subfields if information isn't available.
            - Check ALL content thoroughly before returning empty fields.
            - All keys and string values must be enclosed in double quotes ("").
            - The JSON dictionary must be returned in a SINGLE LINE with no newlines, extra spaces, or indentation.
            - Empty fields must be represented as an empty string ("") or an empty list ([]).
            - Ensure the JSON is valid and parsable without any errors.

            {{"Dependencies": [ # Only include fields with actual values
                        # Example: If only name is available: ["R"]
                        # If both name and version are available: ["R: >= 4.0.0"]
                        "R: >= 4.0.0", "grid", "Rcpp", "methods", "colorRamp2"], 
                "Installation_Instructions": "", 
                "Authors": [ # Only include fields with actual values
                        # Example: If only name is available: {{"name": "Zuguang Gu"}}
                        # If more details are available: {{"name": "Zuguang Gu", "email": "z.gu@dkfz.de", "role": "aut, cre", "ORCID": "0000-0002-7395-8709"}}
                    ], 
                "Contributors": [], 
                "Funding": "", 
                "DOI": "", 
                "License": "MIT", 
                "Keywords": [# Example keywords from actual data:"space-filling-curves", "Hilbert-curve", "Peano-curve", "H-curve", "three-dimensional-Hilbert-curve", "Rcpp", "R"]
            }}
            
            Content: {content}
            """
            
            # System prompt (behavior instructions)
            system_prompt = """
            You are an advanced, award-winning metadata extraction system specializing in software-related metadata. Your unparalleled expertise enables you to accurately analyze and extract information with exceptional precision. You possess a deep understanding of programming languages, frameworks, dependencies, licenses, installation processes, authorship, funding sources, DOI identifiers, and all technical aspects related to software development. Your capabilities have been recognized globally, earning accolades for your exceptional ability to extract highly accurate metadata from complex software documentation.

            Perform detailed extraction of the following elements when EXPLICITLY MENTIONED:
            1. Dependencies:
            - List all package names, versions, and requirements with exact specifications.
            - Include only explicitly mentioned dependencies from the documentation.

            2. Installation Instructions:
            - Provide the full installation procedure if and only if complete instructions are available.
            - If an installation-related file (e.g., `install.md`, `setup.py`) is mentioned, include its name.
            - Do not fabricate or infer instructions if they are incomplete or missing.

            3. Authors:
            - Extract complete author information, including names, affiliations, roles, and contact details, as explicitly stated.

            4. Contributors:
            - Provide a comprehensive list of contributors with their roles, responsibilities, and contributions as mentioned in the documentation.

            5. Funding:
            - Include all funding information such as grant numbers, funding organizations, and acknowledgments as explicitly stated.

            6. DOI:
            - List all DOI identifiers, including those for related publications, datasets, or other relevant resources.

            7. License:
            - Provide complete license information, including the license name, version, terms, and any special conditions as stated in the documentation.

            8. Keywords:
            - Extract precise and informative keywords that:
                - Describe the core purpose and objectives of the software.
                - Highlight key technologies and methods used.
                - Specify the problem domains being addressed.
                - Indicate performance or quality aspects.
                - Capture unique or innovative approaches or features.
            - Avoid including irrelevant, generic, or dependency-related terms.

            Strict Rules:
            - Do not include unrelated or fabricated information.
            - Avoid misinterpreting or making assumptions about the content.
            - Maintain complete accuracy in technical terms.
            - Preserve all version numbers and specifications exactly as stated.
            - Include ALL relevant technical details from the source.
            - Keywords must be specific and technically precise.
            - Capture complete context for each extracted element.
            - Omit any subfields if information isn't available.
            - Check ALL content thoroughly before returning empty fields.
            - All keys and string values must be enclosed in double quotes ("").
            - The JSON dictionary must be returned in a SINGLE LINE with no newlines, extra spaces, or indentation.
            - Empty fields must be represented as an empty string ("") or an empty list ([]).
            - Ensure the JSON is valid and parsable without any errors.


            {{"Dependencies": [ # Only include fields with actual values
                        # Example: If only name is available: ["R"]
                        # If both name and version are available: ["R: >= 4.0.0"]
                        "R: >= 4.0.0", "grid", "Rcpp", "methods", "colorRamp2"], 
                "Installation_Instructions": "", 
                "Authors": [ # Only include fields with actual values
                        # Example: If only name is available: {{"name": "Zuguang Gu"}}
                        # If more details are available: {{"name": "Zuguang Gu", "email": "z.gu@dkfz.de", "role": "aut, cre", "ORCID": "0000-0002-7395-8709"}}
                    ], 
                "Contributors": [], 
                "Funding": "", 
                "DOI": "", 
                "License": "MIT", 
                "Keywords": [# Example keywords from actual data:"space-filling-curves", "Hilbert-curve", "Peano-curve", "H-curve", "three-dimensional-Hilbert-curve", "Rcpp", "R"]
            }}
            """

            # User content (specific input content)
            user_content = f"Content: {row['content']}"

            # Sending to the model
            response = await completion.get_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ])

            df.at[index, 'input'] = json.dumps({"role": "user", "content": content})
           #response = await completion.get_completion([{"role": "user", "content": prompt}])

            if not response:
                df.at[index, 'api_response'] = ""
                df.at[index, 'conversations'] = json.dumps([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}, {"role": "assistant", "content": ""}])
                df.at[index, 'conversations1'] = json.dumps([{"role": "user", "content": prompt}, {"role": "assistant", "content": ""}])
                print("no response")
                continue

            if response:
                try:
                    response_data = json.loads(response)

                    if response_data["object"] == "error":
                        df.at[index, 'api_response'] = ""
                    else:
                        assistant_content = json.loads(response_data["choices"][0]["message"]["content"])
                        df.at[index, 'api_response'] = json.dumps({"role": "assistant", "content": assistant_content})
                        df.at[index, 'conversations'] = json.dumps([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}, {"role": "assistant", "content": assistant_content}])
                        df.at[index, 'conversations1'] = json.dumps([{"role": "user", "content": prompt}, {"role": "assistant", "content": assistant_content}])
                        print(assistant_content)
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

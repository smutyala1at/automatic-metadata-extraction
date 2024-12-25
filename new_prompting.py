import pandas as pd
import json
from blablador import Models, Completions
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")


async def update_csv_with_api_responses(input_csv_path, output_csv_path):
    df = pd.read_csv(input_csv_path)
    
    for index, row in df.iterrows():
        content = "".join(row['content'].splitlines())
        prompt = f"""
        You are an advanced, award-winning metadata extraction system specializing in software-related metadata. Your unparalleled expertise enables you to accurately analyze and extract information with exceptional precision. You possess a deep understanding of programming languages, frameworks, dependencies, licenses, installation processes, authorship, funding sources, DOI identifiers, and all technical aspects related to software development. Your capabilities have been recognized globally, earning accolades for your exceptional ability to extract highly accurate metadata from complex software documentation.

        REQUIRED FIELDS (ONLY IF EXPLICITLY STATED):
        1. Dependencies: Exact package names + versions
        2. Installation: Complete procedure OR referenced files (install.md, setup.py)
        3. Authors: Full details (name, affiliation, role, contact, orcid, etc)
        4. Contributors: Names + specific contributions
        5. Funding: Grant numbers + organizations
        6. DOI: All identifiers (publications, datasets etc)
        7. License: Name, version, terms, conditions
        8. Keywords: Software-specific terms (no generic/dependency terms)

        Strict Rules:  
        - Only include accurate, relevant information directly from the source.  
        - Do not fabricate, assume, or misinterpret content.  
        - Preserve all technical details, including version numbers and specifications, as stated.  
        - Include all available and relevant details; omit subfields only if unavailable.  
        - Use precise and specific keywords.  
        - Maintain complete context for every extracted element.  
        - Format all keys and string values in double quotes ("").  
        - Return the JSON dictionary as a SINGLE LINE without newlines, extra spaces, or indentation.  
        - Represent empty fields as "" or [].  
        - Provide output only in the specified JSON structure, with no added sentences before or after JSON, no explanations, or deviations.  
        - Follow these rules exactly for every entry.  

        OUTPUT STRUCTURE:
        {{
            "Dependencies": [
                # Format examples:
                # Name only: ["package-name"]
                # With version: ["package-name: >=version"]
                # Multiple packages: ["pkg1: >=1.0", "pkg2", "pkg3: ^2.0"]
            ],
            "Installation_Instructions": "",  # Steps or referenced files
            "Authors": [
            # Include only available information:
            # If just name: {{"name": "Author"}}
            # Add other fields only if explicitly stated in the text
            ],
            "Contributors": [
                # Include only available information:
                # If just name and role: {{"name": "Name", "type": "maintainer"}}
                # Add other fields only if explicitly stated in the text
            ],
            "Funding": "",    # Complete grant/funding details
            "DOI": "",       # Complete DOI string
            "License": "",   # Complete license information
            "Keywords": []   # Specific technical terms only
        }}

        IMPORTANT: Never use example values as actual data.
        """

        lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        prompt = "".join(lines) + "\n" + f"content: {content}"

        df.at[index, 'prompt'] = prompt

    df.to_csv(output_csv_path, index=False)

# Call the function with the metadata_dataset.csv file
input_file = 'metadata_dataset.csv'
output_file = 'processed_metadata.csv'
updated_df = asyncio.run(update_csv_with_api_responses(input_file, output_file))
print(f"Results saved to {output_file}")

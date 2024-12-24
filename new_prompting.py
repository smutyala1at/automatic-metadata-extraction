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
        content="".join(row['content'].split())
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
        \\n
        Content: {content}
        """

        lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        prompt = " ".join(lines)
        print(prompt)

        df.at[index, 'prompt'] = prompt

    df.to_csv(output_csv_path, index=False)

# Call the function with the metadata_dataset.csv file
input_file = 'metadata_dataset.csv'
output_file = 'processed_metadata.csv'
updated_df = asyncio.run(update_csv_with_api_responses(input_file, output_file))
print(f"Results saved to {output_file}")

import pandas as pd
import json
from blablador import Models, ChatCompletions
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
print(API_KEY)

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

async def update_csv_with_api_responses(csv_file_path, output_csv_path):
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Add new columns if they don't exist
    if 'final_res' not in df.columns:
        df['final_res'] = None
    if 'error' not in df.columns:
        df['error'] = None

    # Get available models and select Llama
    models = Models(api_key=API_KEY).get_model_ids()
    print("Available models:", models)
    
    completion = ChatCompletions(api_key=API_KEY, model=models[4])
    print("Using model:", models[4])
    
    # Process each row
    for index, row in df.iterrows():
        try:
            prompt_and_content = row['prompt']

            response = await completion.get_completion([{"role": "user", "content": prompt_and_content}])
            
            # Validate and parse response
            if not response:
                print(f"Empty response for row {index}")
                df.at[index, 'final_res'] = json.dumps([{"role": "user", "content": prompt_and_content}, {"role": "assistant", "content": ""}])
                df.at[index, 'error'] = json.dumps("true")
                continue

            try:
                response_data = json.loads(response)
                
                if response_data["object"] == "error":
                    df.at[index, 'final_res'] = json.dumps([{
                        "role": "user", 
                        "content": prompt_and_content
                    }, {
                        "role": "assistant", 
                        "content": f"Error: {response_data['detail']}"
                    }])
                    df.at[index, 'error'] = json.dumps("true")
                    print("Error in response")
                    continue
                
                # Original choices check
                if 'choices' in response_data and response_data['choices']:
                    message = response_data['choices'][0].get('message', {}).get('content', '')
                    print(f"Message: {message}")
                    df.at[index, 'final_res'] = json.dumps([
                        {"role": "user", "content": prompt_and_content},
                        {"role": "assistant", "content": message}
                    ])
                    df.at[index, 'error'] = json.dumps("false")
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error in row {index}: {e}")
                df.at[index, 'final_res'] = json.dumps([{"role": "user", "content": prompt_and_content}, {"role": "assistant", "content": ""}])
                df.at[index, 'error'] = json.dumps("true")
                
        except Exception as e:
            print(f"Error processing row {index}: {str(e)}")
            df.at[index, 'final_res'] = json.dumps([{"role": "user", "content": prompt_and_content}, {"role": "assistant", "content": ""}])
            df.at[index, 'error'] = json.dumps("true")
    
    df.to_csv(output_csv_path, index=False)
    df.to_csv("backup.csv", index=False)
    return df


# Call the function with the metadata_dataset.csv file
updated_df = asyncio.run(update_csv_with_api_responses('processed_metadata.csv', 'new.csv'))
print("CSV file has been updated with API responses")

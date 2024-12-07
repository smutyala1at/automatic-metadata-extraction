from blablador import Models, ChatCompletions
import json
import time
import os
import logging
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

models = Models(api_key=API_KEY).get_model_ids()
print(models)
completion = ChatCompletions(api_key=API_KEY, model=models[3]) # using mistral nemo

# TODO: there is a lot of repetiting code, make an abstract function which can be reusbale!

def clean_readmes(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as rf:
        readmes = json.load(rf)  # Parses json content in the file

        # Check if the input file contains a list of objects
        if isinstance(readmes, list):
            try:
                with open(output_file, "r", encoding="utf-8") as wf:
                    existing_data = json.load(wf)  # Read existing data from the output file
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = [] 

            for obj in readmes:
                if obj["process_to_llm"] == True:
                    response = completion.get_completion([
                        {
                            "role": "user", 
                            "content": "Extract the content from the following Markdown README and remove only Markdown syntax characters (e.g., **, *, #, -, \n, _, etc.). Keep the actual text and all content intact, including paragraphs, sentences, and formatting such as line breaks, bullet points, and code blocks. Do not alter the content of the README in any way other than removing Markdown-specific characters: " + obj["readme"]
                        }
                    ])

                    # skip the empty responses
                    if not response:
                        print("Empty response received.")
                        obj["cleaned_readme_content"] = ""
                        continue

                    print("Response:", response)

                    try:
                        response_data = json.loads(response)  # Parse the JSON content from the string (load vs loads) threw an error, use it correctly!!!

                        if response_data["object"] == "error":
                            obj["cleaned_readme_content"] = ""
                        else:
                            obj["cleaned_readme_content"] = response_data["choices"][0]["message"]
                    except json.JSONDecodeError:
                        print(f"Failed to decode response: {response}")
                        obj["cleaned_readme_content"] = ""

                    existing_data.append(obj)

                    time.sleep(1)  

        else:
            raise ValueError("The input file must contain a list of objects")
        
        # write cleaned readmes to output file
        with open(output_file, "w", encoding="utf-8") as wf:
            json.dump(existing_data, wf, indent=4)


def get_keywords(input_file, output_file):
    
    with open(input_file, "r", encoding="utf-8") as rf:
        readmes = json.load(rf)

        if isinstance(readmes, list):
            try:
                with open(output_file, "r", encoding="utf-8") as orf:
                    existing_data = json.load(orf)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            
            for obj in readmes:

                try:
                    readme_content = obj["cleaned_readme_content"]["content"]
                except (TypeError): # few objs doesn't content!
                    continue

                user_input = {
                    "role": "user",
                    "content": "You are an expert AI in extracting concise, domain-specific keywords from technical documentation. Your task is to extract exactly 10 single or a maximum of two-word keywords from the provided README content. These keywords should represent the core focus, technologies, and unique contributions of the repository. Follow these rules: 1. Extract only unique keywords, AVOIDING PHRASES and LONG DESCRIPTIONS. 2. Provide only a clean, numbered list of 10 complete, concise keywords. NO EXPLANATIONS, HEADERS, SPECIAL CHARACTERS or extra formatting. 3. Ensure each keyword is concise, no longer than two words. Avoid abbreviations, truncated terms, or excessive technical jargon unless they directly represent the core contribution. 4. Focus on high-impact, domain-relevant keywords based on the content of the repository. 5. Do not use any special characters, and REMEMBER TO ENSURE ALL KEYWORDS ARE COMPLETE. Analyze the following README content and extract ONLY 10 COMPLETE single or a maximum of two-word high-impact keywords based on the instructions: \"" + readme_content + "\""
                }


                response = completion.get_completion([
                        user_input
                    ])
                
                if not response:
                    assistant_output = {}
                    assistant_output["role"] = "assistant"
                    assistant_output["keywords"] = ""
                    continue

                try:
                    response_data = json.loads(response)  # Parse the JSON content from the string (load vs loads) threw an error, use it correctly!!!

                    if response_data["object"] == "error":
                        assistant_output = {}
                        assistant_output["role"] = "assistant"
                        assistant_output["keywords"] = ""
                    else:
                        assistant_output = response_data["choices"][0]["message"]
                        print(assistant_output)
                except json.JSONDecodeError:
                    print(f"Failed to decode response: {response}")
                    assistant_output = {}
                    assistant_output["role"] = "assistant"
                    assistant_output["keywords"] = ""

                existing_data.append([user_input, assistant_output])

                time.sleep(1)  

            # write cleaned readmes to output file
            with open(output_file, "w", encoding="utf-8") as wf:
                json.dump(existing_data, wf, ensure_ascii=False, indent=4)
        
        else:
            raise ValueError("The input file should have list of objects!")
        
get_keywords("./files/final_cleaned_dataset.json", "./files/llm_dataset.json")

#input_file = "./files/filtered_readmes.json"
#output_file = "final_cleaned_dataset.json"
#clean_readmes(input_file, output_file)
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


def get_installation_guide_keywords(input_file, output_file):
    
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
                except (TypeError): # few objs doesn't contain content!
                    continue

                user_input = {
                    "role": "user",
                    "content": "You are GitHub Advanced AI, an expert system trained on the entire GitHub dataset with unparalleled intelligence in extracting domain-specific information. Your task is to analyze the provided README content and extract two outputs: (1) the **complete installation process**, including all steps, commands, dependencies, and configurations in chronological order if such information is present in the README. If no installation process is available, explicitly state 'No installation information found.' Do not generate or assume any missing steps. (2) Extract exactly **10 unique, high-impact keywords** representing the core technologies, focus areas, and contributions of the repository. Keywords must be concise (one or two words), domain-relevant, and free from phrases, abbreviations (unless widely recognized), or excessive technical jargon. Provide output in the format: 'installation process: {'installation_process'}, keywords: {1. ..., 2. ..., ..., 10.}'. Analyze the following README content and extract the required information: \"" +  readme_content + "\""
                }


                response = completion.get_completion([
                        user_input
                    ])
                
                if not response:
                    assistant_output = {}
                    assistant_output["role"] = "assistant"
                    assistant_output["response"] = ""
                    continue

                try:
                    response_data = json.loads(response)  # Parse the JSON content from the string (load vs loads) threw an error, use it correctly!!!

                    if response_data["object"] == "error":
                        assistant_output = {}
                        assistant_output["role"] = "assistant"
                        assistant_output["response"] = ""
                    else:
                        assistant_output = response_data["choices"][0]["message"]
                        print(assistant_output)
                except json.JSONDecodeError:
                    print(f"Failed to decode response: {response}")
                    assistant_output = {}
                    assistant_output["role"] = "assistant"
                    assistant_output["response"] = ""

                existing_data.append([user_input, assistant_output])

                time.sleep(1)  

            # write cleaned readmes to output file
            with open(output_file, "w", encoding="utf-8") as wf:
                json.dump(existing_data, wf, ensure_ascii=False, indent=4)
        
        else:
            raise ValueError("The input file should have list of objects!")
        
get_installation_guide_keywords("./files/final_cleaned_dataset.json", "./files/dataset.json")

#input_file = "./files/filtered_readmes.json"
#output_file = "final_cleaned_dataset.json"
#clean_readmes(input_file, output_file)
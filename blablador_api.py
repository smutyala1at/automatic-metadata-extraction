
from blablador import Models, ChatCompletions
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

models = Models(api_key=API_KEY).get_model_ids()
completion = ChatCompletions(api_key=API_KEY, model=models[3]) # using mistral


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


input_file = "./files/filtered_readmes.json"
output_file = "final_cleaned_dataset.json"
clean_readmes(input_file, output_file)


import json
import tiktoken

def get_readme_file_length(file_name_or_path):

    with open(file_name_or_path, 'r') as f:
        data = json.load(f)

    print("Length of the list:", len(data))


def get_token_count(input_file, output_file):

    # Initialize tokenizer
    tokenizer = tiktoken.get_encoding("cl100k_base") 

    with open(input_file, "r", encoding="utf-8") as rf:
        readmes = json.load(rf)
    
    # check if the input files contains a list of objects
    if isinstance(readmes, list):
        id = 1
        for obj in readmes:
            obj["id"] = id # adding ids maybe easier later when using as dataset
            obj["token_count"] = len(tokenizer.encode(obj["readme"]))
            id += 1
            print(obj)
    else:
        raise ValueError("The input file must contain a list of objects")
    
    with open(output_file, "w", encoding="utf-8") as wf:
        json.dump(readmes, wf, indent=4)


def filter_readmes(input_file, output_file):

    with open(input_file, "r", encoding="utf-8") as rf:
        readmes = json.load(rf)

        # check if the input files contains a list of objects
        if isinstance(readmes, list):
            for obj in readmes:
                if obj["token_count"] > 2000:
                    obj["process_to_llm"] = False
                else:
                    obj["process_to_llm"] = True
        else:
            raise ValueError("The input file must contain a list of objects")
        
        with open(output_file, "w", encoding="utf-8") as wf:
            json.dump(readmes, wf, indent=4)


def get_valid_readmes_count(input_file):

    with open(input_file, "r", encoding="utf-8") as rf:
        readmes = json.load(rf)
        print("total readmes count ", len(readmes))

        if isinstance(readmes, list):
            count = 0
            for obj in readmes:
                if obj["process_to_llm"] == True:
                    count += 1
            print("allowed readmes count: ", count)
        else:
            raise ValueError("The input file must contain a list of objs")


# get_token_count("./files/readmes.json", "./files/readmes_output.json")
# get_readme_file_length("./files/readmes.json")

filter_readmes("readmes_output.json", "filtered_readmes.json")
get_valid_readmes_count("filtered_readmes.json")
import json

def get_readme_file_length(file_name_or_path):

    with open(file_name_or_path, 'r') as f:
        data = json.load(f)

    print("Length of the list:", len(data))


get_readme_file_length("./files/readmes.json")
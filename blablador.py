import json
import requests
import aiohttp
import asyncio
from typing import List, Union
import pandas as pd

class Models():
   
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'accept': 'application/json', 'Authorization': f'Bearer {api_key}'}
   
    url = "https://helmholtz-blablador.fz-juelich.de:8000/v1/models"
     
    def get_model_data(self):
        response = requests.get(url = self.url, headers = self.headers)
        response = json.loads(response.text)
        return(response["data"])

    def get_model_ids(self):
        response = requests.get(url = self.url, headers = self.headers)
        response = json.loads(response.text)

        # TODO write error messages for 400, 401, etc respones
        # like with response.ok , response.status, etc... 

        ids = []
        for model in response["data"]:
            ids.append(model["id"])

        return(ids)

class ChatCompletions:
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, 
                 choices: int = 1, max_tokens: int = 32720, user: str = 'default'):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.choices = choices
        self.max_tokens = max_tokens
        self.user = user
        self.headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.url = "https://helmholtz-blablador.fz-juelich.de:8000/v1/chat/completions"
        self.top_p = 1
        self.presence_penalty = 0
        self.frequency_penalty = 0

    async def get_completion(self, messages: List[dict]):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": self.choices,
            "max_tokens": self.max_tokens,
            "stream": False,  # Changed from "false" string to boolean
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "user": self.user
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=self.url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)  # Increased timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Error response: {error_text}")
                        return error_text
                        
                    response_text = await response.text()
                    return response_text
                    
        except asyncio.TimeoutError:
            print("Request timed out")
            return json.dumps({"error": "timeout"})
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return json.dumps({"error": str(e)})

class Completions:
    def __init__(self, api_key: str, model: str, temperature: float = 0.7,
                 choices: int = 1, max_tokens: int = 32720, user: str = "default"):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.choices = choices
        self.max_tokens = max_tokens
        self.user = user
        self.headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.url = "https://helmholtz-blablador.fz-juelich.de:8000/v1/completions"
        self.suffix = "string"
        self.logprobs = 0
        self.echo = "false"
        self.top_p = 1
        self.presence_penalty = 0
        self.frequency_penalty = 0

    async def get_completion(self, prompt: str):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "suffix": self.suffix,
            "temperature": self.temperature,
            "n": self.choices,
            "max_tokens": self.max_tokens,
            "stop": ["string"],
            "stream": "false",
            "top_p": self.top_p,
            "logprobs": self.logprobs,
            "echo": self.echo,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "user": self.user
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=self.url, headers=self.headers, 
                                      json=payload, timeout=30) as response:
                    print(f"Response status: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Error: {error_text}")
                        return None
                    return await response.text()
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None

class TokenCount:
    def __init__(self, model: str, max_tokens: int = 0):
        self.model = model
        self.max_tokens = max_tokens
        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.url = "https://helmholtz-blablador.fz-juelich.de:8000/api/v1/token_check"

    async def count(self, prompts: Union[str, List[str]]):
        if isinstance(prompts, str):
            prompt_list = [{
                "model": "zephyr-7b-beta",
                "prompt": prompts,
                "max_tokens": self.max_tokens
            }]
        else:
            prompt_list = [{
                "model": "zephyr-7b-beta",
                "prompt": prompt,
                "max_tokens": self.max_tokens
            } for prompt in prompts]

        payload = {"prompts": prompt_list}

        async with aiohttp.ClientSession() as session:
            async with session.post(url=self.url, headers=self.headers, 
                                  json=payload) as response:
                return await response.text()

async def update_csv_with_api_responses(csv_file_path, output_csv_path):
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Add new columns if they don't exist
    if 'final_res' not in df.columns:
        df['final_res'] = None
    if 'error' not in df.columns:
        df['error'] = None

    # Get available models and select appropriate model
    models_client = Models(api_key=API_KEY)
    models = await models_client.get_model_ids()  # Add await here
    print("Available models:", models)
    
    # Use alias-fast instead of full model name
    model_alias = "alias-fast"
    completion = ChatCompletions(api_key=API_KEY, model=model_alias)

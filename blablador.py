import json
import aiohttp
import asyncio
from typing import List, Union

class Models:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {'accept': 'application/json', 'Authorization': f'Bearer {api_key}'}
        self.url = "https://helmholtz-blablador.fz-juelich.de:8000/v1/models"

    async def get_model_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=self.url, headers=self.headers) as response:
                data = await response.json()
                return data["data"]

    async def get_model_ids(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=self.url, headers=self.headers) as response:
                data = await response.json()
                return [model["id"] for model in data["data"]]

class ChatCompletions:
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, 
                 choices: int = 1, max_tokens: int = 32768, user: str = 'default'):
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
            "top_k": -1,
            "n": self.choices,
            "max_tokens": self.max_tokens,
            "stop": "string",
            "stream": "false",
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "user": self.user
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url=self.url, headers=self.headers, 
                                  json=payload, timeout=30) as response:
                return await response.text()

class Completions:
    def __init__(self, api_key: str, model: str, temperature: float = 0.7,
                 choices: int = 1, max_tokens: int = 32768, user: str = "default"):
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

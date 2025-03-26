import requests
import json
from threading import Thread
from queue import Queue
import llm
from typing import Optional
from pydantic import Field
import string
import random


MODELS = {
    "gpt4o": "gpt-4o-mini",
    "claude3": "claude-3-haiku-20240307",
    "llama70b": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "mistral": "mistralai/Mistral-Small-24B-Instruct-2501",
    "o3mini": "o3-mini",
}


@llm.hookimpl
def register_commands(cli):
    @cli.group(name="duckchat")
    def duckchat_group():
        "Commands for interacting with DuckDuckGo AI Chat."


@llm.hookimpl
def register_models(register):
    for model_alias, model_id in MODELS.items():
        register(DuckChatModel(model_id), aliases=[model_alias])


class DuckChatModel(llm.Model):
    """DuckDuckGo AI Chat model integration for LLM framework."""

    class Options(llm.Options):
        """Parameters that can be set when the model is run by vqd."""

        vqd: Optional[str] = Field(
            default=None,
            description=("vqd "),
        )

        vqdhash: Optional[str] = Field(
            default=None,
            description=("vqdhash "),
        )

    def __init__(self, model_id: str):
        self.model_id = model_id

    def __str__(self) -> str:
        return f"DuckChat: {self.model_id}"

    def execute(
        self,
        prompt: llm.Prompt,
        stream: bool,
        response: llm.Response,
        conversation=None,
    ):
        duckchat = DuckChat()
        messages = self.build_messages(prompt, conversation)
        response._prompt_json = {"messages": messages}

        if conversation:
            # for llm chat, vqd's should be fetched for first response.
            try:
                vqd = conversation.responses[-1].prompt.options.vqd
                vqdhash = conversation.responses[-1].prompt.options.vqdhash
            except IndexError as ex:
                try:
                    vqd, vqdhash = duckchat.fetch_vqd()
                except Exception as e:
                    raise RuntimeError(f"Failed to fetch vqd: {e}")
        else:
            try:
                vqd, vqdhash = duckchat.fetch_vqd()
            except Exception as e:
                raise RuntimeError(f"Failed to fetch vqd: {e}")

        try:
            chat_response = duckchat.fetch_response(
                chat_url="https://duckduckgo.com/duckchat/v1/chat",
                vqd=vqd,
                vqd_hash_1=vqdhash,
                model=self.model_id,
                messages=messages,
            )
        except Exception as e:
            raise RuntimeError(f"Error during chat: {e}")

        vqd = chat_response.headers.get("x-vqd-4", "")
        prompt.options.vqd = vqd

        # vqdhash = chat_response.headers.get("x-vqd-hash-1", "")
        prompt.options.vqdhash = vqdhash

        if stream:
            for message in duckchat.process_stream(chat_response):
                yield message
        else:
            final_message = ""
            for message in duckchat.process_stream(chat_response):
                final_message += message
            yield final_message

    def build_messages(self, prompt, conversation):
        messages = []
        if not conversation:
            if prompt.system:
                # system message not accepted
                messages.append(
                    {"role": "user", "content": prompt.prompt + " " + prompt.system}
                )
            else:
                messages.append({"role": "user", "content": prompt.prompt})
            return messages

        for prev_response in conversation.responses:
            messages.append({"role": "user", "content": prev_response.prompt.prompt})
            messages.append({"role": "assistant", "content": prev_response.text()})
        messages.append({"role": "user", "content": prompt.prompt})
        return messages


class RateLimitError(Exception):
    pass


class DuckChat:
    """Utility class to handle interactions with DuckDuckGo Chat."""

    _vqd_cache = None
    _vqd_hash_1 = None

    @staticmethod
    def fetch_vqd():
        if DuckChat._vqd_cache:
            return DuckChat._vqd_cache, DuckChat._vqd_hash_1
        url = "https://duckduckgo.com/duckchat/v1/status"
        headers = {
            "accept": "text/event-stream",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "origin": "https://duckduckgo.com",
            "referer": "https://duckduckgo.com/",
            "x-vqd-accept": "1",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            random_hash = "".join(
                random.choice(string.ascii_lowercase) for _ in range(7)
            )
            vqd_hash_1 = random_hash
            vqd = response.headers.get("x-vqd-4")
            DuckChat._vqd_cache = vqd
            DuckChat._vqd_hash_1 = vqd_hash_1
            return DuckChat._vqd_cache, DuckChat._vqd_hash_1
        elif response.status_code == 429:
            raise RateLimitError("Too many requests. Please try again later.")
        else:
            raise Exception(
                f"Failed to initialize chat: {response.status_code} {response.text}"
            )

    @staticmethod
    def fetch_response(chat_url, vqd, vqd_hash_1, model, messages):
        payload = {"model": model, "messages": messages}
        headers = {
            "accept": "text/event-stream",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "origin": "https://duckduckgo.com",
            "referer": "https://duckduckgo.com/",
            "x-vqd-4": vqd,
        }
        if vqd and vqd_hash_1:
            headers["x-vqd-hash-1"] = vqd_hash_1

        response = requests.post(chat_url, headers=headers, json=payload, stream=True)

        if response.status_code == 429:
            raise RateLimitError(
                f"Too many requests. Please try again later. {response.status_code} {response.text}"
            )

        elif response.status_code != 200:
            raise Exception(
                f"Failed to send message: {response.status_code} {response.text}"
            )
        return response

    @staticmethod
    def process_stream(response):
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line == "data: [DONE]":
                    break
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        message = data.get("message", "")
                        if message:
                            yield message
                    except json.JSONDecodeError:
                        continue

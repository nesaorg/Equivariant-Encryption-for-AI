import asyncio
import html
import os
import re
import unicodedata
import uuid
import warnings
import nats
from typing import Any, Generator, List, Optional
import ast
import httpx
import msgspec
from nats.js import api as js_api
from nesa.backend.utils import sanitize_subject_token, desanitize_subject_token
from nesa.backend.protocol import InferenceResponse, LLMInference, Message, Role, SessionID
from nesa.backend.registry import ModelRegistry
from nesa.settings import settings
from transformers import AutoTokenizer

response_topic: str = "inference-results"
request_topic: str = "inference-requests"
model_mappings = {"nesaorg_Llama-3.1-8B-Instruct-Encrypted": "meta-llama/Llama-3.1-8B-Instruct-ee"}

async def async_yield_text(text):
    for item in text:
        yield item
        await asyncio.sleep(0.1)


def clean_string(message):
    """
    cleans HTML-encoded characters and unwanted characters from a string.
    """
    decoded_content = html.unescape(message)
    printable_content = re.sub(r"[^ -~]", "", decoded_content)
    normalized_content = unicodedata.normalize("NFKC", printable_content)
    cleaned_content = normalized_content.strip()

    return cleaned_content


async def sse_message_handler(inf_request: LLMInference, timeout=60):
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }


    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", settings.stream_url, data=msgspec.json.encode(inf_request), headers=headers, timeout=None
        ) as response:
            response.raise_for_status()

            buffer = ""
            start_time = asyncio.get_event_loop().time()
            first_message_received = False
            async for chunk in response.aiter_text(chunk_size=1024): 
                buffer += chunk
                await asyncio.sleep(0.0)
                while "\n\n" in buffer:
                    event_block, buffer = buffer.split("\n\n", 1)

                    lines = event_block.splitlines()
                    sse_event = {}
                    for line in lines:
                        if line.startswith("event:"):
                            sse_event["event"] = line[len("event:") :].strip()
                        elif line.startswith("data:"):
                            sse_event["data"] = line[len("data:") :].strip()

                    if "data" in sse_event:
                        try:
                            inf_response = msgspec.json.decode(
                                sse_event["data"].encode("utf-8"), type=InferenceResponse
                            )

                            first_message_received = True

                            if inf_response.choices[0].finish_reason:
                                yield inf_response.choices[0].delta.content
                                return

                            yield inf_response.choices[0].delta.content

                        except msgspec.DecodeError:
                            print("Could not decode SSE data as InferenceResponse")

                if not first_message_received and (asyncio.get_event_loop().time() - start_time) > timeout:
                    yield None
                    return


def generate_prompt_template(
    current_msg: str, system_prompt: Optional[str], history: Optional[str], lookback=10, use_memory=True
):
    current_msg = [{"role": Role.USER.value, "content": clean_string(current_msg)}]
    system_instructions = [{"role": Role.SYSTEM.value, "content": clean_string(system_prompt)}]  # noqa
    history = history[-lookback:]
    messages = []

    if use_memory:
        for i, msg_pair in enumerate(history):
            user_msg, assistant_msg = msg_pair
            user_msg = {"role": Role.USER.value, "content": clean_string(user_msg)}
            messages.append(user_msg)
            assistant_msg =assistant_msg.split("[file]", 1)[0]
            assistant_msg = {"role": Role.ASSISTANT.value, "content": clean_string(assistant_msg)}
            messages.append(assistant_msg)

    history = system_instructions + messages + current_msg
    
    return history


def process_stream_sync(inf_request, tokenizer):
    """
    Converts the async streaming handler into a synchronous generator.
    """
    terminators = [
                tokenizer.eos_token_id,  # noqa: // todo:  need a mechanism to forward to backend
                tokenizer.convert_tokens_to_ids("<|eot_id|>"),
            ]
    async def async_wrapper():
        print("[Client]")
        print("Output received from server:")
        out_tokens = []
        async for content in sse_message_handler(inf_request):    
            if content:
                if isinstance(content,int):
                    out_tokens.append(content)
                yield content

        print(out_tokens)
        print()

    def sync_generator():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            gen = async_wrapper()
            while True:
                content = loop.run_until_complete(gen.__anext__())
                if content is None:
                    raise StopAsyncIteration
                if isinstance(content,str):
                    yield f"""[file]{content}[file]"""
                else:
                    if content not in terminators:         
                        yield tokenizer.decode(content)
        except StopAsyncIteration:
            return
        finally:
            loop.close()
    return sync_generator()


@ModelRegistry.register("nesaorg_Llama-3.1-8B-Instruct-Encrypted", is_model_specific=True)
class DistributedLLM:
    def __init__(self, **kwargs):
        warnings.warn("Instantiation is deprecated.", DeprecationWarning)

    @classmethod
    def load_model_tokenizer(cls, model_name, **kwargs):
        model = None
        tokenizer_dir = os.path.join("models", model_name)
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
        if "llama" in model_name:
            terminators = [
                tokenizer.eos_token_id,  # noqa: // todo:  need a mechanism to forward to backend
                tokenizer.convert_tokens_to_ids("<|eot_id|>"),
            ]
        return tokenizer, model  # avoid loading the model locally for llms.

    @classmethod
    def perform_inference(
        cls,
        tokenizer: Any,
        current_msg: str,
        model_name: Optional[Any] = None,
        history: Optional[List[str]] = [],
        system_prompt: Optional[str] = "",
        **kwargs,
    ) -> Generator[str, None, None]:
    
        prompt_template = generate_prompt_template(
            current_msg=current_msg, system_prompt=system_prompt, history=history
        )
        print("[Server]")
        print("Input received from client:")
        
        input_ids = tokenizer.apply_chat_template(prompt_template, add_generation_prompt=True)
        print(input_ids[-20:])
        inf_request = LLMInference(
            stream=True,
            model=model_mappings[model_name],
            correlation_id=str(uuid.uuid4()),
            messages=[Message(content=f"{input_ids}", role=Role.ASSISTANT.value)],
            session_id=SessionID(ee=True),
            model_params={},
        )
        
        for token in process_stream_sync(inf_request, tokenizer):
            yield token


if __name__ == "__main__":
    model_name = 'nesaorg_Llama-3.1-8B-Instruct-Encrypted'
    tokenizer_dir = os.path.join("models", model_name)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
    prompt_template = generate_prompt_template(
            current_msg="hello", system_prompt="you are a friend of user", history=[['user message 1',
                                                                                    'assistant message 1'],
                                                                                    ['user message 2',
                                                                                     'assistant message 2']]
        )

    input_ids = tokenizer.apply_chat_template(prompt_template, add_generation_prompt=True)
    print(tokenizer.decode(input_ids))
    inf_request = LLMInference(
            stream=True,
            model=model_mappings[model_name],
            correlation_id=str(uuid.uuid4()),
            messages=[Message(content=f"{input_ids}", role=Role.ASSISTANT.value)],
            session_id=SessionID(ee=True),
            model_params={},
        )
    for token in process_stream_sync(inf_request, tokenizer):
        print(token)

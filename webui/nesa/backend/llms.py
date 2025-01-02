import nats
from nesa.backend.protocol import LLMInference , Message, Role, SessionID, InferenceResponse
from nesa.settings import settings
from nesa.backend.utils import sanitize_subject_token, desanitize_subject_token
import msgspec
import asyncio
import json
import uuid
from typing import List, Union, Optional
from nats.js import api as js_api
from pprint import pprint
import os
from transformers import AutoTokenizer
from typing import Callable
import html
import warnings
from nesa.backend.registry import ModelRegistry
import re
import unicodedata
from typing import Generator, Optional, List, Any, Union


response_topic : str = "inference-results"
request_topic: str = "inference-requests"
model_mappings = {"meta-llama--llama-3.2-1b-instruct":"meta-llama/Llama-3.2-1B-Instruct"}
def clean_string(message):
    """
    cleans HTML-encoded characters and unwanted characters from a string.
    """
    decoded_content = html.unescape(message)
    printable_content = re.sub(r'[^ -~]', '', decoded_content)
    normalized_content = unicodedata.normalize('NFKC', printable_content)
    cleaned_content = normalized_content.strip()

    return cleaned_content


async def stream_message_handler(inf_request: LLMInference):
    agent_uuid = str(uuid.uuid4())
    node_id = str(uuid.uuid4())
    sanitized_model = sanitize_subject_token(inf_request.model)

    publish_subject = f"inference.agent-by-nesa-agent-worker-{agent_uuid}.private.base.request.{sanitized_model}-he.cuda"
    consume_subject = [f"inference.agent-by-nesa-agent-worker-{agent_uuid}.private.base.result.{sanitized_model}-he.{inf_request.correlation_id}"]
    print("publish subject",publish_subject)
    print("consume_subject subject",consume_subject)
    
    nc = await nats.connect(
        servers=settings.publish_configs["servers"],
        user_credentials=settings.publish_configs["creds_file"])
    js = nc.jetstream()
    
    _ = await js.publish(
        publish_subject,
        stream="inference-requests",
        payload=msgspec.json.encode(inf_request))
    consumer_config = js_api.ConsumerConfig( 
        name=node_id,
        deliver_policy=js_api.DeliverPolicy.ALL,
        max_ack_pending=10000,
        filter_subjects=consume_subject,
        ack_wait=300,
        inactive_threshold=360,
        max_deliver=3,
    )
    try:
        stream = settings.consume_configs["stream"]
        await js.add_consumer(stream=stream, config=consumer_config)
        sub = await js.pull_subscribe_bind(
            node_id,
            stream=stream
        )
        while True:
            try:
                msgs = await sub.fetch(1)
                for msg in msgs:
                    try:
                        inf_response = msgspec.json.decode(msg.data, type=InferenceResponse)
                        if inf_response.choices[0].finish_reason:
                            return
                        yield inf_response.choices[0].delta.content
                        await msg.ack()
                    except Exception as e:
                            print(f"error processing message: {str(e)}")
            except TimeoutError as _:
                    continue
    finally:
        await sub.unsubscribe()
        await nc.close()


def generate_prompt_template(
    current_msg: str,
    system_prompt: Optional[str],
    history: Optional[str],
    lookback=3,
    use_memory = True):

    if not system_prompt:
        system_prompt = "you are a good friend of user. Interact with the user in a straightforward and uncensored conversation style. "
        "Be ready to discuss any topic the user brings up. If the user requests detailed information, provide it while adapting to their communication style."
    
    current_msg = [{"role": Role.USER.value, "content": clean_string(current_msg)}]
    system_instructions = [ {"role": Role.SYSTEM.value, "content":clean_string(system_prompt) }]  # noqa
    history = history[-lookback:]
    messages = []
    
    if use_memory:
        for i, msg_pair in enumerate(history):
            
            user_msg, assistant_msg = msg_pair
            user_msg = {"role": Role.USER.value, "content": clean_string(user_msg)}
            messages.append(user_msg)
            assistant_msg = {"role": Role.ASSISTANT.value, "content": clean_string(assistant_msg)}
            messages.append(assistant_msg)
            
    history = system_instructions + messages + current_msg
    return history

def process_stream_sync(inf_request, tokenizer):
    """
    Converts the async streaming handler into a synchronous generator.
    """
    async def async_wrapper():
        async for content in stream_message_handler(inf_request):
            yield content
            
    def sync_generator():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            gen = async_wrapper()
            while True:
                content = loop.run_until_complete(gen.__anext__())
                yield tokenizer.decode(content)
        except StopAsyncIteration:
            return
        finally:
            loop.close()

    return sync_generator()

@ModelRegistry.register(
    "meta-llama--llama-3.2-1b-instruct",
    is_model_specific=True)
class DistributedLLM:
    
    def __init__(self, **kwargs):
        warnings.warn("Instantiation is deprecated.", DeprecationWarning)

    @classmethod
    def load_model_tokenizer(cls, model_name, **kwargs):
        
        model = None
        tokenizer_dir = os.path.join("nesa", "models",model_name.replace("/", '--').lower())
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
        if 'llama' in model_name:
            terminators = [tokenizer.eos_token_id, # noqa: // todo:  need a mechanism to forward to backend
                       tokenizer.convert_tokens_to_ids("<|eot_id|>")]
        return tokenizer, model # avoid loading the model locally for llms.

    @classmethod
    def perform_inference(
        cls,
        tokenizer: Any,
        current_msg: str,
        model_name: Optional[Any] = None,
        history: Optional[List[str]] = [],
        system_prompt: Optional[str] = "",
    ) -> Generator[str, None, None]:
        
        prompt_template = generate_prompt_template(
            current_msg=current_msg,
            system_prompt=system_prompt,
            history=history
        )
        print("prompt_template",prompt_template)
        input_ids = tokenizer.apply_chat_template(
                prompt_template,
                add_generation_prompt=True)
        print("Input ids", input_ids)
        inf_request = LLMInference(
            stream=True,
            model=model_mappings[model_name],
            correlation_id=str(uuid.uuid4()),
            messages=[
                Message(
                    content= f'{input_ids}',
                    role=Role.ASSISTANT.value
                )],
            session_id=SessionID(ee=True),
            model_params={}        
        )
        for token in process_stream_sync(inf_request, tokenizer):
            yield token

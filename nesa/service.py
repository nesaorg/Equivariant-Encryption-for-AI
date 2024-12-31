import nats
from nesa.protocol import LLMInference , Message, Role, SessionID, InferenceResponse
from settings import settings
from nesa.utils import sanitize_subject_token, desanitize_subject_token
import msgspec
import asyncio
import json
import uuid
from nats.js import api as js_api
from pprint import pprint
import os
from transformers import AutoTokenizer

response_topic : str = "inference-results"
request_topic: str = "inference-requests"

async def stream_message_handler(inf_request: LLMInference):
    agent_uuid = str(uuid.uuid4())
    node_id = str(uuid.uuid4())
    sanitized_model = sanitize_subject_token(inf_request.model)

    publish_subject = f"inference.agent-by-nesa-agent-worker-{agent_uuid}.private.base.request.{sanitized_model}-he.cuda"
    consume_subject = [f"inference.agent-by-nesa-agent-worker-{agent_uuid}.private.base.result.{sanitized_model}-he.{inf_request.correlation_id}"]
    
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


async def generate_response_token(message:str , model: str):
    tokenizer_dir = os.path.join("models",model.replace("/", '--').lower())
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
    if 'llama' in model:
        terminators = [tokenizer.eos_token_id, # noqa
                       tokenizer.convert_tokens_to_ids("<|eot_id|>")]    
    prompt_template = [{"role": Role.USER.value,
                "content": message}]
    input_ids = tokenizer.apply_chat_template(
            prompt_template,
            add_generation_prompt=True)
    
    inf_request = LLMInference(
        stream=True,
        model=model,
        correlation_id=str(uuid.uuid4()),
        messages=[
            Message(
                content= f'{input_ids}',
                role=Role.ASSISTANT.value
            )],
        session_id=SessionID(ee=True),
        model_params={}        
    )
    async for content in stream_message_handler(inf_request):

        token = tokenizer.decode(content)
        print(token,end='')

if __name__ == "__main__":
    model = "meta-llama/Llama-3.2-1B-Instruct"
    message='write a story on AI and ml'
    
    asyncio.run(generate_response_token(message,model))

    
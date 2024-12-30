import nats
from nesa.protocol import LLMInference 
from settings import settings
from nesa.utils import sanitize_subject_token, desanitize_subject_token
import msgspec
import asyncio

response_topic : str = "inference-results"
request_topic: str = "inference-requests"

async def get_response(inf_request,model_name):
    print(settings.publish_configs["creds_file"])
    nc = await nats.connect(
        servers=settings.publish_configs["servers"],
        user_credentials=settings.publish_configs["creds_file"])
    js = nc.jetstream()
    publish_subject = f"inference.*.private.base.request.{sanitize_subject_token(model_name)}-he.cuda"
    resp = await js.publish(
        publish_subject,
        stream=request_topic,
        payload=msgspec.json.encode(inf_request))
    print(resp)


data = """{
    "stream": true,
    "messages": [{"content": "[128000,86363]", "role": "user"}],
    "model": "meta-llama/llama-3.2-1b-inStruct",
    "model_params": {
        "max_new_tokens": 1,
        "num_beams": 1,
        "system_prompt": null,
        "temperature": 1,
        "top_k": 1,
        "top_p": 1,
        "custom_param": "value"
    },
    "session_id": {
        "ee": true,
        "session_id": null,
        "user_id": "662d57657f4de830388db819"
    }
}"""

if __name__ == "__main__":
    model_name = "meta-llama/Llama-3.2-1B-Instruct"
    inf_request = msgspec.json.decode(data,
                                      type=LLMInference)
    asyncio.run(get_response(inf_request=inf_request,
                             model_name=model_name))
    print(inf_request)
    
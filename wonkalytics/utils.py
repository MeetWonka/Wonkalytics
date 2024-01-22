import asyncio
import datetime
import functools
import requests
import sys
from .analytics import wonkalytics_and_promptlayer_api_request
from .generator_wrapper import GeneratorWrapper
import wonkalytics.openai_wrapper  as openai_wrapper
import types
import contextvars

def get_api_key():
    """ Get the API key from openai_wrapper, raise an error if not set. """
    if not openai_wrapper.api_key:
        raise ValueError("PROMPTLAYER_API_KEY not set in openai_wrapper.")
    return openai_wrapper.api_key

def wonkalytics_api_handler(function_name, provider_type, args, kwargs, tags, response, request_start_time, request_end_time, api_key, return_pl_id=False):
    """ Handle API requests for both generators and regular responses. """
    if isinstance(response, (types.GeneratorType, types.AsyncGeneratorType)) or type(response).__name__ in ["Stream", "AsyncStream"]:
        return GeneratorWrapper(response, {
            "function_name": function_name, "provider_type": provider_type, "args": args, "kwargs": kwargs, "tags": tags, 
            "request_start_time": request_start_time, "request_end_time": request_end_time, "return_pl_id": return_pl_id,
        })
    else:
        request_id = wonkalytics_and_promptlayer_api_request(function_name, provider_type, args, kwargs, tags, response, request_start_time, request_end_time, api_key, return_pl_id)
        return (response, request_id) if return_pl_id else response

async def run_async(func, *args, **kwargs):
    """ Run the given function in an asynchronous thread. """
    loop = asyncio.get_running_loop()
    context = contextvars.copy_context()
    return await loop.run_in_executor(None, functools.partial(context.run, func, *args, **kwargs))

def promptlayer_track_score(request_id, score, score_name, api_key):
    """ Track score by making a POST request to the API. """
    data = {"request_id": request_id, "score": score, "api_key": api_key, "name": score_name}
    try:
        response = requests.post(f"{URL_API_PROMPTLAYER}/library-track-score", json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"WARNING: Error tracking score in PromptLayer: {e}", file=sys.stderr)
        return False

async def async_wrapper(coroutine_obj, return_pl_id, request_start_time, function_name, provider_type, tags, *args, **kwargs):
    """ Async wrapper for handling coroutine objects and logging. """
    response = await coroutine_obj
    request_end_time = datetime.datetime.now().timestamp()
    return await run_async(wonkalytics_api_handler, function_name, provider_type, args, kwargs, tags, response, request_start_time, request_end_time, get_api_key(), return_pl_id)

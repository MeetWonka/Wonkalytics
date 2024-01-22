'''Example endpoint used for illustration of usage and the test.py file.'''

import logging
import time
import asyncio
import wonkalytics.openai_wrapper as openai_wrapper
import json
import os
from sse_starlette.sse import EventSourceResponse
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


@router.post("/test",response_class=HTMLResponse, summary="Generate a competence summary")
async def summarize():
    # Later move these env variables inside our analytics logic
    openai_wrapper.api_key = os.getenv('PROMPTLAYER_API_KEY')
        
    import openai as openai_module

    openai = openai_wrapper.OpenAIWrapper(openai_module, function_name="openai")
    openai.api_key = os.getenv('OPENAI_API_KEY')

    # Some pseudo messages for testing
    messages = [
        {
            "role": "system",
            "content": "Guess a number between 1 and 10. Respond very shortly with just a single short sentence."
        },
        {
            "role": "user",
            "content": "You must guess a number between 1 and 10."
        }
                ]

    async def event_publisher():
        start_time = time.time()
        completion = openai.ChatCompletion.create(
            pl_tags=["competence", "tests"],
            model="gpt-4-1106-preview",
            messages=messages,
            temperature=1,
            max_tokens=4096,
            top_p=1,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            return_pl_id = True,
            stream = True
        )

        for chunk in completion:
            delta = chunk[0].choices[0].delta
            # logging.debug(chunk)

            try:
                yield dict(event="data",data=delta.content.replace("\n\n", " \n\n"))
            except:
                if chunk[1]:
                    elapsed_time = time.time() - start_time

                    yield dict(event="wl_request_id",data=chunk[1])
                    yield dict(event="elapsed_time",data=elapsed_time)
            
            await asyncio.sleep(0.0001)

    return EventSourceResponse(event_publisher())
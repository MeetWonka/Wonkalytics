import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import example.endpoint

logging.basicConfig()
# Set logging to debug to log OpenAI response chunks
logging.root.setLevel(logging.DEBUG)

app = FastAPI()
app.include_router(example.endpoint.router)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    logging.info('Base API Called.')
    return {"message": "Hello World"}

# test_streaming.py
import httpx
import pytest
import subprocess
import time

# Start a dummy, example unicorn server to test that the streaming still works
@pytest.fixture(scope="session", autouse=True)
def start_uvicorn():
    # Start Uvicorn in a subprocess
    server = subprocess.Popen(["uvicorn", "example.main:app", "--port", "8000"])
    time.sleep(3)  # Wait for the server to start

    yield

    # After tests are done, kill the server
    server.kill()


@pytest.mark.asyncio
async def test_stream_competence_summary():
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", "http://127.0.0.1:8000/test") as response:
            async for chunk in response.aiter_text():
                assert chunk is not None

from setuptools import setup, find_packages

setup(
    name="Wonkalytics",
    version="0.1.0",
    description="Analytics and logging tool for streaming interactions with OpenAI's API, with support for Azure SQL database logging.",
    author="Wonka",  # Replace with your name
    author_email="s.vanderbijl@meetwonka.com",  # Replace with your email
    url="https://github.com/MeetWonka/Wonkalytics",
    packages=find_packages(),
    install_requires=[
        "aiohttp==3.9.1",
        "aiosignal==1.3.1",
        "annotated-types==0.6.0",
        "anyio==4.2.0",
        "async-timeout==4.0.3",
        "attrs==23.2.0",
        "certifi==2023.11.17",
        "charset-normalizer==3.3.2",
        "click==8.1.7",
        "distro==1.9.0",
        "exceptiongroup==1.2.0",
        "fastapi==0.109.0",
        "frozenlist==1.4.1",
        "h11==0.14.0",
        "httpcore==1.0.2",
        "httpx==0.26.0",
        "idna==3.6",
        "iniconfig==2.0.0",
        "multidict==6.0.4",
        "openai==0.28.1",
        "packaging==23.2",
        "pluggy==1.3.0",
        "pydantic==2.5.3",
        "pydantic_core==2.14.6",
        "pyodbc==5.0.1",
        "pytest==7.4.4",
        "pytest-asyncio==0.23.3",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "sniffio==1.3.0",
        "sse-starlette==1.8.2",
        "starlette==0.35.1",
        "tomli==2.0.1",
        "tqdm==4.66.1",
        "typing_extensions==4.9.0",
        "urllib3==2.1.0",
        "uvicorn==0.26.0",
        "yarl==1.9.4"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)

## Installation

## Prerequisites & pip install

First install OBDC server 18 for SQL: https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver15

For mac you additionally need:
```bash
brew install unixodbc
```

Afterwards simply do:
```bash
pip install git+https://github.com/MeetWonka/Wonkalytics.git
```

On apple M1 pyobcd must be installed from source rather than the default pip install. So on apple silicon macs you have to do:
```bash
pip uninstall pyodbc && pip install --no-binary :all: pyodbc
```

### Set environment variables
Don't forget to set these environment variables:
```bash
AZURE_SQL_SERVER=tcp:{your_azure_sql_server},1433
AZURE_SQL_DB={your_azure_db_name}
AZURE_SQL_USER={your_azure_sql_admin_user}
AZURE_SQL_PASSWORD={your_azure_SQL_password}
AZURE_TABLE_NAME={sql_table_name}
OPENAI_API_KEY={your_openai_key}
OPENAI_ORG_ID={your_openai_org_id}
PROMPTLAYER_API_KEY={promptlayer_api_key}
```

You're ready to go!

## Examples

### Logging a simple analytics log
```python
from analytics import _write_to_azure_sql
from datetime import datetime

log_item = {
    'username': 'logging_test', 
    'action': 'test_log', 
    'timestamp': datetime.now(),
    'tenant_id': 'test_tenant_id',
    'email': 'logtestmail@wonka.com'
}
_write_to_azure_sql(log_item)

```

### Scoring a previously logged interaction/prompt
```python
from analytics import score

response_id = "chatcmpl-8jnIJAkEKBQJn5cs7QCJ1wIcBaII2"
assert score(response_id, 100) == True  # Returns true if no errors
```

### Streaming an openai response and automatically log the interaction
NOTE: See the examples folder to see a more complete example of this.

This allows you to itneract with the streaming of openai as you always do. Several properties will be logged to analytics (see the default database columns). If 'auth_info' key is present on the request then auth info will be logged to analytics with the request.

```python
import logging
import time
import asyncio
import openai_wrapper
import json
import os
from sse_starlette.sse import EventSourceResponse
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import openai as openai_module

@router.post("/test",response_class=HTMLResponse, summary="Generate a competence summary")
async def test():
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
    # Interact with openai as you always do
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

            try:
                yield dict(event="data",data=delta.content.replace("\n\n", " \n\n"))
            except:
                if chunk[1]:
                    elapsed_time = time.time() - start_time

                    yield dict(event="wl_request_id",data=chunk[1])
                    yield dict(event="elapsed_time",data=elapsed_time)
            
            await asyncio.sleep(0.0001)

    return EventSourceResponse(event_publisher())
```

## Parameter formats

Several parameters are expected to follow a default format, when following the streaming examples above parameters should automatically be in the expected format. By default the sql table columns are expected to follow this format:

```
[action]                      TEXT           NULL,
[username]                    TEXT           NULL,
[timestamp]                   DATETIME       NULL,
[tenant_id]                   TEXT           NULL,
[email]                       TEXT           NULL,
[system_msg]                  TEXT           NULL,
[messages]                    TEXT           NULL,
[model]                       TEXT           NULL,
[provider_type]               TEXT           NULL,
[temperature]                 FLOAT (53)     NULL,
[max_tokens]                  INT            NULL,
[top_p]                       FLOAT (53)     NULL,
[frequency_penalty]           FLOAT (53)     NULL,
[presence_penalty]            FLOAT (53)     NULL,
[response_id]                 NVARCHAR (MAX) NULL,
[response_system_fingerprint] TEXT           NULL,
[start_time]                  FLOAT (53)     NULL,
[end_time]                    FLOAT (53)     NULL,
[score]                       INT            NULL
```

The correct key values are automatically extracted when following the examples above to interact with the API. Specifically authinfo is expected to follow the azure /.auth/me format (logging auth_info is optional though) which is:
```js
    // Your API request 
    {
        // Optional authinfo key
        auth_info:    {
            clientPrincipal:  {
                claims: [
                { typ: "iss", val: "https://login.microsoftonline.com/{SOME_TENANT_ID}/v2.0" },
                { typ: "name", val: "Test username" },
                { typ: "http://schemas.microsoft.com/identity/claims/objectidentifier", val: "{SOME_USER_ID}" },
                { typ: "preferred_username", val: "test@testmail.eu" },
                { typ: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier", val: "yp7A9ctNvtDWYXMLCNS9qaokNoorgC3VQQPmpbwsqoM" },
                { typ: "http://schemas.microsoft.com/identity/claims/tenantid", val: "{SOME_TENANT_ID}" },
                { typ: "ver", val: "2.0" }],
                identityProvider: "aad",
                userDetails: "test@testmail.eu",
                userId: "{SOME_USER_ID}",
                userRoles: [
                    "authenticated",
                    "anonymous"
                ],
            }
    }

    }
```


## Testing 
You can run tests by running this in your activated venv:

```bash
python -m pytest
```

## ToDo

- Currently the CI tests write to the ITZU SQL database, much change this later to some test SQL DB.

- Give the option to map parameter values differently, to match the column names of the particular analytics SQL table for your project.

## Documentation


All functions require environment variables to be set for the Azure SQL database connection. Make sure to set the following environment variables:

- `AZURE_SQL_SERVER`: The SQL server address.

- `AZURE_SQL_DB`: The SQL database name.

- `AZURE_SQL_USER`: The SQL database username.

- `AZURE_SQL_PASSWORD`: The SQL database password.

- `AZURE_TABLE_NAME`: The name of the SQL table for logging.

If any of these environment variables are missing, the functions will raise an error.

### `_write_to_azure_sql`

Log an analytics item to the SQL database.

**Important:** For our analytics databases for different projects, we intend to use the following schema: [action, username, timestamp, tenant_id, email].

**Parameters:**

- `item` (dict): A dictionary item containing the column names to write to as keys and the values as values. Nested dictionaries will be automatically flattened where their keys will be built as PARENTKEY_CHILDKEY, to an arbitrary depth. The dict may contain keys that are not in the table columns; these will simply be ignored.

- `encrypt` (str, optional): A string indicating whether to encrypt the connection (default is 'yes').

- `connection_timeout` (int, optional): The timeout for the database connection in seconds (default is 30).

- `trust_server_certificate` (str, optional): A string indicating whether to trust the SQL server certificate (default is 'no').

**Returns:**

- `bool`: True if the log addition was successful, False otherwise.

### `score`

Update the 'score' column value in the SQL table for a specific row identified by 'response_id'.

**Parameters:**

- `response_id` (int): The unique identifier for the row you want to update.

- `score` (float): The new score value to set in the 'score' column.

- `encrypt` (str, optional): A string indicating whether to encrypt the connection (default is 'yes').

- `connection_timeout` (int, optional): The timeout for the database connection in seconds (default is 30).

- `trust_server_certificate` (str, optional): A string indicating whether to trust the SQL server certificate (default is 'no').


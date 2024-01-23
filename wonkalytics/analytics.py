import os
import pyodbc
import logging
from datetime import datetime
from .authinfo import extract_auth_info_pl_tags
from dotenv import load_dotenv
import json
import requests
import sys

load_dotenv()


URL_API_PROMPTLAYER = os.environ.setdefault(
    "URL_API_PROMPTLAYER", "https://api.promptlayer.com"
)


def _check_if_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except Exception:
        return False


def wonkalytics_and_promptlayer_api_request(
    function_name,
    provider_type,
    args,
    kwargs,
    tags,
    request,
    response,
    request_start_time,
    request_end_time,
    api_key,
    return_pl_id=False,
    metadata=None,
):
    """
    Send analytics data to both Wonkalytics and PromptLayer APIs and log requests to an Azure SQL database.

    This function prepares and sends a POST request to the PromptLayer API with the provided data. 
    It also formats and writes the same data to an Azure SQL database for Wonkalytics. 
    The function handles JSON serialization of arguments and catches any exceptions that occur 
    during the request or database logging process.

    Args:
        function_name (str): The name of the function making the request.
        provider_type (str): The type of provider (e.g., 'openai').
        args (list): Positional arguments of the function call.
        kwargs (dict): Keyword arguments of the function call.
        tags (list): Tags associated with the analytics event.
        response: The response received from the provider to be logged.
        request_start_time (float): The start timestamp of the request.
        request_end_time (float): The end timestamp of the request.
        api_key (str): API key for authenticating the request.
        return_pl_id (bool, optional): Flag to determine if the PromptLayer request ID should be returned. Defaults to False.
        metadata (dict, optional): Additional metadata to include in the analytics data.

    Returns:
        str or None: The request ID from PromptLayer if 'return_pl_id' is True; otherwise, None.

    Raises:
        ValueError: If 'kwargs' contains non-JSON-serializable values.
        Exception: For any issues encountered during the POST request or Azure SQL logging.
    """
    request_response = None
    try:
        # value for both promptlayer and wonkalytics
        json_post_dict = {
                "function_name": function_name,
                "provider_type": provider_type,
                "args": args,
                "kwargs": {
                    k: v for k, v in kwargs.items() if _check_if_json_serializable(v)
                },
                "api_key": api_key,
                "tags": tags,
                "request_response": response,
                "request_start_time": request_start_time,
                "request_end_time": request_end_time,
                "metadata": metadata,
            }
        
        request_response = requests.post(
            f"{URL_API_PROMPTLAYER}/track-request",
            json=json_post_dict,
        )

        # For us this is valuable but promptlayer can't handle this
        json_post_dict["request"] = request

        # Wonkalytics
        _write_to_azure_sql(json_post_dict)

        
    except Exception as e:
        print(
            f"WARNING: While logging your request Wonkalytics had the following error: {e}",
            file=sys.stderr,
        )
    if request_response is not None and return_pl_id:
        return request_response.json().get("request_id")
    


def _write_to_azure_sql(item: dict, encrypt: str = 'yes', connection_timeout: int = 30, trust_server_certificate: str = 'no'):
    """
    Log an analytics item to the SQL database.

    Important: for our analytics databases for different projects we intend to use the following schema:
    [action, username, timestamp, tenant_id, email]

    Parameters:
    item (dict): A dictionary item containing the column names to write to as keys and the values as values. Nested dictionaries will be automatically flattened where there keys will be build as PARENTKEY_CHILDKEY, to an arbitrary depth. The dict may contain keys that are not in the table columns, these will simply be ignored.

    Example:
    ```
    from analytics import write_to_azure_sql
    from datetime import datetime

    log_item = {
        'username': 'logging_test', 
        'action': 'test_log', 
        'timestamp': datetime.now(),
        'tenant_id': 'test_tenant_id',
        'email': 'logtestmail@wonka.com'
    }

    write_to_azure_sql(log_item)
    ```
    """
    del item['api_key'] # We do not want to log api keys
    logging.info('Wonkalytics received item to log:')
    logging.info(item)

    if not isinstance(item, dict):
        raise ValueError('Wonkalytics, analytics log item should be a dict.')

    # Check if all environment variables are set
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DB')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    table_name = os.getenv('AZURE_TABLE_NAME')

    _check_required_env_variables(server, database, username, password, table_name)

    # Filter the item for allowed keys
    proc_item = _item_to_analytics_log(item, server, database, username, password, table_name, encrypt, connection_timeout, trust_server_certificate)

    # Build connection string from vars
    cnxn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Uid={username};Pwd={password};Encrypt={encrypt};TrustServerCertificate={trust_server_certificate};Connection Timeout={connection_timeout};'
    
    # Perform the actual log addition in the SQL table
    with pyodbc.connect(cnxn_str) as cnxn:
        cursor = cnxn.cursor()
        columns = ', '.join(proc_item.keys())
        placeholders = ', '.join(['?'] * len(proc_item))
        sql = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(proc_item.values()))
        cnxn.commit()
    
    return True

def score(response_id: str, score: int, encrypt: str = 'yes', connection_timeout: int = 30, trust_server_certificate: str = 'no'):
    """
    Update the 'score' column value in the SQL table for a specific row identified by 'response_id'.

    Args:
        response_id (int): The unique identifier for the row you want to update.
        score (float): The new score value to set in the 'score' column.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    # Check if all environment variables are set
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DB')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    table_name = os.getenv('AZURE_TABLE_NAME')

    _check_required_env_variables(server, database, username, password, table_name)

    # Build connection string from vars
    cnxn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Uid={username};Pwd={password};Encrypt={encrypt};TrustServerCertificate={trust_server_certificate};Connection Timeout={connection_timeout};'
    
    # Perform the actual log addition in the SQL table
    with pyodbc.connect(cnxn_str) as cnxn:
            cursor = cnxn.cursor()
            
            # Construct the SQL UPDATE statement with parameterized query
            sql = f"UPDATE [{table_name}] SET score = ? WHERE response_id = ?"
            
            # Execute the UPDATE statement with the provided score and response_id as parameters
            cursor.execute(sql, (score, response_id))
            
            # Commit the transaction
            cnxn.commit()
    
    return True

def _item_to_analytics_log(item, server, database, username, password, table_name, encrypt: str = 'yes', connection_timeout: int = 30, trust_server_certificate: str = 'no'):
    """
    Process an item for logging in the analytics SQL database.

    This function handles several preprocessing steps:
    - Flattens nested dictionaries in the item.
    - Processes and extracts specific data from ChatGPT messages.
    - Extracts and elevates a response message to the top level.
    - Removes specific prefixes ('kwargs_' and 'request_') from keys.
    - Extracts authentication information and adds tenant ID, username, and email to the item.
    - Timestamps the item with the current datetime.
    - Filters the item's keys to match the allowed columns in the SQL table.

    Args:
        item (dict): The dictionary item to be processed.
        server (str): SQL server address.
        database (str): SQL database name.
        username (str): SQL database username.
        password (str): SQL database password.
        table_name (str): SQL table name for logging.
        encrypt (str): Encryption option for SQL connection.
        connection_timeout (int): Timeout for SQL connection.
        trust_server_certificate (str): Option to trust the SQL server certificate.

    Returns:
        dict: Processed dictionary item ready for SQL logging.
    """
    # Get authinfo (may be None) must be done BEFORE flattening
    auth_info = item.get('request', {}).get('auth_info', None)
    tenantid, user_name, user_mail = extract_auth_info_pl_tags(auth_info)
    item['tenant_id'] = tenantid
    item['username'] = user_name
    item['email'] = user_mail

    flattened_item = _flatten_dict(item)

    # After flattening raise the chatgpt messages to the top level
    proc_item = _process_chatgpt_msgs(flattened_item)

    # After flattening raise the response message to the top level
    proc_item = _extract_response_msg(flattened_item)

    # Remove prefixes
    _remove_prefix_from_keys(proc_item, 'kwargs_')
    _remove_prefix_from_keys(proc_item, 'request_')

    # Timestamp the item
    proc_item['timestamp'] = datetime.now()

    # Filter for allowed column keys in SQL table
    allowed_keys = _get_allowed_keys(table_name, server, database, username, password, encrypt, connection_timeout, trust_server_certificate)
    filtered_item = _filter_allowed_keys(proc_item, allowed_keys)

    logging.info('Wonkalytics item to log after processing and key filtering')
    logging.info(filtered_item)

    return filtered_item

def _remove_prefix_from_keys(original_dict, prefix):
    """
    Remove a specified prefix from the keys in a dictionary. 
    If removing a prefix results in overwriting an existing key, a warning is logged.

    Args:
        original_dict (dict): Dictionary whose keys are to be modified.
        prefix (str): The prefix to be removed from the keys.

    Returns:
        None: The function modifies the dictionary in place.
    """
    for key in list(original_dict.keys()):
        if key.startswith(prefix):
            new_key = key.removeprefix(prefix)
            if new_key in original_dict:
                logging.warning(f"Removing prefix: {prefix} overwrites existing key: {new_key}")
            original_dict[new_key] = original_dict.pop(key)

def _extract_response_msg(item: dict) -> dict:
    """
    Extract the response message from a nested structure within the given dictionary and 
    add it to the top level of the dictionary.

    Assumes the response message is located at item['request_response_choices'][0]['content'].
    Adds this message under the key 'response'.
    """
    if 'request_response_choices' in item:
        item['response'] = item['request_response_choices'][0]['content']
    return item

def _process_chatgpt_msgs(item: dict) -> dict:
    """
    Extract and process ChatGPT messages from the given dictionary, 
    specifically handling 'system' messages and other roles like 'user' and 'assistant'.
    
    The function pops the 'kwargs_messages' from the item, processes them, and then updates 
    the original item with these messages. 'System' messages are logged under 'system_msg', 
    while other messages are concatenated and logged under 'messages'.

    Args:
        item (dict): The dictionary containing ChatGPT messages under 'kwargs_messages'.

    Returns:
        dict: The original dictionary updated with processed ChatGPT messages.
    """
    # There might be logging requests without ChatGPT messages
    messages = item.pop('kwargs_messages', [])

    if len(messages) == 0:
        logging.warning('The item that you want to log with Wonkalytics has no ChatGPT messages. If this is intentional you can ignore this warning.')

    analytics_key_vals = _map_messages_to_keyvals(messages)

    # Update the item to log with the messages
    for key, val in analytics_key_vals.items():
        item[key] = val

    return item


def _map_messages_to_keyvals(messages: list[dict]) -> dict:
    """
    Converts a list of ChatGPT message dictionaries into a format suitable for analytics. 
    This function segregates 'system' messages and compiles other messages into a single string.

    Each message in the list is examined for its 'role'. Messages with the 'system' role are 
    stored under the 'system_msg' key. Other messages are concatenated into a single string, 
    separated by their roles and line breaks, and stored under the 'messages' key. This allows 
    for easy distinction between system-generated messages and user/assistant interactions in the analytics.

    Args:
        messages (list[dict]): A list of message dictionaries, each containing 'role' and 'content' keys.

    Returns:
        dict: A dictionary with two keys, 'system_msg' and 'messages', containing the processed messages.
              'system_msg' contains the content of the last 'system' role message. 'messages' contains 
              a concatenated string of all other messages.
    """
    analytics_key_vals = {}
    non_system_msgs = ''

    for msg in messages:
        if msg['role'] == 'system':
            analytics_key_vals['system_msg'] = msg['content']
        # There might be situations where 'user' and 'assistent' messages are pre-given (before the response) to give examples to the model. These should be separately logged from the "actual" user and assistent messages.
        else:
            non_system_msgs += msg['role'] + ':\n'
            non_system_msgs += msg['content'] + '\n\n'
    
    analytics_key_vals['messages'] = non_system_msgs

    return analytics_key_vals

def _get_allowed_keys(table_name: str, server: str, database: str, username: str, password: str, encrypt: str = 'yes', connection_timeout: int = 30, trust_server_certificate: str = 'no') -> set:
    """
    Retrieves the column names from a specified table in the Azure SQL database.

    Parameters:
    table_name (str): The name of the table to retrieve column names from.

    Returns:
    set: A set of strings representing the column names in the table.

    Raises:
    Exception: Propagates any exceptions that occur during the database operation.
    """
    cnxn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Uid={username};Pwd={password};Encrypt={encrypt};TrustServerCertificate={trust_server_certificate};Connection Timeout={connection_timeout};'
    query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'"
    
    with pyodbc.connect(cnxn_str) as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query)
        columns = {row.COLUMN_NAME for row in cursor.fetchall()}
    
    logging.debug(f"Table {table_name} has allowed columns: {columns}")
    return columns


def _filter_allowed_keys(item: dict, allowed_keys: set) -> dict:
    """
    Filters a dictionary to include only keys that are in a specified set of allowed keys.
    Logs a warning for any keys in the item that are not allowed and raises an error if
    the filtered dictionary is empty.

    Parameters:
    item (dict): The dictionary to be filtered.
    allowed_keys (set): A set of strings representing allowed keys.

    Returns:
    dict: A dictionary containing only the allowed keys and values.

    Raises:
    ValueError: If the filtered dictionary is empty.
    """
    filtered_item = {}
    for k, v in item.items():
        if k in allowed_keys:
            filtered_item[k] = v
        else:
            logging.warning(f"Key '{k}' is not allowed in SQL table and will be ignored.")
    
    if not filtered_item:
        raise ValueError("Filtered dictionary is empty. None of the keys are allowed.")

    return filtered_item


def _check_required_env_variables(server, database, username, password, table_name):
    env_vars = {'AZURE_SQL_SERVER': server, 'AZURE_SQL_DB': database,
                'AZURE_SQL_USER': username, 'AZURE_SQL_PASSWORD': password,
                'AZURE_TABLE_NAME': table_name}
    missing_vars = [key for key, value in env_vars.items() if value is None]
    if missing_vars:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")


def _flatten_dict(item: dict, parent_key='', sep='_') -> dict:
    """
    Flattens a nested dictionary into a single-level dictionary with compound keys.

    Parameters:
    item (dict): The dictionary to be flattened.
    parent_key (str, optional): The base key to use for compound key names. Defaults to ''.
    sep (str, optional): The separator to use between compound key names. Defaults to '_'.

    Returns:
    dict: A flattened dictionary.

    Example Usage:
    >>> flatten_dict({'a': 1, 'b': {'c': 2, 'd': {'e': 3}}})
    {'a': 1, 'b_c': 2, 'b_d_e': 3}

    Notes:
    - Nested dictionaries are combined into one with compound keys.
    - Lists and other iterable types within the dictionary are not flattened.
    """
    items = []
    for k, v in item.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

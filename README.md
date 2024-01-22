## Install python package


On apple M1 pyobcd must be installed from source rather than the default pip install:

```
pip install --no-binary :all: pyodbc
```


## Set environment variables
Please set these environment variables:
```
AZURE_SQL_SERVER=tcp:{your_azure_sql_server},1433
AZURE_SQL_DB={your_azure_db_name}
AZURE_SQL_USER={your_azure_sql_admin_user}
AZURE_SQL_PASSWORD={your_azure_SQL_password}
AZURE_TABLE_NAME={sql_table_name}
OPENAI_API_KEY={your_openai_key}
OPENAI_ORG_ID={your_openai_org_id}
PROMPTLAYER_API_KEY={promptlayer_api_key}
```



## Install ODBC driver

https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver15

Afterwards also do:
```
brew install unixodbc
```

## Testing 

python -m pytest

## ToDo

Currently the CI tests write to the ITZU SQL database, much change this later to some test SQL DB
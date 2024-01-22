## Install python package


On apple M1 pyobcd must be installed from source rather than the default pip install:

```
pip install --no-binary :all: pyodbc
```


## Set environment variables




## Install ODBC driver

https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos?view=sql-server-ver15

Afterwards also do:
```
brew install unixodbc
```

## Testing 

python -m pytest
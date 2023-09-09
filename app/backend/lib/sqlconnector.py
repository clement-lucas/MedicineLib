# SQL Database への接続を行うクラス
import os
from azure import identity
import pyodbc, struct

class SQLConnector:
    @staticmethod
    def get_conn():
        sql_connection_string = os.environ.get('SQL_CONNECTION_STRING')

        if os.environ.get('SQL_AUTHENTICATION') is None:
            return pyodbc.connect(sql_connection_string)
        elif os.environ.get('SQL_AUTHENTICATION') != 'ActiveDirectoryMsi':
            return pyodbc.connect(sql_connection_string)

        credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
        token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
        conn = pyodbc.connect(sql_connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
        return conn

import os
import pyodbc
from approaches.approach import Approach
from text import nonewlines

class GetPatientApproach(Approach):
    def __init__(self, sourcepage_field: str, content_field: str):
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        
    def run(self, patient_code:str) -> any:

        print("run")
        print(patient_code)

        # SQL Server に接続する
        sql_connection_string = os.environ.get('SQL_CONNECTION_STRING')
        cnxn = pyodbc.connect(sql_connection_string)
        cursor = cnxn.cursor()

        # SQL Server から患者情報を取得する
        cursor.execute("""SELECT PID_NAME
            FROM [dbo].[EXTBDH1] WHERE ACTIVE_FLG = 1 AND PID = ?""", patient_code)
        rows = cursor.fetchall() 
        for row in rows:
            return {"name":row[0]}
        return {"name":"患者情報が見つかりませんでした。"}



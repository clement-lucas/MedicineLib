import os
import pyodbc
from approaches.approach import Approach
from text import nonewlines

class GetHistoryDetailApproach(Approach):
    def __init__(self, sourcepage_field: str, content_field: str):
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        
    def run(self, id:str) -> any:

        print("run")
        print(id)

        # SQL Server に接続する
        sql_connection_string = os.environ.get('SQL_CONNECTION_STRING')
        cnxn = pyodbc.connect(sql_connection_string)
        cursor = cnxn.cursor()

        # SQL Server から履歴情報を取得する
        cursor.execute("""
SELECT TOP (1000) [Id]
      ,[History].[UserId]
      ,[History].[PID]
      ,[History].[DocumentName]
      ,[History].[Prompt]
      ,[History].[MedicalRecord]
      ,[History].[Response]
      ,[History].[CreatedDateTime]
      ,[History].[UpdatedDateTime]
	  ,Patient.[PID_NAME]
  FROM [dbo].[History]
  INNER JOIN (SELECT DISTINCT PID, PID_NAME FROM EXTBDH1 WHERE ACTIVE_FLG = 1) AS Patient
  ON [History].[PID] = Patient.[PID] AND [History].[IsDeleted] = 0 AND [Id] = ?
  """, id)
        rows = cursor.fetchall() 
        for row in rows:
            return {"id":row[0] , 
                    "user_id":row[1] , 
                    "pid":row[2] , 
                    "document_name":row[3] , 
                    "prompt":row[4] , 
                    "medical_record":row[5] , 
                    "response":row[6] , 
                    "created_date_time":row[7] , 
                    "updated_date_time":row[8], 
                    "patient_name":row[9]} 
        return {"name":"履歴情報が見つかりませんでした。"}



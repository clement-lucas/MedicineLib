import os
import pyodbc
from approaches.approach import Approach
from text import nonewlines

class GetHistoryIndexApproach(Approach):
    def __init__(self, sourcepage_field: str, content_field: str):
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        
    def run(self, user_id:str) -> any:

        print("run")
        print(user_id)

        # SQL Server に接続する
        sql_connection_string = os.environ.get('SQL_CONNECTION_STRING')
        cnxn = pyodbc.connect(sql_connection_string)
        cursor = cnxn.cursor()

        # SQL Server から履歴情報を取得する
        cursor.execute("""SELECT 
        [Id]
      ,[UserId]
      ,[PID]
      ,[DocumentName]
      ,[CreatedDateTime]
      ,[UpdatedDateTime]
  FROM [dbo].[History]
  WHERE [UserId] = ?,
  [IsDeleted] = 0
  """, user_id)
        rows = cursor.fetchall() 
        records = []
        for row in rows:
            records.append({"id":row[0] ,
                     "user_id":row[1] , 
                     "pid":row[2] , 
                     "document_name":row[3] , 
                     "created_date_time":row[4] , 
                     "updated_date_time":row[5] })
        return records



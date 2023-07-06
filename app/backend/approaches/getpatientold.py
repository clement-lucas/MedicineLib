import os
import pyodbc
from approaches.approach import Approach
from text import nonewlines

# このクラスは旧体系の患者情報取得クラスです。
class GetPatientOldApproach(Approach):
    def __init__(self, sourcepage_field: str, content_field: str):
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        
    def run(self, patient_code:str) -> any:

        print("run")
        print(patient_code)

        # SQL Server に接続する
        cnxn = pyodbc.connect(os.environ.get("SQL_CONNECTION_STRING"))
        cursor = cnxn.cursor()

        # SQL Server から患者情報を取得する
        cursor.execute("""SELECT Name
            FROM [dbo].[Patient] WHERE IsDeleted = 0 AND PatientCode = ?""", patient_code)
        #cursor.execute('SELECT Name FROM Patient WHERE PatientCode = ?', patient_code)
        rows = cursor.fetchall() 
        records = ""
        for row in rows:
            return {"name":row[0]}
        return {"name":"患者情報が見つかりませんでした。"}



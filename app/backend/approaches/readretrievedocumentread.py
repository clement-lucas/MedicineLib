import openai
from lib.sqlconnector import SQLConnector
from approaches.approach import Approach
from azure.search.documents import SearchClient
from langchainadapters import HtmlCallbackHandler
from text import nonewlines
from lookuptool import CsvLookupTool

# Attempt to answer questions by iteratively evaluating the question to see what information is missing, and once all information
# is present then formulate an answer. Each iteration consists of two parts: first use GPT to see if we need more information, 
# second if more data is needed use the requested "tool" to retrieve it. The last call to GPT answers the actual question.
# This is inspired by the MKRL paper[1] and applied here using the implementation in Langchain.
# [1] E. Karpas, et al. arXiv:2205.00445
class ReadRetrieveDocumentReadApproach(Approach):

    prompt_prefix = """
The assistant will answer questions about the contents of the medical records as source. Medical record data consists of the date of receipt and the contents of the description. Be brief in your answers.
Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below.
""" 

    def __init__(self, search_client: SearchClient, chatgpt_deployment: str, gpt_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.chatgpt_deployment = chatgpt_deployment
        self.gpt_deployment = gpt_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        
    def run(self, document_name: str, patient_code:str, overrides: dict) -> any:

        print("run")
        print(document_name)
        print(patient_code)

        # SQL Server に接続する
        cnxn = SQLConnector.get_conn()
        cursor = cnxn.cursor()

        # SQL Server から患者情報を取得する
        cursor.execute("""SELECT TOP (1000) 
            CONVERT(VARCHAR,[Date],111) + ':' + [Record] AS Record
            FROM [dbo].[MedicalRecord] WHERE IsDeleted = 0 AND PatientCode = ?""", patient_code)
        #cursor.execute('SELECT Name FROM Patient WHERE PatientCode = ?', patient_code)
        rows = cursor.fetchall() 
        records = ""
        for row in rows:
            print(row[0])
            records += row[0] + "\n\n"
        print(records)

#        follow_up_questions_prompt = self.follow_up_questions_prompt_content if overrides.get("suggest_followup_questions") else ""
#        以下のカルテデータからHL7規格に沿った{format_name}を json 形式で出力してください。
#         回答の最後に、データの日付を[yyyy/mm/dd]の形式で記載してください。
#        紹介状は、人間に対する手紙のような部分と、HL7規格に沿ったXMLデータの部分にわかれています。

        question = ""
        if document_name == "紹介状":
            question = """
あなたは医療事務アシスタントです。
以下のカルテデータにて書かれた人を違う医者に引き継ぐ必要があります。
以下のカルテデータにて書かれた人を他の医師に引継ぎのための紹介状を書いてください。
宛先の医師名は（宛先の医師名）とします。
ただし、作成される文章は1000文字以内とします。"""
        elif document_name == "入院経過":
            question = """
あなたは医療事務アシスタントです。
以下のカルテデータから入院経過を抽出してください。
ただし、作成される文章は1000文字以内とします。"""
        elif document_name == "看護記録":
            question = """
あなたは医療事務アシスタントです。
以下のカルテデータから看護記録を作成してください。
ただし、作成される文章は1000文字以内とします。"""

        messages = [{"role":"system","content":self.prompt_prefix},
                    {"role":"user","content":question + "\n\nカルテデータ：\n\n" + records}]
        print(messages)

        completion = openai.ChatCompletion.create(
            engine=self.gpt_deployment,
            messages = messages,
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        answer = completion.choices[0].message.content
        print(answer)        
        return {"data_points": "test results", "answer": answer, "thoughts": f"Searched for:<br>q test<br><br>Prompt:<br>"}

    def get_chat_history_as_text(self, question, include_last_turn=True, approx_max_tokens=1000) -> str:
        history_text = """<|im_start|>user""" +"\n" + "user" + "\n" + question + """<|im_end|>""" + "\n" + """<|im_start|>assistant"""
        return history_text
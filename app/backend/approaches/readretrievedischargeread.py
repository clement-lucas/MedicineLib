import os
import openai
import pyodbc
from approaches.approach import Approach
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from langchain.llms.openai import AzureOpenAI
from langchain.callbacks.base import CallbackManager
from langchain.chains import LLMChain
from langchain.agents import Tool, ZeroShotAgent, AgentExecutor
from langchain.llms.openai import AzureOpenAI
from langchainadapters import HtmlCallbackHandler
from text import nonewlines
from lookuptool import CsvLookupTool
from parser.doctorsnoteparser import DoctorsNoteParser as DNP
from parser.nursesnoteparser import NursesNoteParser as NNP


# Attempt to answer questions by iteratively evaluating the question to see what information is missing, and once all information
# is present then formulate an answer. Each iteration consists of two parts: first use GPT to see if we need more information, 
# second if more data is needed use the requested "tool" to retrieve it. The last call to GPT answers the actual question.
# This is inspired by the MKRL paper[1] and applied here using the implementation in Langchain.
# [1] E. Karpas, et al. arXiv:2205.00445
class ReadRetrieveDischargeReadApproach(Approach):

    prompt_prefix = """<|im_start|>system
The assistant will answer questions about the contents of the medical file as source. Medical record data consists of the date of receipt and the contents of the description. Be brief in your answers.
Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below.
Sources:
{sources}
<|im_end|>
{chat_history}
""" 

    def __init__(self, search_client: SearchClient, chatgpt_deployment: str, gpt_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.chatgpt_deployment = chatgpt_deployment
        self.gpt_deployment = gpt_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    # yyyyMMddHHMISS -> yyyy/MM/dd HH:MI:SS に変換する関数
    # 例）20140224095813 -> 2014/02/24 09:58:13
    def get_datetime(self, org):
        year = org[0:4]
        month = org[4:6]
        day = org[6:8]
        hour = org[8:10]
        minute = org[10:12]
        second = org[12:14]
        return year + "/" + month + "/" + day + " " + hour + ":" + minute + ":" + second

    def get_allergy(self, cursor, pi_item_id, jpn_item_name, patient_code):
        select_allergy_sql = """SELECT PI_ITEM_02, PI_ITEM_03
            FROM EATBPI
            WHERE PI_ACT_FLG = 1
            AND PI_ITEM_ID = ?
            AND PID = ?"""
        
        cursor.execute(select_allergy_sql, pi_item_id, patient_code)
        rows = cursor.fetchall() 
        is_first = True
        records = ""
        for row in rows:
            if is_first:
                records += "\n以下は患者の" + jpn_item_name + "アレルギーに関する情報 です。\n\n"
            is_first = False
            print(row[0])
            print(row[1])
            records += "原因となる" + jpn_item_name + "：" + row[0] + "\n"
            records += "摂取時症状：" + row[1] + "\n\n"
        return records

    def run(self, document_name: str, patient_code:str, overrides: dict) -> any:

        print("run")
        print(document_name)
        print(patient_code)

        # SQL Server に接続する
        # 接続文字列を取得する
        sql_connection_string = os.environ.get('SQL_CONNECTION_STRING')
        cnxn = pyodbc.connect(sql_connection_string)
        cursor = cnxn.cursor()

        # SQL Server から患者情報を取得する
        # cursor.execute("""SELECT TOP (1000) 
        #     CONVERT(VARCHAR,[Date],111) + ':' + [Record] AS Record
        #     FROM [dbo].[MedicalRecord] WHERE IsDeleted = 0 AND PatientCode = ?""", patient_code)
        #cursor.execute('SELECT Name FROM Patient WHERE PatientCode = ?', patient_code)

        # TODO もしも、標準的な利用シナリオにおいて、入力データが多いなどの理由でGPTのトークン長制限を超えてしまう場合は、
        # 入力データと出力項目を分割して、複数回に分けてGPTに投げるようにするなどの工夫が必要。

        # TODO 日付等の各種取得条件は適宜実装のこと
        select_datax_sql = """SELECT EXTBDH1.DOCDATE, EXTBDC1.DOC_DATAX FROM EXTBDC1 
            INNER JOIN EXTBDH1 
            ON EXTBDC1.DOC_NO = EXTBDH1.DOC_NO
            AND EXTBDH1.DOC_K = ? 
            AND EXTBDH1.ACTIVE_FLG = 1 
            AND EXTBDC1.ACTIVE_FLG = 1 
            AND EXTBDH1.PID = ?
            ORDER BY EXTBDH1.DOCDATE DESC"""

        # 医師記録の取得
        cursor.execute(select_datax_sql,'MD01', patient_code)
        rows = cursor.fetchall() 
        records = ""
        is_first = True
        for row in rows:
            if is_first:
                records += "\n以下は医師の書いた SOAP です。\n\n"
            is_first = False
            print("------1")
            print(row[0])
            print("------2")
            print(row[1])
            print("------3")
            datetime = self.get_datetime(row[0])
            # XML のまま GPT に投げても解釈してくれないこともないが、
            # XML のままだとトークン数をとても消費してしまうので、
            # XML を解釈して、平文に変換する。
            soap = DNP(row[1])
            records += "記入日：" + datetime + "\n\n"
            if soap.S != "":
                records += "S：" + soap.S + "\n\n"
            if soap.O != "":
                records += "O：" + soap.O + "\n\n"
            if soap.A != "":
                records += "A：" + soap.A + "\n\n"
            if soap.P != "":
                records += "P：" + soap.P + "\n\n"
            records += "\n\n"
            
        print(records)

        # 看護記録の取得
        cursor.execute(select_datax_sql,'ON01', patient_code)
        rows = cursor.fetchall() 
        is_first = True
        for row in rows:
            if is_first:
                records += "\n以下は看護師の書いた SOAP です。\n\n"
            is_first = False
            print("------1")
            print(row[0])
            print("------2")
            print(row[1])
            print("------3")
            datetime = self.get_datetime(row[0])
            # XML のまま GPT に投げても解釈してくれないこともないが、
            # XML のままだとトークン数をとても消費してしまうので、
            # XML を解釈して、平文に変換する。
            soap = NNP(row[1])
            records += "記入日：" + datetime + "\n\n"
            if soap.S != "":
                records += "S：" + soap.S + "\n\n"
            if soap.O != "":
                records += "O：" + soap.O + "\n\n"
            if soap.A != "":
                records += "A：" + soap.A + "\n\n"
            if soap.P != "":
                records += "P：" + soap.P + "\n\n"
            records += "\n\n"
        print(records)

        # TODO SV08, SV09 への対応

        # ARG001（薬剤アレルギー）
        # ARG010（食物アレルギー）
        # ARG040（注意すべき食物）
        # ARGN10（その他アレルギー）

        # 薬剤アレルギー情報の取得
        records += self.get_allergy(cursor, 'ARG001', '薬剤', patient_code)
        
        # 食物アレルギー情報の取得
        records += self.get_allergy(cursor, 'ARG010', '食物', patient_code)

        # 注意すべき食物情報の取得
        records += self.get_allergy(cursor, 'ARG040', '注意すべき食物', patient_code)

        # その他アレルギー情報の取得
        records += self.get_allergy(cursor, 'ARGN10', 'その他原因物質', patient_code)
        print(records)

        # 紹介元履歴の取得
        # TODO 本項目は単純な転記であり、
        # GPT の介在を必要としないプログラムにより実現が可能な処理であるため、
        # ここでは SQL サンプルの記載のみにとどめ、取得しないこととする。
        select_shokaimoto_sql = """SELECT 
            PI_ITEM_17 AS SHOKAI_BI,
            PI_ITEM_02 AS TOIN_KA,
            PI_ITEM_04 AS BYOIN_MEI,
            '' AS FROM_KA,
            PI_ITEM_06 AS ISHI_MEI,
            PI_ITEM_13 AS ZIP_CODE,
            PI_ITEM_14 AS ADRESS
            FROM EATBPI
            WHERE PI_ACT_FLG = 1
            AND PI_ITEM_ID = 'BAS001'
            AND PID = ?
            ORDER BY PI_ITEM_17 DESC"""
        
        # cursor.execute(select_shokaimoto_sql, patient_code)
        # rows = cursor.fetchall() 
        # is_first = True
        # for row in rows:
        #     if is_first:
        #         records += "\n以下は患者の紹介元履歴に関する情報 です。\n\n"
        #     is_first = False
        #     print(row[0])
        #     print(row[1])
        #     records += "紹介日：" + row[0] + "\n"
        #     records += "当院診療科：" + row[1] + "\n"
        #     records += "照会元病院：" + row[2] + "\n"
        #     records += "照会元診療科：" + row[3] + "\n"
        #     records += "照会元医師：" + row[4] + "\n"
        #     records += "照会元郵便番号：" + row[5] + "\n"
        #     records += "照会元住所：" + row[6] + "\n\n"

        # 紹介先履歴の取得
        # TODO 本項目は単純な転記であり、
        # GPT の介在を必要としないプログラムにより実現が可能な処理であるため、
        # ここでは SQL サンプルの記載のみにとどめ、取得しないこととする。
        select_shokaisaki_sql = """SELECT 
            PI_ITEM_17 AS SHOKAI_BI,
            PI_ITEM_02 AS TOIN_KA,
            PI_ITEM_10 AS BYOIN_MEI,
            PI_ITEM_14 AS TO_KA,
            PI_ITEM_12 AS ISHI_MEI,
            PI_ITEM_15 AS ZIP_CODE,
            PI_ITEM_16 AS ADRESS
            FROM EATBPI
            WHERE PI_ACT_FLG = 1
            AND PI_ITEM_ID = 'BAS002'
            AND PID = ?
            ORDER BY PI_ITEM_17 DESC"""
        
        # cursor.execute(select_shokaisaki_sql, patient_code)
        # rows = cursor.fetchall() 
        # is_first = True
        # for row in rows:
        #     if is_first:
        #         records += "\n以下は患者の紹介先履歴に関する情報 です。\n\n"
        #     is_first = False
        #     print(row[0])
        #     print(row[1])
        #     records += "紹介日：" + row[0] + "\n"
        #     records += "当院診療科：" + row[1] + "\n"
        #     records += "照会先病院：" + row[2] + "\n"
        #     records += "照会先診療科：" + row[3] + "\n"
        #     records += "照会先医師：" + row[4] + "\n"
        #     records += "照会先郵便番号：" + row[5] + "\n"
        #     records += "照会先住所：" + row[6] + "\n\n"


        # 退院処方の取得
        # TODO 本項目は単純な転記であり、
        # GPT の介在を必要としないプログラムにより実現が可能な処理であるため、
        # ここでは SQL サンプルの記載のみにとどめ、取得しないこととする。
        select_taiinji_shoho_sql = """
        SELECT EXTBOD1.IATTR, EXTBOD1.INAME, EXTBOD1.NUM, EXTBOD1.UNAME FROM EXTBDH1 
            INNER JOIN EXTBOD1 
            ON EXTBOD1.DOC_NO = EXTBDH1.DOC_NO
            AND EXTBDH1.DOC_K = 'H004'
            AND EXTBDH1.ACTIVE_FLG = 1 
            AND EXTBOD1.ACTIVE_FLG = 1 
            AND EXTBDH1.PID = ?
			ORDER BY EXTBOD1.SEQ"""

        # 退院後予約情報の取得
        # TODO 本項目は単純な転記であり、
        # GPT の介在を必要としないプログラムにより実現が可能な処理であるため、
        # ここでは SQL サンプルの記載のみにとどめ、取得しないこととする。
        select_taiinji_yoyakujoho_sql = """
        SELECT EXTBOD1.IATTR, EXTBOD1.INAME FROM EXTBDH1 
            INNER JOIN EXTBOD1 
            ON EXTBOD1.DOC_NO = EXTBDH1.DOC_NO
            AND EXTBDH1.DOC_K = 'W000'
            AND EXTBDH1.ACTIVE_FLG = 1 
            AND EXTBOD1.ACTIVE_FLG = 1 
            AND EXTBDH1.PID = ?
			ORDER BY EXTBOD1.SEQ
            """

#        follow_up_questions_prompt = self.follow_up_questions_prompt_content if overrides.get("suggest_followup_questions") else ""
#        以下のカルテデータからHL7規格に沿った{format_name}を json 形式で出力してください。
#         回答の最後に、データの日付を[yyyy/mm/dd]の形式で記載してください。
#        紹介状は、人間に対する手紙のような部分と、HL7規格に沿ったXMLデータの部分にわかれています。

        question = ""
        if document_name == "退院時サマリ":
            question = """
あなたは医療事務アシスタントです。
カルテデータから退院時サマリを作成しようとしています。
カルテデータは、医師または看護師の書いた SOAP と、アレルギー情報から構成されます。
以下のフォーマットに沿って出力してください。これは例やサンプルではありません。フォーマット中の半角角括弧で囲まれた部分を置き換えてください。
例えば、フォーマットの中に[主訴]とあった場合、[主訴]と書いてある部分を、作成した主訴のテキストで置き換えてください。
カルテデータから読み取れることのできない項目に対しては「なし」という文言を出力してください。
医師の書いたSOAPを優先的に input としてください。作成される文章は1000文字以内とします。
フォーマット開始

【アレルギー・不適応反応】​
[アレルギー・不適応反応]

【主訴または入院理由】​
[主訴または入院理由]

【入院までの経過】​
[入院までの経過]

【入院経過】​
[入院経過]

【退院時状況】​
[退院時状況]

【退院時方針】
[退院時方針]
フォーマット終了

"""
        prompt = self.prompt_prefix.format(sources=records, chat_history=self.get_chat_history_as_text(question))
        print(prompt)
        completion = openai.Completion.create(
            engine=self.gpt_deployment, 
            prompt=prompt, 
            temperature=overrides.get("temperature") or 0.7, 
            max_tokens=1024, 
            n=1, 
            stop=["<|im_end|>", "<|im_start|>"])
        
        print(completion.choices[0].text)
        return {"data_points": "test results", "answer": completion.choices[0].text + "\n\n\nカルテデータ：\n" + records, "thoughts": f"Searched for:<br>q test<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}

    def get_chat_history_as_text(self, question, include_last_turn=True, approx_max_tokens=1000) -> str:
        history_text = """<|im_start|>user""" +"\n" + "user" + "\n" + question + """<|im_end|>""" + "\n" + """<|im_start|>assistant"""
        return history_text

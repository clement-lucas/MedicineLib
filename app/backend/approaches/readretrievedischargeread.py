######################
# 退院時サマリの作成 #
######################

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
    
    # 質問文とカルテデータを受け取って GPT に投げる関数
    def get_answer(self, category_name, question, sources):
        messages = [{"role":"system","content":self.prompt_prefix},
                    {"role":"user","content":question + "\n\nmedical record:\n\n" + sources}]
        print(messages)

        completion = openai.ChatCompletion.create(
            engine=self.gpt_deployment,
            messages = messages,
            temperature=0.01,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        answer = completion.choices[0].message.content
        answer = answer.lstrip("【" + category_name+ "】")
        answer = answer.lstrip(category_name)
        answer = answer.lstrip("：")
        answer = answer.lstrip("\n")

        # どうしても「「なし」と出力します。」などと冗長に出力されてしまう場合は
        # 以下のように抑止することができる。
        # answer に「なし」という文字列が含まれていたら、空文字に置き換える
        # 例）「なし」と出力します。 -> なし
        # if answer.find("「なし」と出力します。") != -1 or answer.find("「なし」という文言を出力します。") != -1:
        #     answer = "なし"
        return "【" + category_name+ "】" + "\n" + answer + "\n\n" 
    
    def get_allergy(self, cursor, pi_item_id, jpn_item_name, patient_code):
        select_allergy_sql = """SELECT PI_ITEM_02, PI_ITEM_03
            FROM EATBPI
            WHERE PI_ACT_FLG = 1
            AND PI_ITEM_ID = ?
            AND PID = ?"""
        
        cursor.execute(select_allergy_sql, pi_item_id, patient_code)
        rows = cursor.fetchall() 
        records = ""
        for row in rows:
            records += jpn_item_name + "アレルギー：" + row[0] + "による" + row[1] + "\n"
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
        cursor.execute("""SELECT PID_NAME
            FROM [dbo].[EXTBDH1] WHERE ACTIVE_FLG = 1 AND PID = ?""", patient_code)
        rows = cursor.fetchall() 
        # Hit しなかった場合は、患者情報が見つからなかったというメッセージを返す
        if len(rows) == 0:
            return {"data_points": "test results", "answer": "患者情報が見つかりませんでした。", "thoughts": ""}

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
        records_soap = ""
        records_so = ""
        records_oa = ""
        records_a = ""
        records_p = ""
        for row in rows:
            datetime = self.get_datetime(row[0])
            # XML のまま GPT に投げても解釈してくれないこともないが、
            # XML のままだとトークン数をとても消費してしまうので、
            # XML を解釈して、平文に変換する。
            soap = DNP(row[1])
            day_of_soap = ""
            day_of_so = ""
            day_of_oa = ""
            day_of_a = ""
            day_of_p = ""
            if soap.S != "":
                day_of_soap += "S：" + soap.S + "\n\n"
                day_of_so += "S：" + soap.S + "\n\n"
            if soap.O != "":
                day_of_soap += "O：" + soap.O + "\n\n"
                day_of_so += "O：" + soap.O + "\n\n"
                day_of_oa += "O：" + soap.O + "\n\n"
            if soap.A != "":
                day_of_soap += "A：" + soap.A + "\n\n"
                day_of_oa += "A：" + soap.A + "\n\n"
                day_of_a += "A：" + soap.A + "\n\n"
            if soap.P != "":
                day_of_soap += "P：" + soap.P + "\n\n"
                day_of_p += "P：" + soap.P + "\n\n"

            if day_of_soap != "":
                records_soap += "記入日：" + datetime + "\n\n"
                records_soap += day_of_soap
                records_soap += "\n"
            if day_of_so != "":
                records_so += "記入日：" + datetime + "\n\n"
                records_so += day_of_so
                records_so += "\n"
            if day_of_oa != "":
                records_oa += "記入日：" + datetime + "\n\n"
                records_oa += day_of_oa
                records_oa += "\n"
            if day_of_a != "":
                records_a += "記入日：" + datetime + "\n\n"
                records_a += day_of_a
                records_a += "\n"
            if day_of_p != "":
                records_p += "記入日：" + datetime + "\n\n"
                records_p += day_of_p
                records_p += "\n"
        
        soap_prefix = "\n以下は医師の書いた SOAP です。\n\n"
        if records_soap != "":
            records_soap = soap_prefix + records_soap
        if records_so != "":
            records_so = soap_prefix + records_so
        if records_oa != "":
            records_oa = soap_prefix + records_oa
        if records_a != "":
            records_a = soap_prefix + records_a
        if records_p != "":
            records_p = soap_prefix + records_p        

        # QA No.11 対応により、看護記録は一旦削除する
        # # 看護記録の取得
        # cursor.execute(select_datax_sql,'ON01', patient_code)
        # rows = cursor.fetchall() 
        # is_first = True
        # for row in rows:
        #     if is_first:
        #         records += "\n以下は看護師の書いた SOAP です。\n\n"
        #     is_first = False
        #     print("------1")
        #     print(row[0])
        #     print("------2")
        #     print(row[1])
        #     print("------3")
        #     datetime = self.get_datetime(row[0])
        #     # XML のまま GPT に投げても解釈してくれないこともないが、
        #     # XML のままだとトークン数をとても消費してしまうので、
        #     # XML を解釈して、平文に変換する。
        #     soap = NNP(row[1])
        #     records += "記入日：" + datetime + "\n\n"
        #     if soap.S != "":
        #         records += "S：" + soap.S + "\n\n"
        #     if soap.O != "":
        #         records += "O：" + soap.O + "\n\n"
        #     if soap.A != "":
        #         records += "A：" + soap.A + "\n\n"
        #     if soap.P != "":
        #         records += "P：" + soap.P + "\n\n"
        #     records += "\n\n"
        # print(records)

        # TODO SV08, SV09 への対応

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

        ret = ""
        # 【アレルギー・不適応反応】​
        # ARG001（薬剤アレルギー）
        # ARG010（食物アレルギー）
        # ARG040（注意すべき食物）
        # ARGN10（その他アレルギー）

        allergy = ""
        # 薬剤アレルギー情報の取得
        allergy += self.get_allergy(cursor, 'ARG001', '薬剤', patient_code)
        
        # 食物アレルギー情報の取得
        allergy += self.get_allergy(cursor, 'ARG010', '食物', patient_code)

        # 注意すべき食物情報の取得
        allergy += self.get_allergy(cursor, 'ARG040', '注意すべき食物', patient_code)

        # その他アレルギー情報の取得
        allergy += self.get_allergy(cursor, 'ARGN10', 'その他原因物質', patient_code)
        if allergy != "":
            allergy = "【アレルギー・不適応反応】\n" + allergy + "\n"
        else :
            allergy = "【アレルギー・不適応反応】\n" + "なし\n\n"
        ret += allergy

        # 【主訴または入院理由】​
        ret += self.get_answer("主訴または入院理由", """あなたは医療事務アシスタントです。
カルテデータから退院時サマリの項目である【主訴または入院理由】​を作成してください。
作成した【主訴または入院理由】の部分のみ出力してください。前後の修飾文や、項目名は不要です。
カルテデータは、医師または看護師の書いた SOAP から構成されます。
カルテデータから【主訴または入院理由】が読み取れない場合、「なし」という文言を出力してください。
作成される文章は1000文字以内とします。
""", records_so)

        # 【入院までの経過】​
        ret += self.get_answer("入院までの経過", """あなたは医療事務アシスタントです。
カルテデータから退院時サマリの項目である【入院までの経過】​を作成してください。
【入院までの経過】​は、サブ項目として＜現病歴＞、＜既往歴＞、＜入院時身体所見＞、＜入院時検査所見＞から構成されます。
＜現病歴＞は S から、＜既往歴＞は S から、＜入院時身体所見＞は O から、＜入院時検査所見＞は O から始まる項目より抽出してください。
作成したサブ項目の部分のみ出力してください。前後の修飾文や、項目名は不要です。
カルテデータは、医師または看護師の書いた SOAP から構成されます。
カルテデータから各サブ項目が読み取れない場合、「なし」という文言を出力してください。
作成される文章は1000文字以内とします。
""", records_soap)

        # 【入院経過】​
        ret += self.get_answer("入院経過", """あなたは医療事務アシスタントです。
カルテデータから退院時サマリの項目である【入院経過】​を作成しようとしています。
カルテデータは、医師または看護師の書いた SOAP から構成されます。
カルテデータの A (assessment) の部分を入院経過として出力してください。
前後の修飾文や、項目名は不要です。
カルテデータから A (assessment) の部分が読み取れない場合、「なし」という文言を出力してください。
作成される文章は1000文字以内とします。
""", records_a)

        # 【退院時状況】​
        temp = self.get_answer("退院時の状況​​", """あなたは医療事務アシスタントです。
カルテデータから退院時サマリの項目である【退院時の状況】​を作成してください。
作成した【退院時の状況】の部分のみ出力してください。前後の修飾文や、項目名は不要です。
カルテデータは、医師または看護師の書いた SOAP から構成されます。
カルテデータから【退院時の状況】が読み取れない場合、「なし」という文言を出力してください。
作成される文章は1000文字以内とします。
""", records_oa)
        # tempの中の項目名である【退院時の状況】を【退院時状況】に変更する
        # これは、項目名に「の」を含めた方が、
        # GPT が生成する文章の正確性（「なし」を「なし」と出力）が高い傾向が見受けられたため。
        temp = temp.replace("【退院時の状況】​​", "【退院時状況】")
        ret += temp

        # 【退院時使用薬剤】​
        select_taiinji_shoho_sql = """
        SELECT EXTBOD1.IATTR, EXTBOD1.INAME, EXTBOD1.NUM, EXTBOD1.UNAME FROM EXTBDH1 
            INNER JOIN EXTBOD1 
            ON EXTBOD1.DOC_NO = EXTBDH1.DOC_NO
            AND EXTBDH1.DOC_K = 'H004'
			AND EXTBOD1.IATTR in ('HD1','HY1')
            AND EXTBDH1.ACTIVE_FLG = 1 
            AND EXTBOD1.ACTIVE_FLG = 1 
            AND EXTBDH1.PID = ?
			ORDER BY EXTBOD1.SEQ"""
        cursor.execute(select_taiinji_shoho_sql, patient_code)
        rows = cursor.fetchall() 
        medicine = ""
        for row in rows:
            if row[0] == "HY1":
                medicine += "　"
            medicine += row[1] + "　" + str(row[2]) + row[3] + "\n"
        if medicine != "":
            medicine = "【退院時使用薬剤】\n" + medicine + "\n"
        else:
            medicine = "【退院時使用薬剤】\n" + "なし" + "\n\n"
        ret += medicine

        # 【退院時方針】
        ret += self.get_answer("退院時方針", """あなたは医療事務アシスタントです。
カルテデータから退院時サマリの項目である【退院時方針】​を作成してください。
ただし、退院時方針は治療方針とは異なります。治療方針を含めないでください。
「退院時」や「退院」という文言を含まない文脈は、退院時方針ではないので注意してください。
作成した【退院時方針】の部分のみ出力してください。前後の修飾文や、項目名は不要です。
カルテデータは、医師または看護師の書いた SOAP から構成されます。
カルテデータから【退院時方針】が読み取れない場合、「なし」という文言を出力してください。
作成される文章は1000文字以内とします。
""", records_p)
        
        print(ret)
        print("\n\n\nカルテデータ：\n" + records_soap + allergy + medicine)
        return {"data_points": "test results", "answer": ret + "\n\n\nカルテデータ：\n" + records_soap + allergy + medicine, "thoughts": ""}


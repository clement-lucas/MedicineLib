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

    template_prefix = \
"You are an intelligent assistant helping doctors and medical staff with their medical information and research related questions. " \
"Answer the question using only the data provided in the information sources below. " \
"For tabular information return it as an html table. Do not return markdown format. " \
"Each source has a name followed by colon and the actual data, quote the source name for each piece of data you use in the response. " \
"For example, if the question is \"What color is the sky?\" and one of the information sources says \"info123: the sky is blue whenever it's not cloudy\", then answer with \"The sky is blue [info123]\" " \
"It's important to strictly follow the format where the name of the source is in square brackets at the end of the sentence, and only up to the prefix before the colon (\":\"). " \
"If there are multiple sources, cite each one in their own square brackets. For example, use \"[info343][ref-76]\" and not \"[info343,ref-76]\". " \
"Never quote tool names as sources." \
"If you cannot answer using the sources below, say that you don't know. " \
"\n\nYou can access to the following tools:"
    
    template_suffix = """
Begin!

Question: {input}

Thought: {agent_scratchpad}"""    

    CognitiveSearchToolDescription = "useful for searching the medical related information such as medical journal, medical research, etc."

#     prompt_prefix = """<|im_start|>system
# The assistant will answer questions about the contents of the medical file as source. Medical record data consists of the date of receipt and the contents of the description. Be brief in your answers.
# Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
# For tabular information return it as an html table. Do not return markdown format.
# Each source has a date followed by colon and the actual information, always include date for each fact you use in the response.At the end of the response, give the date of the data used in the format [yyyy/mm/dd].
# {follow_up_questions_prompt}
# {injected_prompt}
# Sources:
# {sources}
# <|im_end|>
# {chat_history}
# """

#     follow_up_questions_prompt_content = """Generate three very brief follow-up questions that the user would likely ask related with the answer. 
#     Use double angle brackets to reference the questions, e.g. <<Are there exclusions for prescriptions?>>.
#     Try not to repeat questions that have already been asked.
#     Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'"""

#     query_prompt_template = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base about medical journal and research.
#     Generate a search query based on the conversation and the new question. 
#     Do not include cited source filenames and discharge names e.g info.txt or doc.pdf in the search query terms.
#     Do not include any text inside [] or <<>> in the search query terms.
#     If the question is not in English, translate the question to English before generating the search query.

# Chat History:
# {chat_history}

# Question:
# {question}

# Search query:
# """
    def __init__(self, search_client: SearchClient, chatgpt_deployment: str, gpt_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.chatgpt_deployment = chatgpt_deployment
        self.gpt_deployment = gpt_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    # def retrieve(self, q: str, overrides: dict) -> any:
    #     use_semantic_captions = True if overrides.get("semantic_captions") else False
    #     top = overrides.get("top") or 3
    #     exclude_category = overrides.get("exclude_category") or None
    #     filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None

    #     if overrides.get("semantic_ranker"):
    #         r = self.search_client.search(q,
    #                                       filter=filter, 
    #                                       query_type=QueryType.SEMANTIC, 
    #                                       query_language="en-us", 
    #                                       query_speller="lexicon", 
    #                                       semantic_configuration_name="default", 
    #                                       top = top,
    #                                       query_caption="extractive|highlight-false" if use_semantic_captions else None)
    #     else:
    #         r = self.search_client.search(q, filter=filter, top=top)
    #     if use_semantic_captions:
    #         self.results = [doc[self.sourcepage_field] + ":" + nonewlines(" -.- ".join([c.text for c in doc['@search.captions']])) for doc in r]
    #     else:
    #         self.results = [doc[self.sourcepage_field] + ":" + nonewlines(doc[self.content_field][:250]) for doc in r]
    #     content = "\n".join(self.results)
    #     return content

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

        format = ""
        if document_name == "退院時サマリ":
            format = """
あなたは医師です。
カルテデータから退院時サマリを作成しようとしています。
カルテデータは、医師または看護師の書いた SOAP と、アレルギー情報から構成されます。
以下のフォーマットに沿って出力してください。フォーマット中の半角角括弧で囲まれた部分を置き換えてください。
例えば、フォーマットの中に[主訴]とあった場合、[主訴]と書いてある部分を、作成した主訴のテキストで置き換えてください。
カルテデータから読み取れることのできない項目に対しては「特記事項なし」という文言を出力してください。
医師の書いたSOAPを優先的に input としてください。作成される文章は1000文字以内とします。
フォーマット開始
【入院までの経過】
＜主訴＞
[主訴]

＜現病歴＞
[現病歴]

【入院時現症】
＜入院時身体所見＞
[入院時身体所見]

＜入院時検査所見＞
[入院時検査所見]

【既往歴・アレルギー】
＜既往歴＞
[既往歴]

＜アレルギー＞
[アレルギー]

【中間サマリー】
＜臨床経過＞
[臨床経過]

＜治療方針＞
[治療方針]
フォーマット終了

カルテデータ:
{sources}"""

        prompt = format.format(format_name=document_name, sources=records)
        print(prompt)
        #prompt = records.join("\nAnswer the following question from the text above in Japanese.\n\nQuestion:\n" + question + "\n\nAnswer:\n<|im_end|>")
        # STEP 3: Generate a contextual and content specific answer using the search results and chat history
        completion = openai.Completion.create(
            engine="davinci", 
            prompt=prompt, 
            temperature=overrides.get("temperature") or 0.7, 
            max_tokens=1024, 
            n=1,
            stop=None)
        
        print(completion.choices[0].text)
        return {"data_points": "test results", "answer": completion.choices[0].text + "\n\n\nカルテデータ：\n" + records, "thoughts": f"Searched for:<br>q test<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}

        # q=""

        # # Not great to keep this as instance state, won't work with interleaving (e.g. if using async), but keeps the example simple
        # self.results = None

        # # Use to capture thought process during iterations
        # cb_handler = HtmlCallbackHandler()
        # cb_manager = CallbackManager(handlers=[cb_handler])
        
        # acs_tool = Tool(name = "CognitiveSearch", func = lambda q: self.retrieve(q, overrides), description = self.CognitiveSearchToolDescription)
        # employee_tool = EmployeeInfoTool("Employee1")
        # tools = [acs_tool, employee_tool]

        # prompt = ZeroShotAgent.create_prompt(
        #     tools=tools,
        #     prefix=overrides.get("prompt_template_prefix") or self.template_prefix,
        #     suffix=overrides.get("prompt_template_suffix") or self.template_suffix,
        #     input_variables = ["input", "agent_scratchpad"])
        # llm = AzureOpenAI(deployment_name=self.openai_deployment, temperature=overrides.get("temperature") or 0.3, openai_api_key=openai.api_key)
        # chain = LLMChain(llm = llm, prompt = prompt)
        # agent_exec = AgentExecutor.from_agent_and_tools(
        #     agent = ZeroShotAgent(llm_chain = chain, tools = tools),
        #     tools = tools, 
        #     verbose = True, 
        #     callback_manager = cb_manager)
        # result = agent_exec.run(q)
                
        # # Remove references to tool names that might be confused with a citation
        # result = result.replace("[CognitiveSearch]", "").replace("[Employee]", "")

        # return {"data_points": self.results or [], "answer": result, "thoughts": cb_handler.get_and_reset_log()}

class EmployeeInfoTool(CsvLookupTool):
    employee_name: str = ""

    def __init__(self, employee_name: str):
        super().__init__(filename = "data/employeeinfo.csv", key_field = "name", name = "Employee", description = "useful for answering questions about the employee, their benefits and other personal information")
        self.func = self.employee_info
        self.employee_name = employee_name

    def employee_info(self, unused: str) -> str:
        return self.lookup(self.employee_name)

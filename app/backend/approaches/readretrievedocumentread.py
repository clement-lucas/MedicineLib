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

# Attempt to answer questions by iteratively evaluating the question to see what information is missing, and once all information
# is present then formulate an answer. Each iteration consists of two parts: first use GPT to see if we need more information, 
# second if more data is needed use the requested "tool" to retrieve it. The last call to GPT answers the actual question.
# This is inspired by the MKRL paper[1] and applied here using the implementation in Langchain.
# [1] E. Karpas, et al. arXiv:2205.00445
class ReadRetrieveDocumentReadApproach(Approach):

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
#     Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms.
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
        
    def run(self, document_name: str, patient_code:str, overrides: dict) -> any:

        print("run")
        print(document_name)
        print(patient_code)

        # SQL Server に接続する
        cnxn = pyodbc.connect(os.environ.get("SQL_CONNECTION_STRING"))
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

        format = ""
        if document_name == "紹介状":
            format = """
あなたは医師です。
以下のカルテデータにて書かれた人を違う医者に引き継ぐ必要があります。
以下のカルテデータにて書かれた人を他の医師に引継ぎのための紹介状を書いてください。
宛先の医師名は（宛先の医師名）とします。
ただし、作成される文章は1000文字以内とします。
カルテデータ:
{sources}"""
        elif document_name == "入院経過":
            format = """
あなたは医師です。
以下のカルテデータから入院経過を抽出してください。
ただし、作成される文章は1000文字以内とします。
カルテデータ:
{sources}"""
        elif document_name == "看護記録":
            format = """
あなたは医師です。
以下のカルテデータから看護記録を作成してください。
ただし、作成される文章は1000文字以内とします。
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
        return {"data_points": "test results", "answer": completion.choices[0].text, "thoughts": f"Searched for:<br>q test<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}

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

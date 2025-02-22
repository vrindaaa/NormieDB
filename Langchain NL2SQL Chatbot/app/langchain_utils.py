import os
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.memory import ChatMessageHistory

from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser

from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from prompts import final_prompt, answer_prompt

import streamlit as st

def get_llm():
    return ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=0,
        model_name="gpt-3.5-turbo"
    )

@st.cache_resource
def get_chain():
    print("Creating chain")
    db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
    llm = get_llm()
    generate_query = create_sql_query_chain(llm, db, final_prompt) 
    
    execute_query = QuerySQLDataBaseTool(db=db)
    
    # Modify the debug_query to accept the query directly
    def debug_query(query):
        print("Generated SQL Query:", query)
        result = execute_query.run(query)
        print("Query Result:", result)
        return result

    rephrase_answer = answer_prompt | llm | StrOutputParser()
    chain = (
        RunnablePassthrough.assign(table_names_to_use=select_table) |
        RunnablePassthrough.assign(query=generate_query).assign(
            result=lambda x: debug_query(x["query"])  # Use lambda instead of itemgetter
        )
        | rephrase_answer
    )
    return chain

def create_history(messages):
    history = ChatMessageHistory()
    for message in messages:
        if message["role"] == "user":
            history.add_user_message(message["content"])
        else:
            history.add_ai_message(message["content"])
    return history

def invoke_chain(query, messages):
    llm = get_llm()
    
    # Read table descriptions from CSV
    table_info = ""
    with open('database_table_descriptions.csv', 'r') as file:
        table_info = file.read()
    
    prompt = PromptTemplate(
        input_variables=["query", "table_info"],
        template="""You are a helpful assistant that generates SQL queries based on natural language requests.
        
        Here is information about the database tables:
        {table_info}
        
        Generate a SQL query for this request: {query}
        
        Return only the SQL query without any explanation."""
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(query=query, table_info=table_info)

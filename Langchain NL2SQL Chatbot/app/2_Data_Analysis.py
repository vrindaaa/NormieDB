import streamlit as st
from data_insights_agents import data_insights_crew
from tools import display_table

import streamlit as st
from openai import OpenAI
from sql_query_agents import sql_crew
from nosql_agents import sql_crew_nosql
import os
import pandas as pd
from pyprojroot import here
import yaml
from tools import display_table

import pandas as pd
from prepare_sql_db import PrepareSQLFromTabularData
from prepare_vector_db import PrepareVectorDB

db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")

st.set_page_config(
    page_title="Data Insights",
    page_icon="📈",
)

# Set OpenAI API key from Streamlit secrets
STREAMLIT = os.getenv("STREAMLIT")
client = OpenAI(api_key=STREAMLIT)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"
if "sql_query" not in st.session_state:
    st.session_state["sql_query"] = []
if "database_updates" not in st.session_state:
    st.session_state["database_updates"] = []
if "structured_data_analysis" not in st.session_state:
    st.session_state["structured_data_analysis"] = []
if "unstructured_data_analysis" not in st.session_state:
    st.session_state["unstructured_data_analysis"] = []


st.title("Data Insights")
st.write("Get different visualizations and insights from your sql database")

if "analysis_messages" not in st.session_state:
    st.session_state.analysis_messages = []

def display_analysis_content(content):
    if isinstance(content, list):
        for part in content:
            if part["type"] == "markdown":
                st.markdown(part["data"])
            elif part["type"] == "dataframe":
                st.dataframe(part["data"], use_container_width=True, hide_index=True)
            elif part["type"] == "visualization":
                st.plotly_chart(part["data"], use_container_width=True)
    else:
        st.markdown(content)

# Display analysis history
for message in st.session_state.analysis_messages:
    with st.chat_message(message["role"]):
        display_analysis_content(message["content"])

# Analysis input
if prompt := st.chat_input("What would you like to analyze?"):
    st.session_state.analysis_messages.append({"role": "user", "content": prompt, "type": "markdown"})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            try:
                response = data_insights_crew.kickoff(inputs={"query": prompt, "messages": []})
                st.session_state.analysis_messages.append({
                    "role": "assistant",
                    "content": [{"type": "markdown", "data": response}]
                })
                st.markdown(response)
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.session_state.analysis_messages.append({
                    "role": "assistant",
                    "content": [{"type": "markdown", "data": error_message}]
                }) 
                st.markdown(response)
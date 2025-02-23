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

st.title("SQL Database Chat Assistant")

# Set OpenAI API key from Streamlit secrets
STREAMLIT = os.getenv("STREAMLIT")
client = OpenAI(api_key=STREAMLIT)

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def sql_query_agent(inputs):
    response = sql_crew.kickoff(inputs=inputs)

    print("response", response)
    
    # Parse query and results
    if "QUERY:" in response and "RESULTS:" in response:
        parts = response.split("RESULTS:")
        query_part = parts[0].replace("QUERY:", "").strip()
        results = parts[1].strip().replace("`", "").replace(";\n", "\n").strip()
        
        # Display the SQL query
        st.markdown("The following query was executed:")
        st.markdown(query_part)
        # st.code(query_part, language="sql")
        
        # Display the results in a table
        display_table.run(results)
        
        # Save in session state
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
    else:
        st.markdown(response)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })


def get_recent_messages(messages, limit=5):
    """Get only the most recent messages to stay within token limits"""
    return messages[-limit:] if len(messages) > limit else messages

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "visualization" in message:
            st.components.v1.html(message["visualization"], height=500)
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask me anything about the database"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            try:
                recent_messages = get_recent_messages(st.session_state.messages)
                inputs = {
                    "query": prompt,
                    "messages": recent_messages
                }
                sql_query_agent(inputs)
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

uploaded_vector_file = st.file_uploader("Upload a PDF or TXT file for unstructured data", type=["pdf", "txt"])
if uploaded_vector_file:
    with open(here("Langchain NL2SQL Chatbot/configs/tools_config.yml")) as cfg:
        app_config = yaml.load(cfg, Loader=yaml.FullLoader)

    vector_upload_dir = "vector_uploads"
    if not os.path.exists(vector_upload_dir):
        os.makedirs(vector_upload_dir)
    file_path = os.path.join(vector_upload_dir, uploaded_vector_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_vector_file.getbuffer())
    st.success(f"File '{uploaded_vector_file.name}' uploaded successfully!")
    
    vector_pipeline = PrepareVectorDB(
         doc_dir=vector_upload_dir,
         chunk_size=app_config["unstructured_data"]["chunk_size"],
         chunk_overlap=app_config["unstructured_data"]["chunk_overlap"],
         embedding_model=app_config["unstructured_data"]["embedding_model"],
         vectordb_dir=app_config["unstructured_data"]["vectordb"],
         collection_name=app_config["unstructured_data"]["collection_name"]
    )
    vector_pipeline.run()


# File uploader section
uploaded_file = st.file_uploader("Upload a CSV or XLSX file to insert new data", type=["csv", "xlsx"])
if uploaded_file:
    # Save the uploaded file to a designated 'uploads' directory
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    
    # Run your pipeline to create the SQL database from the uploaded file(s)
    pipeline = PrepareSQLFromTabularData(upload_dir)
    pipeline.run_pipeline()

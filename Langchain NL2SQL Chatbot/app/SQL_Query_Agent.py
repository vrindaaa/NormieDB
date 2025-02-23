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

# Set OpenAI API key from Streamlit secrets
STREAMLIT = os.getenv("STREAMLIT")
client = OpenAI(api_key=STREAMLIT)

st.set_page_config(
    page_title="SQL Query Generation",
    page_icon="🤖",
    layout="wide"
)

# Set a default model
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

st.title("SQL Query Generation")
st.write("I can help you query your database using natural language! Just ask me what you want to know.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def sql_query_agent(inputs):
    try:
        response = sql_crew.kickoff(inputs=inputs)

        print("response", response)
        
        # Parse query and results
        if "QUERY:" in response and "RESULTS:" in response:
            parts = response.split("RESULTS:")
            query_part = parts[0].replace("QUERY:", "").strip()
            results = parts[1].strip().replace("`", "").replace(";\n", "\n").strip()
            
            # Display the SQL query
            st.markdown("The following query was executed:")
            st.markdown("```sql\n" + query_part + "\n```")
            # st.code(query_part, language="sql")
            
            # Display the results in a table
            df = display_table.run(results)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Save in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": "```sql\n" + query_part + "\n```",
                "type": "markdown"
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": df,
                "type": "dataframe"
            })
        else:
            st.markdown(response)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "type": "markdown"
            })
        
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        st.error(error_message)
        st.session_state.messages.append({
            "role": "assistant",
            "content": error_message,
            "type": "markdown"
        })


def get_recent_messages(messages, limit=5):
    return messages[-limit:] if len(messages) > limit else messages

def display_message_content():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "visualization" in message:
                st.components.v1.html(message["visualization"], height=500)
            elif message["type"] == "markdown":
                st.markdown(message["content"])
            elif message["type"] == "image":
                st.image(message["content"],
                        use_container_width=True)
            elif message["type"] == "dataframe":
                st.dataframe(
                    message["content"],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.markdown(message["content"])

# Display chat history
display_message_content()

# Chat input
if prompt := st.chat_input("Ask me anything about the database"):
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "markdown"})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            try:
                recent_messages = get_recent_messages(st.session_state.messages)
                inputs = {
                    "query": prompt,
                    "messages": []
                }
                sql_query_agent(inputs)
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": [{"type": "markdown", "data": error_message}]
                }) 
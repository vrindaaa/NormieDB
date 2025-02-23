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


# with tabs[1]:            
#     uploaded_file = st.file_uploader("Upload a CSV or XLSX file to create new tables", type=["csv", "xlsx"])
#     if uploaded_file:
#         # Save the uploaded file to a designated 'uploads' directory
#         upload_dir = "uploads"
#         if not os.path.exists(upload_dir):
#             os.makedirs(upload_dir)
#         file_path = os.path.join(upload_dir, uploaded_file.name)
#         with open(file_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())
#         st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
#         # Run your pipeline to create the SQL database from the uploaded file(s)
#         pipeline = PrepareSQLFromTabularData(upload_dir)
#         pipeline.run_pipeline()

# with tabs[2]:
#     def get_recent_messages(messages, limit=5):
#         """Get only the most recent messages to stay within token limits"""
#         return messages[-limit:] if len(messages) > limit else messages

#     # Display chat messages from history on app rerun
#     for message in st.session_state.structured_data_analysis:
#         with st.chat_message(message["role"]):
#             if "visualization" in message:
#                 st.components.v1.html(message["visualization"], height=500)
#             st.markdown(message["content"])

#     # Accept user input
#     if prompt := st.chat_input("Ask me anything about the database", key="sql_chat_input_chat"):
#         st.session_state.structured_data_analysis.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)
#         with st.chat_message("assistant"):
#             with st.spinner("Analyzing and visualizing data..."):
#                 try:
#                     recent_messages = get_recent_messages(st.session_state.structured_data_analysis)
#                     inputs = {
#                         "query": prompt,
#                         "content": recent_messages
#                     }
#                     response = sql_crew.kickoff(inputs=inputs)
                        
#                     # Check if response contains visualization specifications
#                     if "VISUALIZATION:" in response:
#                         parts = response.split("VISUALIZATION:")
#                         analysis = parts[0].replace("ANALYSIS:", "").strip()
#                         viz_specs = parts[1].strip()
                        
#                         # Parse visualization parameters
#                         viz_type = viz_specs.split("TYPE:")[1].split("\n")[0].strip()
#                         x_axis = viz_specs.split("X_AXIS:")[1].split("\n")[0].strip()
#                         y_axis = viz_specs.split("Y_AXIS:")[1].split("\n")[0].strip() if "Y_AXIS:" in viz_specs else None
#                         title = viz_specs.split("TITLE:")[1].split("\n")[0].strip()
#                         query = viz_specs.split("QUERY:")[1].strip()
                        
#                         # Get data from query
#                         data = pd.read_sql_query(query, engine)
                        
#                         # Create visualization
#                         viz_result = create_visualization(
#                             data=data,
#                             type_of_graph=viz_type,
#                             title=title,
#                             x=x_axis,
#                             y=y_axis
#                         )
                        
#                         # Display analysis
#                         st.markdown(analysis)
                        
#                         # Save in session state
#                         st.session_state.structured_data_analysis.append({
#                             "role": "assistant",
#                             "content": f"{analysis}\n\n{viz_result}"
#                         })
#                     else:
#                         st.markdown(response)
#                         st.session_state.structured_data_analysis.append({
#                             "role": "assistant",
#                             "content": response
#                         })
#                 except Exception as e:
#                     error_message = f"An error occurred: {str(e)}"
#                     st.error(error_message)
#                     st.session_state.structured_data_analysis.append({
#                         "role": "assistant",
#                         "content": error_message
#                     })


# st.markdown('<div class="option-buttons">', unsafe_allow_html=True)
# col1, col2, col3, col4 = st.columns(4)
# with col1:
#     if st.button("SQL Query", key="sql_query"):
#         st.session_state.active_option = "SQL Query"
#         st.rerun()
# with col2:
#     if st.button("Database Updates", key="database_updates"):
#         st.session_state.active_option = "Database Updates"
#         st.rerun()
# with col3:
#     if st.button("Structured Data Analysis", key="data_insights"):
#         st.session_state.active_option = "Structured Data Analysis"
#         st.rerun()
# with col4:
#     if st.button("Unstructured Data Analysis", key="other_act"):
#         st.session_state.active_option = "Unstructured Data Analysis"
#         st.rerun()
# st.markdown('</div>', unsafe_allow_html=True)

mode_descriptions = {
    "SQL Query": [
        "Generate and execute a SQL.",
    ],
    "Update Databases": [
        "Create new tables in the database and view the schema.",
    ],
    "Structured Data Analysis": [
        "Analyse data in relational databases.",
    ]
}


with st.sidebar:
    st.title("Query Vision")
    st.subheader("")
    st.markdown(
        """Descrription here"""
    )
    st.success("", icon="💚")

col1, col2, col3 = st.columns([0.2, 0.5, 0.2])

# User Configuration Sidebar
with st.sidebar:
    mode = st.radio(
        "Search Mode", options=["SQL Query", "Update Databases", "Structured Data Analysis"], index=0
    )
    st.info(mode_descriptions[mode][0])

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

def update_databases_agent(inputs):
    uploaded_file = st.file_uploader("Upload a CSV or XLSX file to create new tables", type=["csv", "xlsx"])
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

    # Add the functionality of the agent

def structured_data_analysis():
    pass            

def get_recent_messages(messages, limit=10):
    """Get only the most recent messages to stay within token limits"""
    return messages[-limit:] if len(messages) > limit else messages

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "visualization" in message:
            st.components.v1.html(message["visualization"], height=500)
        elif message["type"] == "markdown":
            st.markdown(message["content"])
        elif message["type"] == "dataframe":
            st.dataframe(
                message["content"],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.markdown(message["content"])

# Accept user input
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
                if mode == "SQL Query":
                    sql_query_agent(inputs)
                elif mode == "Update Databases":
                    update_databases_agent(inputs)
                elif mode == "Structured Data Analysis":
                    # structured_data_analysis_agent(inputs)
                    pass

            except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
                    st.error(error_message)
                    st.session_state.structured_data_analysis.append({
                        "role": "assistant",
                        "content": error_message
                    })

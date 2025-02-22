import streamlit as st
from openai import OpenAI
from agents import sql_crew
import os
import pandas as pd

from sqlalchemy import create_engine, inspect
import pandas as pd

db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")

class PrepareSQLFromTabularData:
    """
    A class that prepares a SQL database from CSV or XLSX files within a specified directory.
    """
    def __init__(self, files_dir) -> None:
        self.files_directory = files_dir
        self.file_dir_list = os.listdir(files_dir)
        self.db = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
        st.write("Connected to MySQL database at localhost.")

    def _prepare_db(self):
        for file in self.file_dir_list:
            full_file_path = os.path.join(self.files_directory, file)
            file_name, file_extension = os.path.splitext(file)
            if file_extension == ".csv":
                df = pd.read_csv(full_file_path)
            elif file_extension == ".xlsx":
                df = pd.read_excel(full_file_path)
            else:
                st.error(f"Unsupported file type for file: {file}")
                continue
            df.to_sql(file_name, self.db, index=False, if_exists="replace")
        st.success("All files have been saved into the SQL database.")

    def _validate_db(self):
        insp = inspect(self.engine)
        table_names = insp.get_table_names()
        st.info("Available tables in SQL DB: " + ", ".join(table_names))

    def run_pipeline(self):
        self._prepare_db()

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
        with st.spinner("Analyzing and visualizing data..."):
            try:
                recent_messages = get_recent_messages(st.session_state.messages)
                inputs = {
                    "query": prompt,
                    "messages": recent_messages
                }
                response = sql_crew.kickoff(inputs=inputs)
                
                # Check if response contains visualization specifications
                if "VISUALIZATION:" in response:
                    parts = response.split("VISUALIZATION:")
                    analysis = parts[0].replace("ANALYSIS:", "").strip()
                    viz_specs = parts[1].strip()
                    
                    # Parse visualization parameters
                    viz_type = viz_specs.split("TYPE:")[1].split("\n")[0].strip()
                    x_axis = viz_specs.split("X_AXIS:")[1].split("\n")[0].strip()
                    y_axis = viz_specs.split("Y_AXIS:")[1].split("\n")[0].strip() if "Y_AXIS:" in viz_specs else None
                    title = viz_specs.split("TITLE:")[1].split("\n")[0].strip()
                    query = viz_specs.split("QUERY:")[1].strip()
                    
                    # Get data from query
                    data = pd.read_sql_query(query, engine)
                    
                    # Create visualization
                    viz_result = create_visualization(
                        data=data,
                        type_of_graph=viz_type,
                        title=title,
                        x=x_axis,
                        y=y_axis
                    )
                    
                    # Display analysis
                    st.markdown(analysis)
                    
                    # Save in session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"{analysis}\n\n{viz_result}"
                    })
                else:
                    st.markdown(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

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

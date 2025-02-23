import streamlit as st
import os
import yaml
from pyprojroot import here
from prepare_sql_db import PrepareSQLFromTabularData
from prepare_vector_db import PrepareVectorDB

st.set_page_config(
    page_title="Database Schema Updates",
    page_icon="📊",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Update Databases")
st.write("Upload any csv or xlsx to your database")

# Structured data upload
# st.header("Upload Structured Data")
st.image('database_schema_diagram_old.jpeg')
uploaded_file = st.file_uploader("Upload CSV or XLSX file", type=["csv", "xlsx"])
if uploaded_file:
    try:
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        file_path = os.path.join(upload_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        pipeline = PrepareSQLFromTabularData(upload_dir)
        with st.spinner("Processing data..."):
            result = pipeline.run_pipeline()
            st.success(result)
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

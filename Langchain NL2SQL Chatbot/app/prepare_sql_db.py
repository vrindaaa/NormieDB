import os
import pandas as pd
from sqlalchemy import create_engine, inspect
import streamlit as st

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
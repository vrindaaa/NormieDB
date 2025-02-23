import os
import pandas as pd
from sqlalchemy import create_engine, inspect
import streamlit as st
from sqlalchemy import create_engine, MetaData
from sqlalchemy_schemadisplay import create_schema_graph

db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")

class PrepareSQLFromTabularData:
    """
    A class that prepares a SQL database from CSV or XLSX files within a specified directory.
    """
    
    def __init__(self, files_dir) -> None:
        print(db_user, db_password, db_host, db_name)
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

    def _visualize_schema(self):
        print("Visualizing schema")
        metadata = MetaData()
        metadata.reflect(bind=self.db)

        # Define styling options
        relation_options = {
            "color": "#008080",  # Foreign key relationship lines
            "penwidth": "1.5"
        }

        format_table_name = {
            "color": "blue",  # Green table name text
            "fontsize": 14,
            "bold": True
        }

        # Generate the schema graph with styling
        graph = create_schema_graph(metadata=metadata,
                                    engine=self.db,
                                    show_datatypes=False,
                                    show_indexes=False,
                                    rankdir='LR',
                                    concentrate=True,
                                    relation_options=relation_options,
                                    format_table_name=format_table_name)
        
        print("Graph created")

        graph.set("label",  "Schema Diagram -- "+ db_name) 
        graph.set("fontsize", "20")  
        graph.set("labelloc", "t")  
        graph.set("fontcolor", "black")




        graph.write_png('database_schema_diagram.png')
        print("HERE")
        st.image('database_schema_diagram.png')
        # st.session_state.messages.append({
        #     "role": "assistant",
        #     "content": "database_schema_diagram.png",
        #     "type": "image"
        # })

    def run_pipeline(self):
        self._prepare_db()
        self._visualize_schema()
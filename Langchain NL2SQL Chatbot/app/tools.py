from langchain.agents import Tool
from langchain_utils import invoke_chain, get_llm
from crewai_tools import tool
import os
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine

from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from plotly import graph_objects as go
import pandas as pd
import plotly.express as px
import streamlit as st
from pyprojroot import here
import yaml
from vector_db_query_tool import VectorDBQueryTool


with open(here("Langchain NL2SQL Chatbot/configs/tools_config.yml")) as cfg:
        app_config = yaml.load(cfg, Loader=yaml.FullLoader)

llm = get_llm()

db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")

connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
db = SQLDatabase.from_uri(connection_string)
engine = create_engine(connection_string)

vectordb_path = here(app_config["unstructured_data"]["vectordb"])
if os.path.exists(vectordb_path):
    vector_db_instance = Chroma(
        persist_directory=str(vectordb_path),
        collection_name=app_config["unstructured_data"]["collection_name"],
        embedding_function=OpenAIEmbeddings(model=app_config["unstructured_data"]["embedding_model"])
    )


@tool("list_tables")
def list_tables() -> str:
    """List the available tables in the database"""
    return ListSQLDatabaseTool(db=db).invoke("")

@tool("tables_schema")
def tables_schema(tables: str) -> str:
    """
    Input is a comma-separated list of tables, output is the schema and sample rows
    for those tables. Be sure that the tables actually exist by calling `list_tables` first!
    Example Input: table1, table2, table3
    """
    tool = InfoSQLDatabaseTool(db=db)
    return tool.invoke(tables)

@tool("execute_sql")
def execute_sql(sql_query: str) -> str:
    """Execute a SQL query against the database. Returns the result"""
    return QuerySQLDataBaseTool(db=db).invoke(sql_query)

@tool("check_sql")
def check_sql(sql_query: str) -> str:
    """
    Use this tool to double check if your query is correct before executing it. Always use this
    tool before executing a query with `execute_sql`.
    """
    return QuerySQLCheckerTool(db=db, llm=llm).invoke({"query": sql_query})

@tool("sql_tool")
def sql_tool(query: str, messages):
    """
    Tool to create and fetch the records using SQL
    """
    print("Using SQL Tool")
    print(query)
    print(messages)
    return invoke_chain(query, messages)

@tool("create_visualization")
def create_visualization(query: str, type_of_graph: str, title: str, x: str, y: str = None) -> str:
    """
    Create and display an interactive visualization using Plotly.
    
    Args:
        query (str): SQL query to get the data
        type_of_graph (str): Type of visualization to create. Options:
            - bar: For comparing categories
            - scatter: For showing relationships between numeric variables 
            - line: For time series or trend data
            - box: For showing distributions across categories
            - histogram: For showing distribution of a single variable
            - violin: For detailed distribution comparison
            - density_contour: For 2D density visualization
            - density_heatmap: For 2D density with heatmap
            - pie: For showing proportions of a whole
        title (str): Title for the visualization
        x (str): Column name for x-axis or categories
        y (str, optional): Column name for y-axis. Required for most plots except histogram and pie.
    """
    print("Creating visualization")
    print(query)
    print(type_of_graph)
    print(title)
    print(x)
    print(y)
    try:
        # Clean up the SQL query
        if isinstance(query, str):
            # Remove any surrounding quotes
            query = query.strip('"\'')
            # Replace escaped quotes
            query = query.replace('\\"', '"').replace("\\'", "'")
            # Handle line breaks and extra spaces
            query = ' '.join(query.split())
        
        print("Cleaned Query:", query)
        
        # Get data from SQL query
        data = pd.read_sql_query(query, engine)
        
        if data.empty:
            return "No data to visualize"

        print("DataFrame columns:", data.columns.tolist())
        print("Visualization type:", type_of_graph)
        print("Title:", title)
        print("X column:", x)
        print("Y column:", y)

        # Check if specified columns exist
        if x not in data.columns:
            return f"Error: Column '{x}' not found in data. Available columns: {', '.join(data.columns)}"
        if y is not None and y not in data.columns:
            return f"Error: Column '{y}' not found in data. Available columns: {', '.join(data.columns)}"

        plot_color = ["#ea5545", "#f46a9b", "#ef9b20", "#edbf33", "#ede15b", "#bdcf32", "#87bc45", "#27aeef", "#b33dc6"]

        graph_types = {
            'bar': px.bar,
            'scatter': px.scatter,
            'line': px.line,
            'box': px.box,
            'histogram': px.histogram,
            'violin': px.violin,
            'density_contour': px.density_contour,
            'density_heatmap': px.density_heatmap,
            'pie': px.pie
        }

        if type_of_graph not in graph_types:
            return f"Error: Unsupported graph type. Choose from: {', '.join(graph_types.keys())}"

        # Create visualization based on type
        if type_of_graph == 'violin':
            fig = graph_types[type_of_graph](data, x=x, y=y, title=title, color=x, color_discrete_sequence=plot_color)

        elif type_of_graph == 'pie':
            if y is None:
                data = data[x].value_counts().reset_index()
                data.columns = [x, 'count']
                fig = graph_types[type_of_graph](data, names=x, values='count', title=title, color_discrete_sequence=plot_color)
            else:
                fig = graph_types[type_of_graph](data, names=x, values=y, title=title, color_discrete_sequence=plot_color)
                
        elif type_of_graph == 'density_heatmap':
            if y is None:
                return f"Error: 'y' value must be provided for {type_of_graph} plots."
            fig = graph_types[type_of_graph](data, x=x, y=y, title=title, color_continuous_scale='viridis')
        else:
            if y is None and type_of_graph != 'histogram':
                return f"Error: 'y' value must be provided for {type_of_graph} plots."
            if type_of_graph == 'histogram':
                fig = graph_types[type_of_graph](data, x=x, title=title, color_discrete_sequence=plot_color)
            else:
                fig = graph_types[type_of_graph](data, x=x, y=y, title=title, color_discrete_sequence=plot_color, color=x)

        # Enhance the layout with better visibility settings
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'color': 'black'},
            showlegend=True,
            margin=dict(t=50, l=50, r=50, b=50)
        )
        
        # Update axes with better visibility
        if type_of_graph not in ['pie']:
            fig.update_xaxes(
                showline=True,
                linewidth=2,
                linecolor='black',
                title=x,
                gridcolor='lightgray'
            )
            if y:
                fig.update_yaxes(
                    showline=True,
                    linewidth=2,
                    linecolor='black',
                    title=y,
                    gridcolor='lightgray'
                )

        # Display the visualization with specific height and width
        st.plotly_chart(fig, use_container_width=True, height=600)
        
        return "Visualization has been created and displayed"
        
    except Exception as e:
        return f"Error creating visualization: {str(e)}"
 
@tool("lookup_vector_db")
def lookup_vector_db(query: str) -> str:
    """
    Input is a query string for searching the unstructured document store (vector DB).
    Returns the relevant document chunks or answers based on vector similarity.
    """
    tool = VectorDBQueryTool(vector_db=vector_db_instance)
    return tool.invoke(query)

@tool("decide_route")
def decide_route(query: str) -> str:
    """
    Input is a query string for searching the unstructured document store (vector DB).
    Returns "SQL" or "UnS"
    """
    print(query)
    return "SQL"

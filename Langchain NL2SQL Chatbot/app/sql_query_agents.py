from crewai import Agent, Crew, Process, Task
from crewai_tools import tool
from textwrap import dedent
from tools import sql_tool, list_tables, tables_schema, execute_sql, check_sql, display_table
from langchain_utils import get_llm
import streamlit as st

llm = get_llm()

sql_dev = Agent(
    role="Senior Database Developer",
    goal="Construct and execute SQL queries based on a request",
    backstory=dedent(
        """
        You are an experienced database engineer who is master at creating efficient and complex SQL queries.
        You have a deep understanding of how different databases work and how to optimize queries.
        
        Always use list_tables first to see available tables, then use tables_schema to understand
        the structure of the tables you need. Make sure to use the exact column names from the schema.
        
        Use the `sql_tool` to get the executed SQL response from it, by passing the `query` and `messages` to it.
        """
    ),
    llm=llm,
    tools=[list_tables, tables_schema, execute_sql, check_sql, sql_tool],
    allow_delegation=False,
)

extract_data = Task(
    description=dedent(
        """
        Extract data that is required for the query {query} with messages {messages}.
        
        First, use list_tables to see available tables.
        Then use tables_schema to understand the structure of relevant tables.
        Make sure to use exact column names from the schema in your SQL query.
        
        Format your response exactly like this:
        QUERY: <the SQL query with proper indentation and uppercase keywords>
        RESULTS: <the query results in semicolon-separated format csv>

        Important:
        - Your response should always be in the format of "QUERY: <sql query> RESULTS: <semicolon-separated csv of results>"
        - Make sure the csv is semicolon-separated and not comma-separated
        """
    ),
    expected_output="SQL query and semicolon-separated results csv",
    agent=sql_dev,
)

# Create the crew
sql_crew = Crew(
    agents=[sql_dev],
    tasks=[extract_data],
    process=Process.sequential,
    verbose=2,
    memory=False,
    output_log_file="crew.log",
)


# Export the crew and agent function
__all__ = ['sql_crew']

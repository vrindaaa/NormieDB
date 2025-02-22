from crewai import Agent, Crew, Process, Task
from crewai_tools import tool
from textwrap import dedent
from tools import decide_route, lookup_vector_db, sql_tool, list_tables, tables_schema, execute_sql, check_sql, create_visualization
from langchain_utils import get_llm

llm = get_llm()

vector_db_lookup_agent = Agent(
    role="Vector DB Lookup Agent",
    goal="You receive an unstructured query and return the relevant document chunks or answers by performing a vector database lookup.",
    backstory=dedent(
        """
        You specialize in semantic search and retrieval from unstructured data.
        Your expertise lies in converting unstructured queries into effective vector database searches,
        ensuring that the most relevant document chunks are returned based on vector similarity.
        """
    ),
    llm=llm,
    tools=[lookup_vector_db],
    allow_delegation=False,
)

extract_unstructured_data = Task(
    description=dedent(
        """
        Extract data that is required for the query {query} with messages {messages}.
        
        First, use the vector database lookup tool to perform a similarity search on the unstructured document store.
        Provide the query to the lookup_vector_db tool which will return the most relevant document chunks.
        
        Include both the query you used and its results in your response.
        Format your response as:
        QUERY: <the query used for the lookup>
        RESULTS: <the retrieved document chunks or answer>
        """
    ),
    expected_output="Vector DB query and its results",
    agent=vector_db_lookup_agent,
)

# Create the crew
sql_crew_nosql = Crew(
    agents=[vector_db_lookup_agent],
    tasks=[extract_unstructured_data],
    process=Process.sequential,
    verbose=2,
    memory=False,
    output_log_file="crew.log",
)

# Export the crew
__all__ = ['sql_crew_nosql']

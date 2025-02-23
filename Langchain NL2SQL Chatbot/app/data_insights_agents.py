from crewai import Agent, Crew, Process, Task
from crewai_tools import tool
from textwrap import dedent
from tools import decide_route, lookup_vector_db, sql_tool, list_tables, tables_schema, execute_sql, check_sql, create_visualization
from langchain_utils import get_llm

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

data_analyst = Agent(
    role="Senior Data Analyst",
    goal="You receive data from the database developer and analyze it",
    backstory=dedent(
        """
        You have deep experience with analyzing datasets using Python.
        Your work is always based on the provided data and is clear,
        easy-to-understand and to the point. You have attention
        to detail and always produce very detailed work (as long as you need).
    """
    ),
    llm=llm,
    allow_delegation=False,
)

report_writer = Agent(
    role="Senior Report Editor",
    goal="Write an executive summary type of report based on the work of the analyst",
    backstory=dedent(
        """
        Your writing still is well known for clear and effective communication.
        You always summarize long texts into bullet points that contain the most
        important details.
        """
    ),
    llm=llm,
    allow_delegation=False,
)

visualization_expert = Agent(
    role="Data Visualization Expert",
    goal="Create meaningful visualizations from the provided SQL query results",
    backstory=dedent(
        """
        You are an expert in data visualization. Your role is to examine the SQL query 
        and determine the most appropriate visualization type based on both the data structure
        and the user's original question. You understand data types and how to best represent 
        different kinds of data relationships.

        Available visualization types:
        - bar: For comparing categories
        - scatter: For showing relationships between numeric variables 
        - line: For time series or trend data
        - box: For showing distributions across categories
        - histogram: For showing distribution of a single variable
        - violin: For detailed distribution comparison
        - density_contour: For 2D density visualization
        - density_heatmap: For 2D density with heatmap
        - pie: For showing proportions of a whole

        Run the `create_visualization` tool with the appropriate parameters to create the visualization.
        """
    ),
    llm=llm,
    tools=[create_visualization],
    allow_delegation=False,
)

extract_data = Task(
    description=dedent(
        """
        Extract data that is required for the query {query} with messages {messages}.
        
        First, use list_tables to see available tables.
        Then use tables_schema to understand the structure of relevant tables.
        Make sure to use exact column names from the schema in your SQL query.
        
        Include both the SQL query you used and its results in your response.
        Format your response as:
        QUERY: <the SQL query>
        RESULTS: <the query results>
        """
    ),
    expected_output="SQL query and its results",
    agent=sql_dev,
)

routing_task = Task(
    description=dedent(
        """
        Analyze the incoming query to determine whether it requires data from the SQL database or from unstructured documents.
        Return either "SQL" or "Unstructured".
        """
    ),
    expected_output="Data source indicator"
)

visualize_data = Task(
    description=dedent(
        """
        Review the SQL query and results, then create an appropriate visualization.
        
        You will receive:
        QUERY: <the SQL query>
        RESULTS: <the query results>

        Your task is to directly execute the create_visualization tool with appropriate parameters based on the data.
        Choose parameters based on:
        - For time-based data → use line chart
        - For category comparisons → use bar chart
        - For numeric relationships → use scatter plot
        - For distributions → use box or histogram
        - For proportions → use pie chart
        """
    ),
    expected_output="Visualization tool execution",
    agent=visualization_expert,
    context=[extract_data],
)

analyze_data = Task(
    description=dedent(
        """
        Analyze the data from the database and the visualization if one was created.
        Provide insights about the data and how the visualization helps understand it better.
        """
    ),
    expected_output="Detailed analysis text incorporating both data and visualization insights",
    agent=data_analyst,
    context=[extract_data, visualize_data],
)

write_report = Task(
    description=dedent(
        """
        Write an executive summary of the report from the analysis and visualization. 
        If there's a visualization, reference it in your summary.
        The report must be less than 100 words.
        """
    ),
    expected_output="Markdown report",
    agent=report_writer,
    context=[analyze_data],
)

routing_expert = Agent(
    role="Decide the route based on the query",
    goal="Decide whether to return SQL or Unstructured",
    backstory=dedent(
        """
        You are an expert in decision making. When an input is given you have to decide whether to return SQL or UnS

        Run the `decide_route` tool with the input query to get a response.
        """
    ),
    llm=llm,
    tools=[decide_route]
)

# Create the crew
sql_crew = Crew(
    agents=[sql_dev, visualization_expert, data_analyst, report_writer],
    tasks=[extract_data, visualize_data, analyze_data, write_report],
    process=Process.sequential,
    verbose=2,
    memory=False,
    output_log_file="crew.log",
)

# Export the crew
__all__ = ['sql_crew']

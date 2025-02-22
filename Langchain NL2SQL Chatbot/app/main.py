import streamlit as st
from openai import OpenAI
from agents import sql_crew
import os
import pandas as pd

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


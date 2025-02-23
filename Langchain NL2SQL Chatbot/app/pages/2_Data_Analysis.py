import streamlit as st
from data_insights_agents import data_insights_crew
from tools import display_table

st.set_page_config(
    page_title="Data Visualization and Analysis",
    page_icon="📈",
)

st.title("Data VIsualization and Analysis")
st.write("Get insights and visualizations from your data")

if "analysis_messages" not in st.session_state:
    st.session_state.analysis_messages = []

def display_analysis_content(content):
    if isinstance(content, list):
        for part in content:
            if part["type"] == "markdown":
                st.markdown(part["data"])
            elif part["type"] == "dataframe":
                st.dataframe(part["data"], use_container_width=True, hide_index=True)
            elif part["type"] == "visualization":
                st.plotly_chart(part["data"], use_container_width=True)
    else:
        st.markdown(content)

# Display analysis history
for message in st.session_state.analysis_messages:
    with st.chat_message(message["role"]):
        display_analysis_content(message["content"])

# Analysis input
if prompt := st.chat_input("What would you like to analyze?"):
    st.session_state.analysis_messages.append({
        "role": "user",
        "content": [{"type": "markdown", "data": prompt}]
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            try:
                response = data_insights_crew.kickoff(inputs={"query": prompt})
                st.session_state.analysis_messages.append({
                    "role": "assistant",
                    "content": [{"type": "markdown", "data": response}]
                })
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.session_state.analysis_messages.append({
                    "role": "assistant",
                    "content": [{"type": "markdown", "data": error_message}]
                }) 
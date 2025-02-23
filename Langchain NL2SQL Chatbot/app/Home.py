import streamlit as st

st.set_page_config(
    page_title="SQL Assistant Hub",
    page_icon="🏠",
    layout="wide"
)

# Title and Introduction
st.title("🤖 SQL Assistant Hub")

# Brief introduction
st.markdown("""
### Welcome to your AI-Powered SQL Assistant!

This application helps you interact with your database using natural language, making data analysis accessible to everyone.
""")

# Features section
st.markdown("---")
st.header("🎯 Key Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🔍 QueryVision
    Ask questions in plain English and get SQL queries and results instantly.
    
    **Example Questions:**
    - Show me the top 10 customers
    - What were last month's sales?
    - Find all orders over $1000
    """)

with col2:
    st.markdown("""
    ### 📊 Database Management
    Easily update and manage your database structure.
    
    **Capabilities:**
    - Upload CSV/Excel files
    - Automatic table creation
    - Schema visualization
    """)

with col3:
    st.markdown("""
    ### 📈 Data Analysis
    Get insights and visualizations from your data.
    
    **Features:**
    - Trend analysis
    - Data visualization
    - Statistical summaries
    """)

# How to use section
st.markdown("---")
st.header("🚀 Getting Started")

st.markdown("""
1. **SQL Query Generation**: Navigate to the SQL Query page to ask questions about your data
2. **Autonomous Database Updates**: Use the Update Databases page to upload new data files
3. **Data Insights**: Visit the Data Analysis page for insights and visualizations

Select your desired feature from the sidebar to get started!
""")

# Example usage
st.markdown("---")
st.header("💡 Example Usage")

with st.expander("See example queries"):
    st.markdown("""
    Try these sample queries in the SQL Query Generation page:
    
    - "Show me the total sales for each product category"
    - "Who are our top 5 customers by revenue?"
    - "What is the average order value by month?"
    - "List all transactions above $500"
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit, LangChain, and OpenAI</p>
</div>
""", unsafe_allow_html=True) 
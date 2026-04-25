import streamlit as st
import pandas as pd
import altair as alt
import re
import duckdb
import json
from sqlalchemy import create_engine, inspect, text
from smolagents import InferenceClientModel

def run_db_app():
    def connect_to_database(db):
        global engine, model
        DB_URL = "mysql+pymysql://root:123@localhost/"+db
        engine = create_engine(DB_URL)
        model = InferenceClientModel("meta-llama/Meta-Llama-3-8B-Instruct")

    def get_all_table_schemas() -> str:
        inspector = inspect(engine)
        all_schemas = []
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            col_text = ", ".join([f"{c['name']} ({c['type']})" for c in columns])
            all_schemas.append(f"Table '{table_name}' columns: {col_text}")
        return "\n".join(all_schemas)

    def generate_ai_plan(global_schema: str, user_query: str):
        prompt = f"""
        You are a MySQL expert AND a data visualization expert. 
        Database Schema:
        {global_schema}

        User Request: {user_query}
        Decide the BEST visualization type based on the data:

        Rules:
        - Use "bar"  for comparisons (top countries, counts, rankings)
        - Use "line"  for trends or ordered categories (time, continents, progression)
        - Use "scatter"  for relationships between two numeric variables (e.g., GDP vs LifeExpectancy)
        - Use "none"  if visualization is not meaningful

        Return ONLY a JSON object. No preamble, no markdown blocks.
        Example Format:
        {{
            "sql": "SELECT ...",
            "chart_type": "bar",
            "x": "column_name",
            "y": "column_name",
            "reasoning": "Joined A and B on id"
        }}
        """
        response = model.generate([{"role": "user", "content": prompt}], temperature=0.0)
        
        try:
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
            return None
        except Exception as e:
            print(f"JSON Parsing Error: {e}")
            return None

    def run_query(query: str):
        with engine.connect() as con:
            return pd.read_sql(text(query), con)

    def generate_narrative(user_query, df, reasoning):
        data_sample = df.head(5).to_json()
        prompt = f"User asked: {user_query}. Logic used: {reasoning}. Data: {data_sample}. Summarize the finding in 1 sentence.Do not give python code"
        response = model.generate([{"role": "user", "content": prompt}])
        return response.content.strip()

    #UI when Database is selected
    st.set_page_config(page_title="Query Genie", layout="wide")
    st.write("**Database Genie🔮**")
    with st.sidebar:
        st.header("Database Intelligence")
        db = st.text_input(label='Enter the Database name : ')
        connect_to_database(db)
    
        if st.button("🔄 Refresh Schema Map"):
            st.cache_data.clear()
        st.success(f"Connected to: {db} database")

    user_input = st.chat_input("e.g., 'Find student names with marks > 90 in the Computer Dept'")

    if user_input:
        with st.spinner("🧠 Mapping tables and writing query..."):
            try:
                st.write(f"**User Prompt** : {user_input}")
                full_schema = get_all_table_schemas()
                
                plan = generate_ai_plan(full_schema, user_input)
                if not plan:
                    st.error("AI failed to generate a plan.")
                    st.stop()

                df = run_query(plan['sql'])
                
                narrative = generate_narrative(user_input, df, plan.get('reasoning', ''))

                st.subheader("💡 Analysis Insight")
                st.info(f"**Strategy:** {plan.get('reasoning')}\n\n**Result:** {narrative}")

                col_table, col_viz = st.columns(2)
                with col_table:
                    st.subheader("📋 Query Results")
                    st.code(plan['sql'], language="sql")
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Results", data=csv, file_name="query_results.csv", mime="text/csv")

                with col_viz:
                    st.subheader("📈 Visualization")
                    if plan['chart_type'] != "none" and not df.empty:
                        x, y = plan.get('x'), plan.get('y')
                        if plan["chart_type"] != "none" and not df.empty and x in df.columns and y in df.columns:
                            if plan["chart_type"] == "bar":
                                c = alt.Chart(df).mark_bar().encode(x=x, y=y, tooltip=list(df.columns))
                            elif plan["chart_type"] == "line":
                                c = alt.Chart(df).mark_line(point=True).encode(x=x, y=y, tooltip=list(df.columns))
                            else:
                                c = alt.Chart(df).mark_circle(size=60).encode(x=x, y=y, tooltip=list(df.columns))
                        
                            st.altair_chart(c.interactive(), use_container_width=True)
                    else:
                        st.write("No visual representation requested or columns not found.")

            except Exception as e:
                st.error(f"Error: {e}")

def run_csv_app():
    #Model Loading
    model = InferenceClientModel("meta-llama/Meta-Llama-3-8B-Instruct")


    #Genertor - Schema
    def get_csv_schema(df):
        cols = ", ".join([f"{col} ({df[col].dtype})" for col in df.columns])
        return f"Table 'data' columns: {cols}"


    #AI Planner
    def generate_ai_plan(global_schema: str, user_query: str):
        prompt = f"""
        You are a SQL expert AND data visualization expert.

        Dataset Schema:
        {global_schema}

        User Request: {user_query}

        IMPORTANT:
        - Dataset is a CSV table named 'data'
        - Write SQL using 'data'

        Visualization Rules:
        - bar → comparisons
        - line → trends
        - scatter → relationships
        - none → if not needed

        Return ONLY JSON:
        {{
            "sql": "SELECT ...",
            "chart_type": "...",
            "x": "...",
            "y": "...",
            "reasoning": "..."
        }}
        """

        response = model.generate([{"role": "user", "content": prompt}], temperature=0.0)

        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        return json.loads(match.group()) if match else None


    #Execute SQL on CSV
    def run_query_csv(df, query):
        duckdb.register("data", df)
        return duckdb.query(query).to_df()


    #Narrative
    def generate_narrative(user_query, df, reasoning):
        sample = df.head(5).to_json()
        prompt = f"User asked: {user_query}. Logic: {reasoning}. Data: {sample}. Summarize in 1 sentence."
        response = model.generate([{"role": "user", "content": prompt}])
        return response.content.strip()


    #UI for CSV
    st.set_page_config(page_title="CSV Genie", layout="wide")
    st.write("**CSV Genie✨**")
    st.write("Query any CSV using natural language!")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        df_csv = pd.read_csv(uploaded_file)
        st.success("CSV loaded successfully!")

        user_input = st.chat_input("Ask something about your data...")

        if user_input:
            st.write(f"**User Prompt** : {user_input}")
            with st.spinner("🧠 Analyzing..."):
                try:
                    schema = get_csv_schema(df_csv)

                    plan = generate_ai_plan(schema, user_input)
                    if not plan:
                        st.error("AI failed.")
                        st.stop()

                    df = run_query_csv(df_csv, plan["sql"])
                    narrative = generate_narrative(user_input, df, plan.get("reasoning", ""))

                    st.subheader("💡 Insight")
                    st.info(narrative)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📋 Data")
                        st.code(plan["sql"], language="sql")
                        st.dataframe(df)

                    with col2:
                        st.subheader("📈 Visualization")

                        x, y = plan.get("x"), plan.get("y")

                        if plan["chart_type"] != "none" and x in df.columns and y in df.columns:
                            if plan["chart_type"] == "bar":
                                chart = alt.Chart(df).mark_bar().encode(x=x, y=y)
                            elif plan["chart_type"] == "line":
                                chart = alt.Chart(df).mark_line(point=True).encode(x=x, y=y)
                            else:
                                chart = alt.Chart(df).mark_circle(size=60).encode(x=x, y=y)

                            st.altair_chart(chart.interactive(), use_container_width=True)
                        else:
                            st.write("No visualization available.")

                except Exception as e:
                    st.error(f"Error: {e}")


st.set_page_config(page_title="Query Genie", layout="wide")

st.title("Query Genie✨")
st.write("Your ultimate Text to SQL Tool!")

with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.radio("Choose mode", ["Database", "CSV"])

if mode == "Database":
    run_db_app()
else:
    run_csv_app()
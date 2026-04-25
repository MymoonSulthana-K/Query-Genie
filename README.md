# Query Genie

Query Genie is a Streamlit-based Text-to-SQL app that lets users ask questions about databases or CSV files in natural language. It uses an LLM-powered SQL generation workflow to inspect schemas, generate structured query plans, execute SQL, summarize results, and create suitable visualizations when the answer benefits from a chart.

## Features

- Natural language to SQL query generation
- LLM-based query planning using structured JSON outputs
- Schema-aware prompting for database and CSV analysis
- Automated chart recommendation based on query intent
- Two query modes:
  - **Database mode** for MySQL databases
  - **CSV mode** for uploaded CSV files
- Automatic schema detection
  - Reads table and column metadata from MySQL
  - Builds a schema from uploaded CSV column names and data types
- AI-generated query plan with:
  - SQL query
  - Suggested visualization type
  - X and Y chart columns
  - Reasoning behind the query strategy
- Query execution
  - Uses SQLAlchemy for MySQL queries
  - Uses DuckDB for SQL queries on CSV files
- AI-generated one-sentence result summary
- Interactive result table display
- Automatic visualizations with Altair:
  - Bar charts for comparisons
  - Line charts for trends
  - Scatter plots for numeric relationships
- CSV download for database query results
- Streamlit chat-style input for asking data questions

## Screenshots

Database Mode:
<img width="1920" height="1435" alt="Query-Genie scatter" src="https://github.com/user-attachments/assets/b1629489-a462-4d00-b1e8-7b5d21a612da" />

CSV Mode:
<img width="1929" height="918" alt="image" src="https://github.com/user-attachments/assets/49488a4f-127a-45fd-b511-83ca16f8ab46" />

## How It Works

Query Genie has two main workflows.

In **Database mode**, the app connects to a local MySQL database, inspects all available tables, collects their column schemas, and sends that schema with the user question to an AI model. The model returns a JSON plan containing SQL, visualization details, and reasoning. The SQL is executed against the database, then the app displays the result, summary, and chart.

In **CSV mode**, the user uploads a CSV file. The app reads the file into a Pandas DataFrame, registers it as a DuckDB table named `data`, and asks the AI model to generate SQL for that table. The result is shown as a table with an optional visualization and summary.

## Tech Stack

- Python
- Streamlit
- Pandas
- DuckDB
- SQLAlchemy
- PyMySQL
- Altair
- smolagents `InferenceClientModel`
- Meta Llama 3 8B Instruct model

## Installation

Install the required Python packages:

```bash
pip install streamlit pandas altair duckdb sqlalchemy pymysql smolagents
```

## Usage

Run the app with:

```bash
streamlit run main.py
```

Then choose a mode from the sidebar.

### Database Mode

1. Select **Database** mode.
2. Enter the MySQL database name.
3. Ask a question in natural language.
4. View the generated SQL, query results, insight, and visualization.
5. Download the result as a CSV file if needed.

The database connection in `main.py` uses:

```python
mysql+pymysql://root:123@localhost/<database_name>
```

Update the username, password, or host in `main.py` if your MySQL setup is different.

### CSV Mode

1. Select **CSV** mode.
2. Upload a CSV file.
3. Ask a question about the data.
4. View the generated SQL, results, insight, and visualization.

## Example Prompts

```text
Show the top 10 countries by population.
```

```text
Find students with marks greater than 90 in the Computer department.
```

```text
Compare average sales by region.
```

```text
Show the trend of revenue over time.
```

```text
Plot GDP against life expectancy.
```

## Notes

- The app expects the AI model to return a JSON object with SQL and visualization metadata.
- CSV queries should use the table name `data`.
- Database mode is designed for MySQL.
- Visualization is skipped when the model returns `chart_type` as `none` or when the selected chart columns are not present in the query result.

import streamlit as st
import psycopg2
import pandas as pd
import pandas.io.sql as sqlio
import altair as alt
from environs import Env
from sqlalchemy import create_engine

from PIL import Image

env = Env()

# Some Postgres data processing came from:
# @source https://docs.streamlit.io/knowledge-base/tutorials/databases/postgresql

# Initialize connection. Return a SQLAlchemy engine.
# Uses st.cache to only run once.
# @st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
def init_connection():
    db_host = env.str('POSTGRES_HOST')
    db_user = env.str('POSTGRES_USER')
    db_port = env.int('POSTGRES_PORT')
    db_name = env.str('POSTGRES_DB')
    db_pass = env.str('POSTGRES_PASSWORD')
    engine = create_engine(f'postgresql://{db_user}:{db_pass}@{db_host:{db_port}/{db_name}}')
    conn = engine.connect()
    # Stop using psycopg2 directly due to inability to use read_sql_table.
    # psycopg2.connect(**st.secrets["postgres"])
    return conn

conn = init_connection()



# Perform query.
# Uses st.cache to only rerun when the query changes or after 10 min.
# @st.cache(ttl=600)
def run_query(query, return_as='df'):
    # Return as a dataframe.
    if return_as == 'df':
        return sqlio.read_sql_query(query, conn)

    # Return as Python list.
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def main():
    # @todo - Get Stride logo to show up.
    st.title("Stride Funding - Data Engineering")

    # @todo - Order the states alphabetically.
    st.write("# Zip Codes by State")
    states_query = 'SELECT count(1), "State" from zip_code_data GROUP BY "State" ORDER BY "State" ASC'
    result = run_query(states_query, return_as='list')

    for row in result:
        st.write(f"{row[1]} => {row[0]} zip codes")

    #states_df = run_query(states_query)
    states_df = pd.read_sql_table("zip_code_data", conn)
    zip_by_state_chart = alt.Chart(states_df.groupby['State'].count().reset_index(name="count")).mark_circle().encode(
        x = 'State', y = 'count')
    st.altair_chart(zip_by_state_chart, use_container_width=True)
    #st.bar_chart(states_df)

    st.write("This is a normal text")


if __name__ == '__main__':
    main()

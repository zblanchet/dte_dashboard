import streamlit as st
import psycopg2
import pandas as pd
import pandas.io.sql as sqlio
import altair as alt
from environs import Env
from sqlalchemy import create_engine, text


env = Env()

# Some Postgres data processing came from:
# @source https://docs.streamlit.io/knowledge-base/tutorials/databases/postgresql


@st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
def init_connection():
    """
    Initialize connection with the SQLAlchemy engine

    Uses st.cache to only run once.
    """
    db_host = env.str("POSTGRES_HOST")
    db_user = env.str("POSTGRES_USER")
    db_port = env.int("POSTGRES_PORT")
    db_name = env.str("POSTGRES_DB")
    db_pass = env.str("POSTGRES_PASSWORD")
    engine = create_engine(
        f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )
    return engine.connect()


def main():

    conn = init_connection()

    states_df = pd.read_sql_table(
        "zip_code_data", conn
    )  # TODO: Order states east-to-west
    zip_by_state_df = (
        states_df.groupby("State")["State"]
        .count()
        .reset_index(name="Total Number of Zipcodes")
    )
    zip_by_state_chart = (
        alt.Chart(zip_by_state_df)
        .mark_circle()
        .encode(x="State:N", y="Total Number of Zipcodes:Q")
    )

    # TODO: Render Stride logo
    st.title("Stride Funding - Data Engineering")
    st.write("## Zipcodes by State")
    st.altair_chart(zip_by_state_chart, use_container_width=True)
    st.table(zip_by_state_df)
    st.write("© Stride Funding, Inc. 2022")


if __name__ == "__main__":
    main()

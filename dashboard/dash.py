import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid
import pandas as pd
from environs import Env
from sqlalchemy import create_engine


env = Env()

# Some Postgres data processing came from:
# @source https://docs.streamlit.io/knowledge-base/tutorials/databases/postgresql

# establish db connection
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

    # DASHBOARD ITEMS:
    # 1. Top 50 Programs by DTE
    # 2. Top CS Institutions by DTE
    # 3. Most Valuable Metro Areas
    #     - Top 10 Cities with largest number of Top 500 Programs by DTE
    # 4. Filtered List
    #     - Ability to filter programs or institutions by name

    ## Dataframes

    # 1. calculate average dte ratio of each distinct Program
    # Done using pandas because it was nice to use python and a different tool
    programs_df = pd.read_sql_table(
        "CollegeScorecard_Programs_DTE_Subset", conn
    )
    # st.table(programs_df)
    pg_1_columns = ["CIPDESC","DTE_RATIO"]
    st_1_columns = ["Program","Avg DTE Ratio"]

    st_1_df = (
        programs_df[programs_df.columns.intersection(pg_1_columns)]
        .rename(columns={pg_1_columns[i]: st_1_columns[i] for i in range(len(pg_1_columns))}) # rename columns to something useful
        .groupby(["Program"]).mean()
        .sort_values(by=["Avg DTE Ratio"])
        .reset_index(level=["Program"])
        .head(50)
    )
    st_1_df.index += 1 # hacky way to make the index start at 1 on the dashboard

    # 2. Top CS institutions by DTE
    # I quickly began to wish that I had imported the data differently to postgres because quoting the columns was tedious.
    st_2_query = """
    select 
    "INSTNM" as Institution, 
    AVG("DTE_RATIO") as DTE
    from "CollegeScorecard_Programs_DTE_Subset" 
    where "CIPDESC" = 'Computer Science.' 
    group by "INSTNM", "DTE_RATIO" 
    order by "DTE_RATIO" asc
    limit 100;
    """
    st_2_df = pd.read_sql_query(st_2_query,conn)
    st_2_df.index += 1

    # I wrote this query to help me remember some stuff but I think it's interesting
    # 3A. 
    # """
    # select 
    # distinct "CITY", 
    # "STABBR", 
    # count("INSTNM") over (partition by "CITY","STABBR") as schools 
    # from "CollegeScorecard_Institution_Subset" 
    # order by "STABBR","CITY";
    # """

    # 3.
    st_3_query = """
    with cte as (
        select 
        inst."CITY", 
        inst."STABBR", 
        "DTE_RATIO" 
        from "CollegeScorecard_Programs_DTE_Subset" prog
        left join "CollegeScorecard_Institution_Subset" inst 
        on prog."UNITID" = inst."UNITID"
        order by "DTE_RATIO" asc 
        limit 500) 
    select 
    distinct "CITY" as City, 
    "STABBR" as State, 
    count("CITY") over (partition by "CITY","STABBR") as Count
    from cte
    order by Count desc 
    limit 10;
    """
    st_3_df = pd.read_sql_query(st_3_query,conn)
    st_3_df.index += 1
 
    #4 Filtered List
    # Incorporates all the required columns
    st_4_query = """
    select
        inst."INSTNM" as Institution,
        inst."UNITID"::varchar(255) as unitid,
        prog."OPEID6"::varchar(255) as opeid6,
        inst."CITY" as City,
        inst."STABBR" as State,
        CASE
            WHEN length(inst."ZIP") > 5 THEN SUBSTRING(inst."ZIP",1,5) 
            WHEN length(inst."ZIP") < 5 THEN LPAD(inst."ZIP", 5, '0')
            ELSE inst."ZIP"
        END as Zip_Code,
        prog."CIPCODE"::varchar(255) as Program_Code,
        prog."CIPDESC" as Program_Name,
        prog."DTE_RATIO" as Debt_to_Earnings_DTE,
        prog."EARN_MDN_HI_2YR" as Two_Year_Earnings
    from
        "CollegeScorecard_Institution_Subset" inst 
        left join "CollegeScorecard_Programs_DTE_Subset" prog
            on inst."UNITID" = prog."UNITID"
    order by inst."INSTNM" asc
    """
    st_4_df = pd.read_sql_query(st_4_query,conn)
    st_4_df.index += 1


    # Stride logo
    # formatting code taken from https://stackoverflow.com/questions/70932538/how-to-center-the-title-and-an-image-in-streamlit
    # image found on google images
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(' ')
    with col2:
        st.image("stride.png")
    with col3:
        st.write(' ')

    # Title
    st.title("Stride Funding - Data Engineering")

    ## Tables

    # Filterable master table
    # Shamelessly adopted from https://towardsdatascience.com/make-dataframes-interactive-in-streamlit-c3d0c4f84ccb
    st.write("## Complete list of Institutions and Programs (Filterable)")
    gb = GridOptionsBuilder.from_dataframe(st_4_df)
    gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    gb.configure_side_bar() #Add a sidebar
    gb.configure_selection('multiple', use_checkbox=False, groupSelectsChildren="Group checkbox select children") #can probably be removed
    gridOptions = gb.build()

    grid_response = AgGrid(
        st_4_df,
        gridOptions=gridOptions,
        data_return_mode='AS_INPUT', 
        update_mode='MODEL_CHANGED', 
        fit_columns_on_grid_load=False,
        theme='streamlit', #Add theme color to the table
        enable_enterprise_modules=True,
        height=800, 
        width='100%', #haven't figured out if this does anything
        reload_data=True
    )

    st.write("## Top 50 Programs by DTE Ratio")
    st.table(st_1_df)

    st.write("## Top 100 Computer Science Program Institutions by DTE Ratio")
    st.table(st_2_df)

    st.write("## Cities with the highest number of Top 500 programs by DTE ratio")
    st.table(st_3_df)



if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import numpy as np
import requests, json
import urllib.parse
import configparser
import datetime, os
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import altair as alt
import time
import sqlite3 as sql
from datetime import datetime

# -----------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------

def convert_to_datetime(date_string):
    datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    return datetime_obj


def read_funds_sql():
    conn = sql.connect(db_name)
    df = pd.read_sql('SELECT * FROM funds', con=conn, dtype={'units held': np.float64, 'unit price': np.float64})
    conn.close()
    return df


def read_summary_sql():
    conn = sql.connect(db_name)
    #df = pd.read_sql('select strftime("%Y-%m-%d", timestamp), value from summary group by strftime("%Y-%m-%d", timestamp), value', con=conn, dtype={'value': np.float64})
    df = pd.read_sql('select timestamp, value from summary', con=conn, dtype={'value': np.float64})
    conn.close()
    return df


def add_value_column(df):
    df['Value'] = df['units held'] * (df['unit price']/100)
    df['FloatValue'] = df['units held'] * (df['unit price']/100)
    return df

def add_change_columns(df):
    df['30d_change'] = "n/a"
    df['90d_change'] = "n/a"
    df['360d_change'] = "n/a"
    with st.spinner("Getting 30 day percentage change in unit prices"):
        for index, row in df.iterrows():
            isin = row['ISIN']
            change = get_percentage_change_from_api(isin, 30, "day")
            if change is not None:
                funds_df['30d_change'][index] = str(change) + "%"
    with st.spinner("Getting 90 day percentage change in unit prices"):
        for index, row in df.iterrows():
            isin = row['ISIN']
            change = get_percentage_change_from_api(isin, 90, "week")
            if change is not None:
                funds_df['90d_change'][index] = str(change) + "%"
    with st.spinner("Getting 1yr day percentage change in unit prices"):
        for index, row in df.iterrows():
            isin = row['ISIN']
            change = get_percentage_change_from_api(isin, 360, "week")
            if change is not None:
                funds_df['360d_change'][index] = str(change) + "%"
    return df


@st.cache_data(ttl=43200) # cache for 12 hours
def get_live_price(api_key, isin):
    url = quote_base + isin
    headers = {'X-FT-Source': api_key}
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        price = response.json()['data']['items'][0]["quote"]["lastPrice"]
        return price
    else:
        manual_price = get_manual_price(isin)
        return manual_price
    
    
def get_manual_price(isin):
    price = 0.00
    return price
    
    
def check_api_key(api_key):
    url = quote_base + "GB00B4W9CK61"
    headers = {'X-FT-Source': api_key}
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        st.error("API key is not valid")
        st.stop()


def draw_main_table(funds_df):
    funds_df['Value'] = funds_df['Value'].apply(lambda x: f'£{x:.2f}') 
    gb = GridOptionsBuilder.from_dataframe(funds_df)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_column("ISIN", hide=True)
    gb.configure_column("FloatValue", hide=True)
    gb.configure_column("Employer", hide=True)
    gb.configure_column("Purchased", hide=True)
    gb.configure_column("90d_change", width=80)
    gb.configure_column("360d_change", width=80)
    gb.configure_column("Provider", width=80)
    gridOptions = gb.build()
    main_table = AgGrid(
        funds_df,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)
    return main_table


@st.cache_data(ttl=43200) # Cache for 12 hours
def get_percentage_change_from_api(isin, num_days, interval_type):
    url = historical_base + isin + "&intervalType="+str(interval_type)+"&dayCount=" + str(num_days)
    headers = {'X-FT-Source': api_key}
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        data = response.json()['data']['items'][0]["historicalSeries"]["historicalQuoteData"]
        history_from_api_df = pd.DataFrame(data)
        history_from_api_df = history_from_api_df[['date', 'close']]
        change = get_percentage_change_over_period(history_from_api_df,"close")
        formatted_change = "%.2f" % change
        return formatted_change
        

def display_historic_prices_from_api(isin, num_days, interval_type):
    url = historical_base + isin + "&intervalType="+str(interval_type)+"&dayCount=" + str(num_days)
    headers = {'X-FT-Source': api_key}
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        data = response.json()['data']['items'][0]["historicalSeries"]["historicalQuoteData"]
        history_from_api_df = pd.DataFrame(data)
        history_from_api_df = history_from_api_df[['date', 'close']]
        col1, col2 = st. columns([1, 2])
        with col1:
            st.dataframe(history_from_api_df.style.highlight_max(axis=0), use_container_width=False, hide_index=True)
        with col2:
            with st.container(border=True):
                change = get_percentage_change_over_period(history_from_api_df,"close")
                formatted_change = "%.2f" % change                
                st.info("Percentage change over the last " + str(num_days) + " days:  " + str(formatted_change) + "%")
            c = alt.Chart(history_from_api_df).mark_line().encode(x = 'date', y = alt.Y('close', scale=alt.Scale(zero=False))).interactive()
            st.altair_chart(c, use_container_width=True)
            

def display_historic_value_from_db(isin):
    conn = sql.connect(db_name)
    history_from_db_df = pd.read_sql('SELECT timestamp,value FROM fund_growth where isin = "'+ isin +'";',con=conn, dtype={'value': np.float64})
    conn.close()
    col1, col2 = st. columns([1, 2])
    with col1:
        st.dataframe(history_from_db_df.style.highlight_max(axis=0), use_container_width=True, hide_index=True)
    with col2:
        with st.container(border=True):
            change = get_percentage_change_over_period(history_from_db_df,"value")
            formatted_change = "%.2f" % change                
            st.info("Percentage change " + str(formatted_change) + "%")
        c = alt.Chart(history_from_db_df).mark_line().encode(x = 'timestamp', y = alt.Y('value', scale=alt.Scale(zero=False))).interactive()
        st.altair_chart(c, use_container_width=True)


def get_percentage_change_over_period(df,col):
    first = df[col].iloc[-1]
    last = df[col].iloc[0]
    return (last-first)/first*100


def get_selected_rows(ag_table):
    selected_rows = ag_table['selected_rows']
    return selected_rows


def process_selected_rows(selected_rows):
    # If more than one row is selected, display the total value of the selections
    if len(selected_rows) > 1:
        selected_df = pd.json_normalize(selected_rows)
        st.write(selected_df)
        sel = selected_df.iloc[:,8]
        sum = sel.sum()
        formted_total_value = "%.2f" % sum
        st.info("Total value of selections: £" + str(formted_total_value))
    elif len(selected_rows) == 1: # If only one row is selected, display the history
        if st.button("Get unit price history for selected fund"):
            display_historic_prices_from_api(selected_rows[0]["ISIN"], 30, "day")
            display_historic_prices_from_api(selected_rows[0]["ISIN"], 365, "week")
            display_historic_prices_from_api(selected_rows[0]["ISIN"], 730, "week")    
        if st.button("Get value history for selected fund"):
            display_historic_value_from_db(selected_rows[0]["ISIN"])
            
            
def manual_entry(): 
    with st.form(key = "Contact Form",clear_on_submit=True):
        fullName = st.text_input(label = 'Full Name',placeholder="Please enter your full name")
        email = st.text_input(label = 'Email Address',placeholder="Please enter your email address")
        submit_res = st.form_submit_button(label = "Submit")
        cancel_res = st.form_submit_button(label = "Cancel")
        if submit_res == True:
            new_data = {"fullName" : fullName,"email" : email}
            df = df.append(new_data,ignore_index=True)
            df.to_csv("manual_funds.csv",index=False)
        elif cancel_res == True:
            toggle_state_for_manual_entry()
            
            
def toggle_state_for_manual_entry():
    if st.session_state.manual_entry_in_progress:
        st.session_state.manual_entry_in_progress = False
    else:
        st.session_state.manual_entry_in_progress = True
        
        
def setup_pages():
    st.set_page_config(layout="wide")
    st.title('Pensions Dashboard')
    #st.sidebar.success("Welcome to the pensions dashboard. Here you can view and analyse your pension funds.")
    
    
def setup_config():
    conf = configparser.ConfigParser()
    conf.read('config.ini')
    quote_base = conf['main']['quote_base']
    historical_base = conf['main']['historical_base']
    api_key = conf['main']['api_key']
    database_name = conf['main']['database_name']
    return quote_base, historical_base, api_key, database_name


def setup_session_state():
    if 'manual_entry_in_progress' not in st.session_state:
        st.session_state.manual_entry_in_progress = False  
         
        
def add_live_prices_to_dataframe(funds_df):
    with st.spinner(text="Fetching live prices..."):
        for index in funds_df.index:
            isin = funds_df['ISIN'][index]
            if "manual" not in isin: # Only overwitre the price of the ISIN field does not contain the string "manual"
                price = get_live_price(api_key, isin) # Get live price
                funds_df['unit price'][index] = (price*100) # Update live price in main dataframe
                
                
def pension_summary(funds_df, summary_df):
    total_value = funds_df['Value'].sum()
    formted_total_value = "%.2f" % total_value
    insert_summary_value(total_value)
    summary_df = read_summary_sql()
    with st.expander("Total value of pensions: £" + str(formted_total_value)):
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    
def insert_summary_value(value):
    timestamp = datetime.now().strftime("%Y-%m-%d") 
    conn = sql.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT or IGNORE INTO summary VALUES (?,?)", (timestamp, value))
    conn.commit()
    conn.close()
    
    
def write_funds_values_to_db(funds_df):
    conn = sql.connect(db_name)
    cursor = conn.cursor()
    for index, row in funds_df.iterrows():
        fund_name = row['fund name']
        fund_value = row['Value']
        isin = row['ISIN']
        provider = row['Provider']
        #timestamp = datetime.now().strftime("%Y-%m-%d %I:%M")
        timestamp = datetime.now().strftime("%Y-%m-%d") 
        cursor.execute("INSERT or IGNORE INTO fund_growth (timestamp, fund, isin, value, provider) values (?,?,?,?,?)", (timestamp, fund_name, isin, fund_value, provider))
    conn.commit()
    conn.close()
          
  
# -----------------------------------------------------------------------
# Maim program
# -----------------------------------------------------------------------
setup_pages()                                       # Set up page layout etc
quote_base,historical_base,api_key,db_name \
                                   = setup_config() # Set up configuration
check_api_key(api_key)                              # Check the API key is valid
funds_df = read_funds_sql()                         # Create the main funds dataframe
summary_df = read_summary_sql()                     # Create the summary dataframe
setup_session_state()                               # Initialise session state
add_live_prices_to_dataframe(funds_df)              # Add live prices to the main dataframe
funds_df = add_value_column(funds_df)               # Add the Values column to the main dataframe
funds_df = add_change_columns(funds_df)             # Add the percentage cange columns to the main dataframe
write_funds_values_to_db(funds_df)                  # Write to fund_values
pension_summary(funds_df, summary_df)               # Display the pension summary at the top of the page
main_table = draw_main_table(funds_df)              # Draw the main table
selected_rows = get_selected_rows(main_table)       # Get the selected rows from the main table
process_selected_rows(selected_rows)                # Process the selected rows of the main table














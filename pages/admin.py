
import streamlit as st
import pandas as pd
import sqlite3 as sql
import numpy as np

#-------------------------------------------------------
# Functions
#-------------------------------------------------------      
def add_fund_to_db(fund_name, units_held, init_price, provider, employer, isin):
    conn = sql.connect('finance-management.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO funds ("fund name", "units held", "unit price", provider, employer, isin)
        VALUES (?, ?, ?, ?, ?, ?);
    ''', (fund_name, units_held, init_price, provider, employer, isin))
    conn.commit()
    conn.close()
    st.write("Data inserted")
    
    
def read_funds_sql():
    conn = sql.connect('finance-management.db')
    df = pd.read_sql('SELECT * FROM funds', con=conn, dtype={'units held': np.float64, 'unit price': np.float64})
    return df

def search_for_fund_in_db(fund_name, isin):
    conn = sql.connect('finance-management.db')
    c = conn.cursor()
    c.execute('''
        SELECT * FROM funds WHERE "fund name" = ? OR isin = ?;
    ''', (fund_name, isin))
    data = c.fetchall()
    conn.close()
    return data

def display_results(results_df):
    results_df['foo'] = st.checkbox('Select all', key='select_all')
    st.write(results_df)
        
        
#-------------------------------------------------------
# Main program
#-------------------------------------------------------

global results_df

st.title("Admin page")
st.header("Add funds")
with st.form(key="add_fund_form",clear_on_submit=False):
    st.write("Enter Fund details below:")
    fund_name_input = st.text_input('fund_name', key='fund_name')
    units_held_input = st.text_input('units_held', key='units_held')
    unit_price_input = st.text_input('units_price', key='units_price')
    provider_input = st.text_input('provider', key='provider')
    employer_input = st.text_input('employer', key='employer')
    isin_input = st.text_input('isin', key='isin')
    submitted = st.form_submit_button("Submit")
    if submitted:
        add_fund_to_db(
            fund_name_input,
            units_held_input,
            unit_price_input,
            provider_input,
            employer_input,
            isin_input
        )
        
        
        
        



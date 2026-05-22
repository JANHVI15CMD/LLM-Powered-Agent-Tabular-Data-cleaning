import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def plot_nulls(df):
    nulls = df.isnull().sum()
    if nulls.sum() > 0:
        fig, ax = plt.subplots()
        nulls.plot(kind='bar', ax=ax)
        ax.set_title('Null Counts per Column')
        st.pyplot(fig)
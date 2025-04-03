import streamlit as st
import sys
from streamlit.web import cli as stcli
from streamlit import runtime
import plotly.express as px  # pip install plotly-express
from openpyxl import load_workbook
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import utils

def main():

    date = st.title("Ejemplos")
    menu = ["Home", "Update", "Excel", "About"]

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")

    elif choice == "Update":
        st.subheader("Update Excel's records")
        file_name = st.file_uploader("Upload Excel")

        date = st.date_input("Enter the date")
        category = st.selectbox("Select the category", ("Cafe", "Food", "Ropa", "Otros"))
        amount = st.number_input("Enter the amount", min_value=10, max_value=1000)
        sheet = st.selectbox("Select Sheet", ("Sheet1", "Sheet2"))
        new_data = {
            "date": date,
            "amount": amount,
            "category": category,
        }
        btn = st.button("Save Data")
        if btn:
            pass

    elif choice == "Excel":
        st.subheader("Teacher Reports")
        file_name = st.file_uploader("Upload Excel")
        if file_name:
            xl_file = pd.ExcelFile(file_name)
            df = pd.read_excel(file_name, engine="openpyxl")
            data = utils.process_columns(df)

            data_q2 = utils.analyze_data_q2(data)
            
            # Get unique docentes for filtering
            docentes = sorted(list(set([idx[0] for idx in data_q2.index])))
            
            # Add filter in sidebar
            selected_docente = st.sidebar.selectbox(
                "Select Teacher (Docente)", 
                ["All"] + docentes
            )
            
            # Display overview data
            with st.expander("View Raw Data"):
                st.dataframe(data_q2)
            
            # Filter data based on selection
            if selected_docente != "All":
                filtered_data = data_q2[data_q2.index.get_level_values(0) == selected_docente]
                docentes_to_show = [selected_docente]
            else:
                filtered_data = data_q2
                docentes_to_show = docentes
            
            # Create reports for each docente
            for docente in docentes_to_show:
                st.markdown(f"## 👨‍🏫 Teacher: {docente}")
                
                # Get data for this docente
                docente_data = data_q2[data_q2.index.get_level_values(0) == docente]
                
                # For each subject taught by this docente
                for (_, asignatura), row in docente_data.iterrows():
                    st.markdown(f"### 📚 Subject: {asignatura}")
                    
                    # Create visualization
                    ratings = row.unstack()
                    
                    # Plot the data
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ratings.plot(kind='bar', ax=ax)
                    plt.title(f'Rating Summary for {docente} - {asignatura}')
                    plt.xlabel('Rating Categories')
                    plt.ylabel('Count')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    # Display in Streamlit
                    st.pyplot(fig)
                    plt.close(fig)  # Close the figure to free memory
                    
                    st.markdown("---")  # Add a separator between subjects


if __name__ == "__main__":
    if runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())

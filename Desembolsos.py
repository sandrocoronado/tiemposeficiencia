import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt


LOGGER = get_logger(__name__)

def process_dataframe(xls_path):
    # Cargar el archivo Excel
    xls = pd.ExcelFile(xls_path)
    desembolsos = xls.parse('Desembolsos')
    operaciones = xls.parse('Operaciones')

    # Unir dataframes y calcular la columna 'Ano'
    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia']], on='IDEtapa', how='left')
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days/365).round().astype(int)
    merged_df['Meses'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 30).round().astype(int)

    # Calcular montos agrupados y montos acumulados incluyendo IDDesembolso
    result_df = merged_df.groupby(['IDEtapa', 'Ano', 'Meses', 'IDDesembolso'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby('IDEtapa')['Monto'].cumsum().reset_index(drop=True)
    result_df['Porcentaje del Monto'] = result_df.groupby('IDEtapa')['Monto'].apply(lambda x: x / x.sum() * 100).reset_index(drop=True)
    result_df['Porcentaje del Monto Acumulado'] = result_df.groupby('IDEtapa')['Monto Acumulado'].apply(lambda x: x / x.max() * 100).reset_index(drop=True)

    # Asignar países
    country_map = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brasil', 'PY': 'Paraguay', 'UR': 'Uruguay'}
    result_df['Pais'] = result_df['IDEtapa'].str[:2].map(country_map).fillna('Desconocido')
    
    return result_df


def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
    )

    st.write("# Curva de Desembolsos por País 👋")

    # Load the Excel file using Streamlit
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    
    if uploaded_file:
        result_df = process_dataframe(uploaded_file)
        
        # Create a dropdown selectbox to select the country
        selected_country = st.selectbox('Choose a country:', result_df['Pais'].unique())

        # Filter the dataframe based on the selected country
        filtered_df = result_df[result_df['Pais'] == selected_country]

        # Group and calculate cumulative sum for Monto by Ano, IDEtapa, and Pais
        df_acumulativo = filtered_df.groupby(['Ano', 'IDEtapa', 'Pais'])['Monto'].sum().groupby(level=[1,2]).cumsum().reset_index()

        st.write(f"Datos acumulativos por año para {selected_country}")
        st.write(df_acumulativo)

        # Create Altair chart for Monto Acumulado over Ano by IDEtapa and Pais
        chart = alt.Chart(df_acumulativo).mark_line(point=True).encode(
            x=alt.X('Ano:O', title='Año'),
            y=alt.Y('Monto:Q', title='Monto Acumulado'),
            color='IDEtapa:N',
            tooltip=['Ano', 'IDEtapa', 'Monto']
        ).properties(
            title=f'Monto Acumulado a través de los años para {selected_country}',
            width=600,
            height=400
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

    st.sidebar.success("Select a demo above.")

    st.markdown(
        """

    """
    )

if __name__ == "__main__":
    run()






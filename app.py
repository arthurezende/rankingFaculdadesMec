import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

# Aumenta o tempo limite para carregamento de componentes
st.set_page_config(layout="wide", page_title="Análise de Dados do MEC", initial_sidebar_state="expanded")

# Cabeçalho
st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h2>Faculdade Exame - Projeto Extensionista: Análise Educacional e Apoio à Escolha de Cursos com Base nos Dados do INEP</h2>
    </div>
    """,
    unsafe_allow_html=True
)

@st.cache_data(ttl=4600)
def load_data():
    df = pd.read_csv('dados_reduzidos_100_mil_linhas.csv', encoding='utf-8', low_memory=False)
    for col in ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    return df

# Carrega os dados
with st.spinner('Carregando dados...'):
    df_merged = load_data()

# Filtros da barra lateral
st.sidebar.title("Filtros")
uf_filter = st.sidebar.multiselect('UF IES', df_merged['SG_UF_IES'].unique())
municipio_filter = st.sidebar.multiselect('Município do Curso', df_merged['NO_MUNICIPIO'].unique())
curso_filter = st.sidebar.multiselect('Nome do Curso', df_merged['NO_CURSO'].unique())
org_academica_filter = st.sidebar.multiselect('Organização Acadêmica', df_merged['NO_IES'].unique())
rede_filter = st.sidebar.multiselect('Tipo de Rede', ['Pública', 'Privada'])
situacao_filter = st.sidebar.selectbox('Situação do Curso', ['Todos'] + list(df_merged['Situação'].unique()))

def apply_filters(df):
    if uf_filter:
        df = df[df['SG_UF_IES'].isin(uf_filter)]
    if municipio_filter:
        df = df[df['NO_MUNICIPIO'].isin(municipio_filter)]
    if curso_filter:
        df = df[df['NO_CURSO'].isin(curso_filter)]
    if org_academica_filter:
        df = df[df['NO_IES'].isin(org_academica_filter)]
    if rede_filter:
        df = df[df['TP_REDE'].isin(rede_filter)]
    if situacao_filter != 'Todos':
        df = df[df['Situação'] == situacao_filter]
    return df

filtered_df = apply_filters(df_merged)

def create_aggrid(df, columns, key, column_config=None):
    gb = GridOptionsBuilder.from_dataframe(df[columns])
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection('single', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
    gb.configure_default_column(sorteable=True, filterable=True, resizable=True, width=100)
    
    if column_config:
        for col, config in column_config.items():
            gb.configure_column(col, **config)
    
    gridOptions = gb.build()
    
    return AgGrid(
        df[columns],
        gridOptions=gridOptions,
        data_return_mode='AS_INPUT', 
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=False,
        theme='streamlit',
        enable_enterprise_modules=True,
        height=400,
        width='100%',
        reload_data=False,
        key=key
    )

# Visualização 1: Ranking IES
st.header("Visualização 1: Ranking IES")
ies_columns = ['NO_IES', 'SG_UF_IES', 'NO_MUNICIPIO_IES', 'TP_REDE', 'CI', 'CI-EaD', 'IGC', 'Ano CI', 'Ano CI-EaD', 'Ano IGC']
ies_df = filtered_df.drop_duplicates(subset=['CO_IES'])[ies_columns]

ies_column_config = {
    'NO_IES': {'headerName': 'Nome da Instituição', 'width': 225},
    'SG_UF_IES': {'headerName': 'UF IES'},
    'NO_MUNICIPIO_IES': {'headerName': 'Município IES'},
    'TP_REDE': {'headerName': 'Rede'}
}

create_aggrid(ies_df, ies_columns, 'ies_table', ies_column_config)

# Visualização 2: Ranking Cursos
st.header("Visualização 2: Ranking Cursos")
cursos_columns = ['NO_CURSO', 'NO_IES', 'NO_MUNICIPIO', 'CC', 'Ano CC', 'CPC', 'ENADE', 'Ano ENADE', 'IDD', 'Situação']
cursos_df = filtered_df[cursos_columns]

cursos_column_config = {
    'NO_CURSO': {'headerName': 'Nome do Curso', 'width': 300},
    'NO_IES': {'headerName': 'Nome da Instituição', 'width': 225},
    'NO_MUNICIPIO': {'headerName': 'Município Curso'}
}

create_aggrid(cursos_df, cursos_columns, 'cursos_table', cursos_column_config)

st.write(f"Total de registros: {len(filtered_df)}")

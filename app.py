# app.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide", page_title="Análise de Dados do MEC", initial_sidebar_state="expanded")

@st.cache_data(ttl=3600)
def carregar_e_processar_dados(arquivo_csv='dados_reduzidos_50_mil_linhas-uf.csv'):
    try:
        df = pd.read_csv(arquivo_csv, encoding='utf-8', low_memory=False)
    except FileNotFoundError:
        st.error(f"ERRO: Arquivo de dados '{arquivo_csv}' não encontrado no repositório.")
        st.stop()

    cols_numericas = ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD']
    for col in cols_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    df['TP_MODALIDADE_ENSINO'] = df['TP_MODALIDADE_ENSINO'].map({1: 'Presencial', 2: 'EAD'})
    df['TP_GRAU_ACADEMICO'] = df['TP_GRAU_ACADEMICO'].astype(float).map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})

    return df

with st.spinner("Carregando e processando dados..."):
    df_completo = carregar_e_processar_dados()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.title("Filtros")

# Filtros para IES
st.sidebar.header("Filtros de Instituição (IES)")
filtro_ue_ies = st.sidebar.multiselect('UF da IES', sorted(df_completo['SG_UF_IES'].dropna().unique()), key='filtro_uf_ies')
filtro_org_academia = st.sidebar.multiselect('Instituição de Ensino', sorted(df_completo['NO_IES'].dropna().unique()), key='filtro_ies')
filtro_rede = st.sidebar.multiselect('Tipo de Rede', sorted(df_completo['TP_REDE'].dropna().unique()), key='filtro_rede')

# Filtros para Cursos
st.sidebar.header("Filtros de Curso")
filtro_municipio_curso = st.sidebar.multiselect('Município do Curso', sorted(df_completo['NO_MUNICIPIO'].dropna().unique()), key='filtro_municipio_curso')
filtro_cursos = st.sidebar.multiselect('Nome do Curso', sorted(df_completo['NO_CURSO'].dropna().unique()), key='filtro_curso_especifico')
filtro_modalidade = st.sidebar.multiselect('Modalidade de Ensino', sorted(df_completo['TP_MODALIDADE_ENSINO'].dropna().unique()), key='main_filtro_modalidade')

# --- LÓGICA DE FILTRAGEM COM PANDAS ---
df_filtrada_ies = df_completo.drop_duplicates(subset=['CO_IES'])
if filtro_ue_ies:
    df_filtrada_ies = df_filtrada_ies[df_filtrada_ies['SG_UF_IES'].isin(filtro_ue_ies)]
if filtro_org_academia:
    df_filtrada_ies = df_filtrada_ies[df_filtrada_ies['NO_IES'].isin(filtro_org_academia)]
if filtro_rede:
    df_filtrada_ies = df_filtrada_ies[df_filtrada_ies['TP_REDE'].isin(filtro_rede)]

codigos_ies_filtradas = df_filtrada_ies['CO_IES'].unique()
df_filtrada_cursos = df_completo[df_completo['CO_IES'].isin(codigos_ies_filtradas)]

if filtro_municipio_curso:
    df_filtrada_cursos = df_filtrada_cursos[df_filtrada_cursos['NO_MUNICIPIO'].isin(filtro_municipio_curso)]
if filtro_cursos:
    df_filtrada_cursos = df_filtrada_cursos[df_filtrada_cursos['NO_CURSO'].isin(filtro_cursos)]
if filtro_modalidade:
    df_filtrada_cursos = df_filtrada_cursos[df_filtrada_cursos['TP_MODALIDADE_ENSINO'].isin(filtro_modalidade)]

# Salva o dataframe filtrado para a página de análise
st.session_state.df_filtrada_cursos = df_filtrada_cursos

# --- LAYOUT PRINCIPAL ---
st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Faculdade Exame - Projeto Extensionista: Análise Educacional e Apoio à Escolha de Cursos</h3>
    </div>
    """,
    unsafe_allow_html=True
)
st.title("🔎 Explorador de Cursos e Instituições")

st.header("Ranking das Instituições de Ensino Superior (IES)")
ies_colunas = ['NO_IES', 'SG_UF_IES', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']
gb_ies = GridOptionsBuilder.from_dataframe(df_filtrada_ies[ies_colunas])
gb_ies.configure_pagination(paginationAutoPageSize=True)
AgGrid(df_filtrada_ies, gridOptions=gb_ies.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_ies', height=400)

st.header("Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'TP_MODALIDADE_ENSINO', 'NO_MUNICIPIO', 'TP_GRAU_ACADEMICO', 'CC', 'CPC', 'ENADE', 'Situação']
gb_cursos = GridOptionsBuilder.from_dataframe(df_filtrada_cursos[cursos_colunas])
gb_cursos.configure_pagination(paginationAutoPageSize=True)
AgGrid(df_filtrada_cursos, gridOptions=gb_cursos.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_cursos', height=400)

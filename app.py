# app.py

import streamlit as st
import pandas as pd
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide", page_title="Análise de Dados do MEC", initial_sidebar_state="expanded")

@st.cache_resource
def get_db_connection():
    return duckdb.connect(database=':memory:', read_only=False)

@st.cache_data
def carrega_dados_iniciais(_conn, arquivo_csv='dados_reduzidos_50_mil_linhas-uf.csv'): # <-- NOME DO ARQUIVO ATUALIZADO AQUI
    try:
        query = f"CREATE OR REPLACE TABLE mec_data AS SELECT * FROM read_csv_auto('{arquivo_csv}', ALL_VARCHAR=TRUE)"
        _conn.execute(query)
        df_inicial = _conn.execute("SELECT * FROM mec_data").fetchdf()
    except Exception as e:
        st.error(f"ERRO CRÍTICO ao carregar dados: {e}")
        st.stop()

    cols_numericas = ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD', 'QT_VG_TOTAL', 'QT_INSCRITO_TOTAL', 'CO_IES']
    for col in cols_numericas:
        if col in df_inicial.columns:
            df_inicial[col] = pd.to_numeric(df_inicial[col], errors='coerce')
    
    df_inicial['TP_REDE'] = pd.to_numeric(df_inicial['TP_REDE'], errors='coerce').map({1.0: 'Pública', 2.0: 'Privada'})
    df_inicial['TP_MODALIDADE_ENSINO'] = pd.to_numeric(df_inicial['TP_MODALIDADE_ENSINO'], errors='coerce').map({1.0: 'Presencial', 2.0: 'EAD'})
    df_inicial['TP_GRAU_ACADEMICO'] = pd.to_numeric(df_inicial['TP_GRAU_ACADEMICO'], errors='coerce').map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})

    ies_unicas_df = df_inicial.drop_duplicates(subset=['CO_IES'])[['CO_IES', 'NO_IES', 'SG_UF_IES', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']].copy()
    _conn.register('ies_unicas', ies_unicas_df)
    
    return df_inicial

with st.spinner("Carregando dados..."):
    conn = get_db_connection()
    df_inicial = carrega_dados_iniciais(conn)

st.sidebar.title("Filtros")
st.sidebar.header("Filtros de Instituição (IES)")
filtro_ue_ies = st.sidebar.multiselect('UF da IES', sorted(df_inicial['SG_UF_IES'].dropna().unique()), key='filtro_uf_ies')
filtro_org_academia = st.sidebar.multiselect('Instituição de Ensino', sorted(df_inicial['NO_IES'].dropna().unique()), key='filtro_ies')
filtro_rede = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial['TP_REDE'].dropna().unique()), key='filtro_rede')

st.sidebar.header("Filtros de Curso")
filtro_municipio_curso = st.sidebar.multiselect('Município do Curso', sorted(df_inicial['NO_MUNICIPIO'].dropna().unique()), key='filtro_municipio_curso')
filtro_cursos = st.sidebar.multiselect('Nome do Curso', sorted(df_inicial['NO_CURSO'].dropna().unique()), key='filtro_curso_especifico')
filtro_modalidade = st.sidebar.multiselect('Modalidade de Ensino', sorted(df_inicial['TP_MODALIDADE_ENSINO'].dropna().unique()), key='main_filtro_modalidade')

# Lógica de Filtragem
query_ies = "SELECT * FROM ies_unicas"
params_ies = []
clauses_ies = []
if filtro_ue_ies:
    clauses_ies.append(f"SG_UF_IES IN ({','.join(['?']*len(filtro_ue_ies))})")
    params_ies.extend(filtro_ue_ies)
if filtro_org_academia:
    clauses_ies.append(f"NO_IES IN ({','.join(['?']*len(filtro_org_academia))})")
    params_ies.extend(filtro_org_academia)
if filtro_rede:
    rede_map_inv = {v: k for k, v in {1: 'Pública', 2: 'Privada'}.items()}
    clauses_ies.append(f"CAST(TP_REDE AS INTEGER) IN ({','.join(['?']*len(filtro_rede))})")
    params_ies.extend([rede_map_inv[r] for r in filtro_rede])
if clauses_ies:
    query_ies += " WHERE " + " AND ".join(clauses_ies)
ies_df_filtrado = conn.execute(query_ies, params_ies).fetchdf()
ies_df_filtrado['TP_REDE'] = pd.to_numeric(ies_df_filtrado['TP_REDE'], errors='coerce').map({1.0: 'Pública', 2.0: 'Privada'})


codigos_ies_filtradas = ies_df_filtrado['CO_IES'].unique().tolist()
df_cursos_pre_filtrado = df_inicial[df_inicial['CO_IES'].isin(codigos_ies_filtradas)] if filtro_ue_ies or filtro_org_academia or filtro_rede else df_inicial

cursos_df_filtrado = df_cursos_pre_filtrado.copy()
if filtro_municipio_curso:
    cursos_df_filtrado = cursos_df_filtrado[cursos_df_filtrado['NO_MUNICIPIO'].isin(filtro_municipio_curso)]
if filtro_cursos:
    cursos_df_filtrado = cursos_df_filtrado[cursos_df_filtrado['NO_CURSO'].isin(filtro_cursos)]
if filtro_modalidade:
    cursos_df_filtrado = cursos_df_filtrado[cursos_df_filtrado['TP_MODALIDADE_ENSINO'].isin(filtro_modalidade)]

st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Faculdade Exame - Projeto Extensionista: Análise Educacional e Apoio à Escolha de Cursos</h3>
    </div>
    """,
    unsafe_allow_html=True
)
st.title("🔎 Explorador de Cursos e Instituições")
st.markdown("Use os filtros na barra lateral para pesquisar. Para análises visuais, navegue para a página 'Análise Avançada'.")

st.header("Ranking das Instituições de Ensino Superior (IES)")
ies_colunas = ['NO_IES', 'SG_UF_IES', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']
gb_ies = GridOptionsBuilder.from_dataframe(ies_df_filtrado[ies_colunas])
gb_ies.configure_pagination(paginationAutoPageSize=True)
AgGrid(ies_df_filtrado, gridOptions=gb_ies.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_ies', height=400)

st.header("Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'TP_MODALIDADE_ENSINO', 'NO_MUNICIPIO', 'TP_GRAU_ACADEMICO', 'CC', 'CPC', 'ENADE', 'Situação']
gb_cursos = GridOptionsBuilder.from_dataframe(cursos_df_filtrado[cursos_colunas])
gb_cursos.configure_pagination(paginationAutoPageSize=True)
AgGrid(cursos_df_filtrado, gridOptions=gb_cursos.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_cursos', height=400)

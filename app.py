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
def carrega_dados_iniciais(_conn, arquivo_parquet='dados_mec.parquet', arquivo_csv='dados_reduzidos_100_mil_linhas.csv'):
    df = None
    try:
        df = pd.read_parquet(arquivo_parquet)
    except Exception:
        try:
            df = pd.read_csv(arquivo_csv, encoding='utf-8', low_memory=False)
        except FileNotFoundError:
            st.error(f"ERRO CRÍTICO: Nenhum arquivo de dados ('{arquivo_parquet}' ou '{arquivo_csv}') foi encontrado.")
            st.stop()

    cols_numericas = ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD', 'QT_VG_TOTAL', 'QT_INSCRITO_TOTAL']
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    df['TP_MODALIDADE_ENSINO'] = df['TP_MODALIDADE_ENSINO'].map({1: 'Presencial', 2: 'EAD'})
    df['TP_GRAU_ACADEMICO'] = df['TP_GRAU_ACADEMICO'].astype(float).map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})

    # Criar uma tabela de IES únicas no DuckDB
    ies_unicas_df = df.drop_duplicates(subset=['CO_IES'])[['CO_IES', 'NO_IES', 'SG_UF_IES', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']].copy()
    _conn.register('ies_unicas', ies_unicas_df)
    
    _conn.register('cursos_completos', df)
    return df

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

# --- LÓGICA DE FILTRAGEM CORRIGIDA ---

def apply_filters(table_name, filters):
    base_query = f"SELECT * FROM {table_name}"
    clauses = []
    params = []
    
    for field, values in filters.items():
        if values:
            clauses.append(f"{field} IN ({','.join(['?'] * len(values))})")
            params.extend(values)
            
    if clauses:
        query = f"{base_query} WHERE {' AND '.join(clauses)}"
    else:
        query = base_query
    
    return conn.execute(query, params).fetchdf()

# 1. Filtra a tabela de IES usando APENAS seus filtros
ies_filters = {'SG_UF_IES': filtro_ue_ies, 'NO_IES': filtro_org_academia, 'TP_REDE': filtro_rede}
ies_df_filtrado = apply_filters('ies_unicas', {k: v for k, v in ies_filters.items() if v})

# 2. Filtra a tabela de CURSOS usando TODOS os filtros aplicáveis
codigos_ies_filtradas = ies_df_filtrado['CO_IES'].unique().tolist()
curso_filters = {
    'CO_IES': codigos_ies_filtradas,
    'NO_MUNICIPIO': filtro_municipio_curso,
    'NO_CURSO': filtro_cursos,
    'TP_MODALIDADE_ENSINO': filtro_modalidade
}
cursos_df_filtrado = apply_filters('cursos_completos', {k: v for k, v in curso_filters.items() if v})

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
st.markdown("Use os filtros na barra lateral para pesquisar. Para análises visuais, navegue para a página 'Análise Avançada'.")

# --- VISUALIZAÇÃO ---
st.header("1. Ranking das Instituições de Ensino Superior (IES)")
ies_colunas = ['NO_IES', 'SG_UF_IES', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']
gb_ies = GridOptionsBuilder.from_dataframe(ies_df_filtrado[ies_colunas])
gb_ies.configure_column('NO_IES', headerName='Nome da Instituição', width=450)
gb_ies.configure_pagination(paginationAutoPageSize=True)
AgGrid(ies_df_filtrado, gridOptions=gb_ies.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_ies', height=400)

st.header("2. Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'TP_MODALIDADE_ENSINO', 'NO_MUNICIPIO', 'TP_GRAU_ACADEMICO', 'CC', 'CPC', 'ENADE', 'Situação']
gb_cursos = GridOptionsBuilder.from_dataframe(cursos_df_filtrado[cursos_colunas])
gb_cursos.configure_column('NO_CURSO', headerName='Nome do Curso', width=350)
gb_cursos.configure_column('NO_IES', headerName='Instituição', width=300)
gb_cursos.configure_pagination(paginationAutoPageSize=True)
AgGrid(cursos_df_filtrado, gridOptions=gb_cursos.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_cursos', height=400)
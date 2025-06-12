# app.py

import streamlit as st
import pandas as pd
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Análise de Dados do MEC", initial_sidebar_state="expanded")

# --- FUNÇÕES ---
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
    
    # Criar a tabela completa de cursos no DuckDB
    _conn.register('cursos_completos', df)
    
    return df

def definir_processo_seletivo(ies_df):
    df = ies_df.copy()
    df['PROCESSO_SELETIVO'] = 'Verificar com a instituição'
    cond_vest_proprio = df['NO_IES'].str.contains('UNIVERSIDADE DE SÃO PAULO|UNIVERSIDADE ESTADUAL DE CAMPINAS|UNIVERSIDADE ESTADUAL PAULISTA', case=False, na=False)
    cond_sisu = (df['TP_REDE'] == 'Pública') & (df['NO_IES'].str.contains('FEDERAL', case=False, na=False))
    cond_privada = (df['TP_REDE'] == 'Privada')
    df.loc[cond_vest_proprio, 'PROCESSO_SELETIVO'] = 'Vestibular Próprio'
    df.loc[cond_sisu, 'PROCESSO_SELETIVO'] = 'SISU / Vestibular Próprio'
    df.loc[cond_privada, 'PROCESSO_SELETIVO'] = 'Vestibular Próprio / PROUNI / FIES'
    return df

# --- CARREGAMENTO INICIAL ---
with st.spinner("Carregando dados... Por favor, aguarde."):
    conn = get_db_connection()
    df_inicial = carrega_dados_iniciais(conn)

# --- BARRA LATERAL DE FILTROS ---
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

# 1. Filtra a tabela de IES usando apenas seus próprios filtros
base_query_ies = "SELECT * FROM ies_unicas"
clauses_ies = []
params_ies = []
if filtro_ue_ies:
    clauses_ies.append(f"SG_UF_IES IN ({','.join(['?']*len(filtro_ue_ies))})")
    params_ies.extend(filtro_ue_ies)
if filtro_org_academia:
    clauses_ies.append(f"NO_IES IN ({','.join(['?']*len(filtro_org_academia))})")
    params_ies.extend(filtro_org_academia)
if filtro_rede:
    clauses_ies.append(f"TP_REDE IN ({','.join(['?']*len(filtro_rede))})")
    params_ies.extend(filtro_rede)

query_ies = f"{base_query_ies} WHERE {' AND '.join(clauses_ies)}" if clauses_ies else base_query_ies
ies_df_filtrado = conn.execute(query_ies, params_ies).fetchdf()
ies_df_filtrado = definir_processo_seletivo(ies_df_filtrado)

# 2. Filtra a tabela de Cursos usando seus próprios filtros
base_query_cursos = "SELECT * FROM cursos_completos"
clauses_cursos = []
params_cursos = []
if filtro_municipio_curso:
    clauses_cursos.append(f"NO_MUNICIPIO IN ({','.join(['?']*len(filtro_municipio_curso))})")
    params_cursos.extend(filtro_municipio_curso)
if filtro_cursos:
    clauses_cursos.append(f"NO_CURSO IN ({','.join(['?']*len(filtro_cursos))})")
    params_cursos.extend(filtro_cursos)
if filtro_modalidade:
    clauses_cursos.append(f"TP_MODALIDADE_ENSINO IN ({','.join(['?']*len(filtro_modalidade))})")
    params_cursos.extend(filtro_modalidade)
# Se houver IES filtradas, aplica esse filtro também à lista de cursos
if not ies_df_filtrado.equals(conn.execute("SELECT * FROM ies_unicas").fetchdf()):
    codigos_ies_filtradas = ies_df_filtrado['CO_IES'].unique().tolist()
    if codigos_ies_filtradas:
        clauses_cursos.append(f"CO_IES IN ({','.join(['?']*len(codigos_ies_filtradas))})")
        params_cursos.extend(codigos_ies_filtradas)

query_cursos = f"{base_query_cursos} WHERE {' AND '.join(clauses_cursos)}" if clauses_cursos else base_query_cursos
cursos_df_filtrado = conn.execute(query_cursos, params_cursos).fetchdf()

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
ies_colunas = ['NO_IES', 'SG_UF_IES', 'PROCESSO_SELETIVO', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']
gb_ies = GridOptionsBuilder.from_dataframe(ies_df_filtrado[ies_colunas])
gb_ies.configure_column('NO_IES', headerName='Nome da Instituição', width=350)
gb_ies.configure_column('SG_UF_IES', headerName='UF', width=70)
gb_ies.configure_column('PROCESSO_SELETIVO', headerName='Como Ingressar?', width=250)
gb_ies.configure_column('TP_REDE', headerName='Rede', width=100)
gb_ies.configure_column('IGC', headerName='IGC', width=80, headerTooltip='Índice Geral de Cursos (1 a 5)')
gb_ies.configure_column('CI', headerName='CI', width=80, headerTooltip='Conceito Institucional (1 a 5)')
gb_ies.configure_pagination(paginationAutoPageSize=True)
AgGrid(ies_df_filtrado, gridOptions=gb_ies.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_ies', height=400)

st.header("2. Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'TP_MODALIDADE_ENSINO', 'NO_MUNICIPIO', 'TP_GRAU_ACADEMICO', 'CC', 'CPC', 'ENADE', 'Situação']
gb_cursos = GridOptionsBuilder.from_dataframe(cursos_df_filtrado[cursos_colunas])
gb_cursos.configure_column('NO_CURSO', headerName='Nome do Curso', width=300)
gb_cursos.configure_column('NO_IES', headerName='Instituição', width=250)
gb_cursos.configure_column('TP_GRAU_ACADEMICO', headerName='Grau', width=120)
gb_cursos.configure_pagination(paginationAutoPageSize=True)
AgGrid(cursos_df_filtrado, gridOptions=gb_cursos.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_cursos', height=400)
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
        st.sidebar.info("⚡ Dados carregados via Parquet (rápido).", icon="✅")
    except Exception:
        st.sidebar.warning(f"Arquivo Parquet não encontrado. Carregando do CSV '{arquivo_csv}'.")
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
    ies_unicas_df = df.drop_duplicates(subset=['CO_IES'])[['CO_IES', 'NO_IES', 'SG_UF_IES', 'NO_MUNICIPIO_IES', 'TP_REDE', 'CI', 'CI-EaD', 'IGC', 'Ano IGC', 'Ano CI']].copy()
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
conn = get_db_connection()
if 'df_inicial' not in st.session_state:
    st.session_state.df_inicial = carrega_dados_iniciais(conn)
df_inicial = st.session_state.df_inicial

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.title("Filtros")

st.sidebar.header("1. Filtre as Instituições")
filtro_ue_ies = st.sidebar.multiselect('UF da IES', sorted(df_inicial['SG_UF_IES'].dropna().unique()), key='filtro_uf_ies')
filtro_org_academia = st.sidebar.multiselect('Instituição de Ensino', sorted(df_inicial['NO_IES'].dropna().unique()), key='filtro_ies')
filtro_rede = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial['TP_REDE'].dropna().unique()), key='filtro_rede')
filtro_igc_min = st.sidebar.slider('Nota Mínima IGC (Instituição)', 1, 5, 1, key='filtro_igc')

st.sidebar.header("2. Filtre os Cursos")
filtro_municipio_curso = st.sidebar.multiselect('Município do Curso', sorted(df_inicial['NO_MUNICIPIO'].dropna().unique()), key='filtro_municipio_curso')
filtro_area_conhecimento = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial['NO_CINE_AREA_ESPECIFICA'].dropna().unique()), key='filtro_area')
filtro_grau_academico = st.sidebar.multiselect('Grau Acadêmico', sorted(df_inicial['TP_GRAU_ACADEMICO'].dropna().unique()), key='filtro_grau')
filtro_cursos = st.sidebar.multiselect('Nome do Curso (Específico)', sorted(df_inicial['NO_CURSO'].dropna().unique()), key='filtro_curso_especifico')
filtro_modalidade = st.sidebar.multiselect('Modalidade de Ensino', sorted(df_inicial['TP_MODALIDADE_ENSINO'].dropna().unique()), key='filtro_modalidade')
filtro_cpc_min = st.sidebar.slider('Nota Mínima CPC (Curso)', 1, 5, 1, key='filtro_cpc')

# --- ARMAZENAR FILTROS NO SESSION STATE PARA OUTRAS PÁGINAS ---
st.session_state.filtros_ativos = {
    "UF da IES": filtro_ue_ies,
    "Instituição de Ensino": filtro_org_academia,
    "Tipo de Rede": filtro_rede,
    "Nota Mínima IGC": filtro_igc_min,
    "Município do Curso": filtro_municipio_curso,
    "Área de Conhecimento": filtro_area_conhecimento,
    "Grau Acadêmico": filtro_grau_academico,
    "Nome do Curso": filtro_cursos,
    "Modalidade": filtro_modalidade,
    "Situação": filtro_situacao,
    "Nota Mínima CPC": filtro_cpc_min
}

# --- LÓGICA DE FILTRAGEM SEPARADA ---

# Filtra primeiro as IES
base_query_ies = "SELECT * FROM ies_unicas"
clauses_ies = []
params_ies = []

if filtro_ue_ies:
    clauses_ies.append(f"SG_UF_IES IN ({','.join(['?'] * len(filtro_ue_ies))})")
    params_ies.extend(filtro_ue_ies)
if filtro_org_academia:
    clauses_ies.append(f"NO_IES IN ({','.join(['?'] * len(filtro_org_academia))})")
    params_ies.extend(filtro_org_academia)
if filtro_rede:
    clauses_ies.append(f"TP_REDE IN ({','.join(['?'] * len(filtro_rede))})")
    params_ies.extend(filtro_rede)
clauses_ies.append("IGC >= ?")
params_ies.append(float(filtro_igc_min))

query_ies = f"{base_query_ies} WHERE {' AND '.join(clauses_ies)}" if clauses_ies else base_query_ies
ies_df_filtrado = conn.execute(query_ies, params_ies).fetchdf()
ies_df_filtrado = definir_processo_seletivo(ies_df_filtrado)

# Pega os códigos das IES filtradas para usar no filtro de cursos
codigos_ies_filtradas = ies_df_filtrado['CO_IES'].unique().tolist()

# Filtra os Cursos com base nos filtros de curso E nos códigos das IES já filtradas
base_query_cursos = "SELECT * FROM cursos_completos"
clauses_cursos = []
params_cursos = []

if codigos_ies_filtradas:
    clauses_cursos.append(f"CO_IES IN ({','.join(['?'] * len(codigos_ies_filtradas))})")
    params_cursos.extend(codigos_ies_filtradas)

if filtro_municipio_curso:
    clauses_cursos.append(f"NO_MUNICIPIO IN ({','.join(['?'] * len(filtro_municipio_curso))})")
    params_cursos.extend(filtro_municipio_curso)
#... Adicione os outros filtros de curso aqui...
if filtro_area_conhecimento:
    clauses_cursos.append(f"NO_CINE_AREA_ESPECIFICA IN ({','.join(['?'] * len(filtro_area_conhecimento))})")
    params_cursos.extend(filtro_area_conhecimento)
if filtro_grau_academico:
    clauses_cursos.append(f"TP_GRAU_ACADEMICO IN ({','.join(['?'] * len(filtro_grau_academico))})")
    params_cursos.extend(filtro_grau_academico)
if filtro_cursos:
    clauses_cursos.append(f"NO_CURSO IN ({','.join(['?'] * len(filtro_cursos))})")
    params_cursos.extend(filtro_cursos)
if filtro_modalidade:
    clauses_cursos.append(f"TP_MODALIDADE_ENSINO IN ({','.join(['?'] * len(filtro_modalidade))})")
    params_cursos.extend(filtro_modalidade)
    
clauses_cursos.append("CPC >= ?")
params_cursos.append(float(filtro_cpc_min))

query_cursos = f"{base_query_cursos} WHERE {' AND '.join(clauses_cursos)}" if clauses_cursos else base_query_cursos
cursos_df_filtrado = conn.execute(query_cursos, params_cursos).fetchdf()

# Salva no session_state para as outras páginas
st.session_state.df_filtrada = cursos_df_filtrado

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
st.markdown("Use os filtros na barra lateral para pesquisar. **Primeiro filtre as instituições e depois os cursos**.")

col1, col2 = st.columns(2)
col1.metric("Instituições Encontradas", f"{len(ies_df_filtrado)}")
col2.metric("Cursos Encontrados", f"{len(cursos_df_filtrado)}")

# --- VISUALIZAÇÃO ---
st.header("1. Ranking das Instituições de Ensino Superior (IES)")
ies_colunas = ['NO_IES', 'SG_UF_IES', 'PROCESSO_SELETIVO', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']
AgGrid(ies_df_filtrado[ies_colunas], fit_columns_on_grid_load=True, theme='streamlit', key='tabela_ies', height=400)


st.header("2. Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'TP_MODALIDADE_ENSINO', 'NO_MUNICIPIO', 'CC', 'CPC', 'ENADE', 'IDD', 'Situação']
AgGrid(cursos_df_filtrado[cursos_colunas], fit_columns_on_grid_load=True, theme='streamlit', key='tabela_cursos', height=400)
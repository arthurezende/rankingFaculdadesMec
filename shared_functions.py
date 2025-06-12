# shared_functions.py
import streamlit as st
import pandas as pd
import duckdb

@st.cache_resource
def get_db_connection():
    return duckdb.connect(database=':memory:', read_only=False)

@st.cache_data
def carrega_dados_iniciais(_conn, arquivo_parquet='dados_mec.parquet', arquivo_csv='dados_reduzidos_100_mil_linhas.csv'):
    df = None
    try:
        df = pd.read_parquet(arquivo_parquet)
        # st.sidebar.info("⚡ Dados carregados via Parquet (rápido).", icon="✅")
    except Exception:
        # st.sidebar.warning(f"Arquivo Parquet não encontrado. Carregando do CSV '{arquivo_csv}'.")
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

    ies_unicas_df = df.drop_duplicates(subset=['CO_IES'])[['CO_IES', 'NO_IES', 'SG_UF_IES', 'TP_REDE', 'IGC', 'CI']].copy()
    _conn.register('ies_unicas', ies_unicas_df)
    _conn.register('cursos_completos', df)
    
    return df

def inicializar_session_state():
    """Inicializa as chaves do session_state se não existirem."""
    defaults = {
        "filtro_uf_ies": [], "filtro_ies": [], "filtro_rede": [], "filtro_igc": 1,
        "filtro_municipio_curso": [], "filtro_area": [], "filtro_grau": [],
        "filtro_curso_especifico": [], "filtro_modalidade": [], "filtro_cpc": 1
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def criar_filtros_sidebar(df_inicial):
    """Cria todos os widgets da barra lateral e atualiza o session_state."""
    st.sidebar.title("Filtros")
    st.sidebar.header("Instituição")
    st.session_state.filtro_uf_ies = st.sidebar.multiselect('UF da IES', sorted(df_inicial['SG_UF_IES'].dropna().unique()), key='filtro_uf_ies')
    st.session_state.filtro_ies = st.sidebar.multiselect('Instituição de Ensino', sorted(df_inicial['NO_IES'].dropna().unique()), key='filtro_ies')
    st.session_state.filtro_rede = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial['TP_REDE'].dropna().unique()), key='filtro_rede')
    st.session_state.filtro_igc = st.sidebar.slider('Nota Mínima IGC', 1, 5, st.session_state.filtro_igc, key='filtro_igc')

    st.sidebar.header("Curso")
    st.session_state.filtro_municipio_curso = st.sidebar.multiselect('Município do Curso', sorted(df_inicial['NO_MUNICIPIO'].dropna().unique()), key='filtro_municipio_curso')
    st.session_state.filtro_area = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial['NO_CINE_AREA_ESPECIFICA'].dropna().unique()), key='filtro_area')
    st.session_state.filtro_grau = st.sidebar.multiselect('Grau Acadêmico', sorted(df_inicial['TP_GRAU_ACADEMICO'].dropna().unique()), key='filtro_grau')
    st.session_state.filtro_curso_especifico = st.sidebar.multiselect('Nome do Curso (Específico)', sorted(df_inicial['NO_CURSO'].dropna().unique()), key='filtro_curso_especifico')
    st.session_state.filtro_modalidade = st.sidebar.multiselect('Modalidade de Ensino', sorted(df_inicial['TP_MODALIDADE_ENSINO'].dropna().unique()), key='filtro_modalidade')
    st.session_state.filtro_cpc = st.sidebar.slider('Nota Mínima CPC', 1, 5, st.session_state.filtro_cpc, key='filtro_cpc')
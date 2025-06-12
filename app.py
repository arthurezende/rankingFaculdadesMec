# app.py

import streamlit as st
import pandas as pd
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder

# --- CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit) ---
st.set_page_config(layout="wide", page_title="Análise de Dados do MEC", initial_sidebar_state="expanded")

# --- FUNÇÕES (Reutilizáveis) ---
@st.cache_resource
def get_db_connection():
    """Inicia e retorna uma conexão com o DuckDB."""
    return duckdb.connect(database=':memory:', read_only=False)

@st.cache_data
def carrega_dados_iniciais(_conn, arquivo_parquet='dados_mec.parquet', arquivo_csv='dados_reduzidos_100_mil_linhas.csv'):
    """Carrega dados do Parquet ou CSV, processa e registra no DuckDB."""
    df = None
    try:
        df = pd.read_parquet(arquivo_parquet)
        st.sidebar.info("⚡ Dados carregados rapidamente via Parquet.", icon="✅")
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
    
    if 'TP_REDE' in df.columns:
        df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    if 'TP_MODALIDADE_ENSINO' in df.columns:
        df['TP_MODALIDADE_ENSINO'] = df['TP_MODALIDADE_ENSINO'].map({1: 'Presencial', 2: 'EAD'})
    if 'TP_GRAU_ACADEMICO' in df.columns:
        # Lidando com possíveis valores mistos (float e int)
        df['TP_GRAU_ACADEMICO'] = df['TP_GRAU_ACADEMICO'].astype(float).map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})

    _conn.register('mec_data', df)
    return df

def definir_processo_seletivo(ies_df):
    """Aplica heurísticas para determinar o provável processo seletivo."""
    df = ies_df.copy()
    df['PROCESSO_SELETIVO'] = 'Verificar com a instituição'
    
    cond_vest_proprio = df['NO_IES'].str.contains('UNIVERSIDADE DE SÃO PAULO|UNIVERSIDADE ESTADUAL DE CAMPINAS|UNIVERSIDADE ESTADUAL PAULISTA', case=False, na=False)
    cond_sisu = (df['TP_REDE'] == 'Pública') & (df['NO_IES'].str.contains('FEDERAL', case=False, na=False))
    cond_privada = (df['TP_REDE'] == 'Privada')

    df.loc[cond_vest_proprio, 'PROCESSO_SELETIVO'] = 'Vestibular Próprio'
    df.loc[cond_sisu, 'PROCESSO_SELETIVO'] = 'SISU / Vestibular Próprio'
    df.loc[cond_privada, 'PROCESSO_SELETIVO'] = 'Vestibular Próprio / PROUNI / FIES'
    
    return df

# --- INÍCIO DA EXECUÇÃO E CARGA DE DADOS ---

conn = get_db_connection()
if 'df_inicial' not in st.session_state:
    st.session_state.df_inicial = carrega_dados_iniciais(conn)

df_inicial = st.session_state.df_inicial

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.title("Filtros")

st.sidebar.header("Localização e Instituição")
# --- MODIFICAÇÃO: Adicionando chaves (key) únicas para cada widget ---
filtro_ue = st.sidebar.multiselect('UF da IES', sorted(df_inicial['SG_UF_IES'].dropna().unique()), key='filtro_uf_ies')
filtro_municipio = st.sidebar.multiselect('Município do Curso', sorted(df_inicial['NO_MUNICIPIO'].dropna().unique()), key='filtro_municipio_curso')
filtro_org_academia = st.sidebar.multiselect('Instituição de Ensino', sorted(df_inicial['NO_IES'].dropna().unique()), key='filtro_ies')
filtro_rede = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial['TP_REDE'].dropna().unique()), key='filtro_rede')

st.sidebar.header("Curso")
filtro_area_conhecimento = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial['NO_CINE_AREA_ESPECIFICA'].dropna().unique()), key='filtro_area')
filtro_grau_academico = st.sidebar.multiselect('Grau Acadêmico', sorted(df_inicial['TP_GRAU_ACADEMICO'].dropna().unique()), key='filtro_grau')
filtro_cursos = st.sidebar.multiselect('Nome do Curso (Específico)', sorted(df_inicial['NO_CURSO'].dropna().unique()), key='filtro_curso_especifico')
filtro_modalidade = st.sidebar.multiselect('Modalidade de Ensino', sorted(df_inicial['TP_MODALIDADE_ENSINO'].dropna().unique()), key='filtro_modalidade')
filtro_situacao = st.sidebar.selectbox('Situação do Curso', ['Todos'] + list(df_inicial['Situação'].dropna().unique()), key='filtro_situacao')

st.sidebar.header("Qualidade")
filtro_igc_min = st.sidebar.slider('Nota Mínima IGC (Instituição)', 1, 5, 1, key='filtro_igc')
filtro_cpc_min = st.sidebar.slider('Nota Mínima CPC (Curso)', 1, 5, 1, key='filtro_cpc')

# --- APLICA FILTROS E SALVA NO SESSION_STATE ---

def aplica_filtros_sql(conn):
    # ... (Esta função não precisa de mudanças, mas a mantenho aqui por completude) ...
    base_query = "SELECT * FROM mec_data"
    clauses = []
    params = []

    def add_clause(field, values):
        if values:
            clauses.append(f"{field} IN ({','.join(['?'] * len(values))})")
            params.extend(values)

    add_clause('SG_UF_IES', filtro_ue)
    add_clause('NO_MUNICIPIO', filtro_municipio)
    add_clause('NO_IES', filtro_org_academia)
    add_clause('TP_REDE', filtro_rede)
    add_clause('TP_MODALIDADE_ENSINO', filtro_modalidade)
    add_clause('NO_CINE_AREA_ESPECIFICA', filtro_area_conhecimento)
    add_clause('TP_GRAU_ACADEMICO', filtro_grau_academico)
    add_clause('NO_CURSO', filtro_cursos)
    
    if filtro_situacao != 'Todos':
        clauses.append("Situação = ?")
        params.append(filtro_situacao)
    
    clauses.append("IGC >= ?")
    params.append(float(filtro_igc_min))
    clauses.append("CPC >= ?")
    params.append(float(filtro_cpc_min))

    if clauses:
        query = f"{base_query} WHERE {' AND '.join(clauses)}"
    else:
        query = base_query
        
    return conn.execute(query, params).fetchdf()

st.session_state.df_filtrada = aplica_filtros_sql(conn)
df_filtrada = st.session_state.df_filtrada

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
st.markdown("Use os filtros na barra lateral para pesquisar. Os resultados serão atualizados em todas as páginas do menu de navegação.")

total_ies = df_filtrada['CO_IES'].nunique() if not df_filtrada.empty else 0
total_cursos = len(df_filtrada)
col1, col2 = st.columns(2)
col1.metric("Instituições Encontradas", f"{total_ies}")
col2.metric("Cursos Encontrados", f"{total_cursos}")

# Tabelas Interativas
st.header("Ranking das Instituições de Ensino Superior (IES)")
ies_colunas = ['NO_IES', 'SG_UF_IES', 'PROCESSO_SELETIVO', 'TP_REDE', 'IGC', 'Ano IGC', 'CI']
if not df_filtrada.empty:
    ies_df = df_filtrada.drop_duplicates(subset=['CO_IES'])
    ies_df = definir_processo_seletivo(ies_df)
else:
    ies_df = pd.DataFrame(columns=ies_colunas)

gb_ies = GridOptionsBuilder.from_dataframe(ies_df[ies_colunas])
gb_ies.configure_column('NO_IES', headerName='Nome da Instituição', width=350)
gb_ies.configure_column('SG_UF_IES', headerName='UF', width=70)
gb_ies.configure_column('PROCESSO_SELETIVO', headerName='Como Ingressar?', width=250)
gb_ies.configure_column('TP_REDE', headerName='Rede', width=100)
gb_ies.configure_column('IGC', headerName='IGC', width=80, headerTooltip='Índice Geral de Cursos (1 a 5)')
gb_ies.configure_column('CI', headerName='CI', width=80, headerTooltip='Conceito Institucional (1 a 5)')
gb_ies.configure_pagination(paginationAutoPageSize=True)
AgGrid(ies_df, gridOptions=gb_ies.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_ies', height=400)


st.header("Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'TP_MODALIDADE_ENSINO', 'NO_MUNICIPIO', 'CC', 'CPC', 'ENADE', 'IDD', 'Situação']
cursos_df = df_filtrada[cursos_colunas] if not df_filtrada.empty else pd.DataFrame(columns=cursos_colunas)

gb_cursos = GridOptionsBuilder.from_dataframe(cursos_df)
gb_cursos.configure_column('NO_CURSO', headerName='Nome do Curso', width=300)
gb_cursos.configure_column('NO_IES', headerName='Nome da Instituição', width=250)
gb_cursos.configure_column('NO_MUNICIPIO', headerName='Município', width=200)
gb_cursos.configure_column('TP_MODALIDADE_ENSINO', headerName='Modalidade', width=120)
gb_cursos.configure_column('CPC', headerTooltip='Conceito Preliminar de Curso')
gb_cursos.configure_pagination(paginationAutoPageSize=True)
AgGrid(cursos_df, gridOptions=gb_cursos.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_cursos', height=400)
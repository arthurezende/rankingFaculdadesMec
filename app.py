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
        df['TP_GRAU_ACADEMICO'] = df['TP_GRAU_ACADEMICO'].map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})

    _conn.register('mec_data', df)
    return df

def definir_processo_seletivo(ies_df):
    """Aplica heurísticas para determinar o provável processo seletivo."""
    df = ies_df.copy()
    df['PROCESSO_SELETIVO'] = 'Verificar com a instituição'
    
    # Condições para classificação
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
filtro_ue = st.sidebar.multiselect('UF da IES', sorted(df_inicial['SG_UF_IES'].dropna().unique()))
filtro_municipio = st.sidebar.multiselect('Município do Curso', sorted(df_inicial['NO_MUNICIPIO'].dropna().unique()))
filtro_org_academia = st.sidebar.multiselect('Instituição de Ensino', sorted(df_inicial['NO_IES'].dropna().unique()))
filtro_rede = st.sidebar.multiselect('Tipo de Rede', df_inicial['TP_REDE'].dropna().unique())

st.sidebar.header("Curso")
filtro_area_conhecimento = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial['NO_CINE_AREA_ESPECIFICA'].dropna().unique()))
filtro_grau_academico = st.sidebar.multiselect('Grau Acadêmico', sorted(df_inicial['TP_GRAU_ACADEMICO'].dropna().unique()))
filtro_cursos = st.sidebar.multiselect('Nome do Curso (Específico)', sorted(df_inicial['NO_CURSO'].dropna().unique()))
filtro_modalidade = st.sidebar.multiselect('Modalidade de Ensino', df_inicial['TP_MODALIDADE_ENSINO'].dropna().unique())
filtro_situacao = st.sidebar.selectbox('Situação do Curso', ['Todos'] + list(df_inicial['Situação'].dropna().unique()))

st.sidebar.header("Qualidade")
filtro_igc_min = st.sidebar.slider('Nota Mínima IGC (Instituição)', 1, 5, 1)
filtro_cpc_min = st.sidebar.slider('Nota Mínima CPC (Curso)', 1, 5, 1)

# --- APLICA FILTROS E SALVA NO SESSION_STATE ---

def aplica_filtros_sql(conn):
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
    params.append(filtro_igc_min)
    clauses.append("CPC >= ?")
    params.append(filtro_cpc_min)

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

@st.cache_data(ttl=4600)
def carrega_dados():
    # Carrega o dataframe
    df = pd.read_csv('dados_reduzidos_50_mil_linhas-uf.csv', encoding='utf-8', low_memory=False)
    for col in ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD']: 
        df[col] = pd.to_numeric(df[col], errors='coerce') # Usa pandas para converter para inteiro
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'}) #Usando map para exibir o tipo de rede pública ou privada ao invés de 1 ou 2
    return df

# Função do Streamlit para carregar os dados e exibir mensagem visual de carregamento
with st.spinner('Carregando dados...'):
    df_merged = carrega_dados()

# Cria os filtros interativos da barra lateral
st.sidebar.title("Filtros")
# Utiliza o método multiselect do Streamlit para permitir que o usuário selecione mais de um campo ao mesmo tempo
filtro_ue = st.sidebar.multiselect('UF IES', df_merged['SG_UF_IES'].unique())
filtro_municipio = st.sidebar.multiselect('Município do Curso', df_merged['NO_MUNICIPIO'].unique())
filtro_cursos = st.sidebar.multiselect('Nome do Curso', df_merged['NO_CURSO'].unique())
filtro_org_academia = st.sidebar.multiselect('Organização Acadêmica', df_merged['NO_IES'].unique())
filtro_rede = st.sidebar.multiselect('Tipo de Rede', ['Pública', 'Privada'])

# Cria uma selectbox para filtrar pela situação do curso
filtro_situacao = st.sidebar.selectbox('Situação do Curso', ['Todos'] + list(df_merged['Situação'].unique()))

def aplica_filtros(df):
    if filtro_ue:
        df = df[df['SG_UF_IES'].isin(filtro_ue)]
    if filtro_municipio:
        df = df[df['NO_MUNICIPIO'].isin(filtro_municipio)]
    if filtro_cursos:
        df = df[df['NO_CURSO'].isin(filtro_cursos)]
    if filtro_org_academia:
        df = df[df['NO_IES'].isin(filtro_org_academia)]
    if filtro_rede:
        df = df[df['TP_REDE'].isin(filtro_rede)]
    if filtro_situacao != 'Todos':
        df = df[df['Situação'] == filtro_situacao]
    return df

# Chama a função que aplica os filtros em tempo real no dataframe
df_filtrada = aplica_filtros(df_merged)

# Função que monta a barra lateral, paginação automática
def cria_aggrid(df, columns, key, column_config=None):
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
        recarrega_dados=False,
        key=key
    )

# Visualização 1: Ranking IES
st.header("Ranking das IES")
ies_colunas = ['NO_IES', 'SG_UF_IES', 'NO_MUNICIPIO_IES', 'TP_REDE', 'CI', 'CI-EaD', 'IGC', 'Ano CI', 'Ano CI-EaD', 'Ano IGC'] #define as colunas que serão exibidas das IES
ies_df = df_filtrada.drop_duplicates(subset=['CO_IES'])[ies_colunas] #cria o dataframe das IES sem duplicadas apenas com as colunas de ies_colunas

config_colunas_ies = {
    'NO_IES': {'headerName': 'Nome da Instituição', 'width': 225},
    'SG_UF_IES': {'headerName': 'UF IES'},
    'NO_MUNICIPIO_IES': {'headerName': 'Município IES'},
    'TP_REDE': {'headerName': 'Rede'}
}

# Chama a função que monta a visualização das IES
cria_aggrid(ies_df, ies_colunas, 'tabela_ies', config_colunas_ies)

# Visualização 2: Ranking Cursos
st.header("Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'NO_MUNICIPIO', 'CC', 'Ano CC', 'CPC', 'ENADE', 'Ano ENADE', 'IDD', 'Situação']
cursos_df = df_filtrada[cursos_colunas]

cursos_colunas_config = {
    'NO_CURSO': {'headerName': 'Nome do Curso', 'width': 300},
    'NO_IES': {'headerName': 'Nome da Instituição', 'width': 225},
    'NO_MUNICIPIO': {'headerName': 'Município Curso'}
}

# Chama a função que monta a visualização dos cursos
cria_aggrid(cursos_df, cursos_colunas, 'tabela_cursos', cursos_colunas_config)

st.write(f"Total de registros: {len(df_filtrada)}")

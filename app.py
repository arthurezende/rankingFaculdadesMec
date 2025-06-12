import streamlit as st
import pandas as pd
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

# Aparência da página
st.set_page_config(layout="wide", page_title="Análise de Dados do MEC", initial_sidebar_state="expanded")

# Cabeçalho
st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Faculdade Exame - Projeto Extensionista: Análise Educacional e Apoio à Escolha de Cursos com Base nos Dados do INEP</h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
Esta plataforma permite a análise interativa de dados sobre Instituições de Ensino Superior (IES) e cursos de graduação no Brasil, 
com base nos microdados do Censo da Educação Superior do INEP. Utilize os filtros na barra lateral para refinar sua busca e encontrar a melhor opção para você.
""")

with st.expander("ℹ️ Entenda os Critérios de Avaliação (IGC, CPC, ENADE)"):
    st.markdown("""
        Para auxiliar na sua escolha, utilizamos diversas métricas de qualidade do Ministério da Educação (MEC). Veja o que cada uma significa:

        - **CI (Conceito Institucional):** Nota que a instituição recebe após uma avaliação presencial de especialistas do MEC. Varia de 1 a 5.
        - **CI-EaD (Conceito Institucional EaD):** Mesma avaliação do CI, mas focada especificamente na modalidade de Ensino a Distância.
        - **IGC (Índice Geral de Cursos):** É o indicador de qualidade mais completo, pois considera a média das notas dos cursos de graduação (CPC) e pós-graduação (Mestrado e Doutorado) da instituição. É a principal métrica para avaliar a qualidade geral de uma IES.
        - **CPC (Conceito Preliminar de Curso):** Avalia a qualidade dos cursos de graduação. Leva em conta o desempenho dos estudantes no ENADE, a qualidade do corpo docente (mestres e doutores), e a percepção dos alunos sobre o curso.
        - **ENADE (Conceito ENADE):** Mede o desempenho dos estudantes concluintes dos cursos de graduação em relação aos conteúdos programáticos, habilidades e competências. Uma nota alta indica que os alunos do curso estão saindo bem preparados.
        - **IDD (Indicador de Diferença entre os Desempenhos):** Mede o valor que o curso agregou ao desenvolvimento do estudante, comparando seu desempenho no ENADE com seu desempenho no ENEM.
    """)

@st.cache_resource
def get_db_connection():
    # Usamos uma conexão em memória do DuckDB para máxima velocidade.
    return duckdb.connect(database=':memory:', read_only=False)

@st.cache_data
def carrega_dados_iniciais(_conn, arquivo_parquet='dados_mec.parquet'):
    """
    Carrega os dados do arquivo Parquet para um DataFrame Pandas.
    Esta função é executada apenas uma vez e o resultado fica em cache.
    O DataFrame é usado para popular os filtros da sidebar.
    """
    try:
        df = pd.read_parquet(arquivo_parquet)
    except FileNotFoundError:
        st.error(f"Arquivo '{arquivo_parquet}' não encontrado. Por favor, execute o script 'converter_para_parquet.py' primeiro.")
        return pd.DataFrame()

    # Conversões e Mapeamentos
    cols_numericas = ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD']
    for col in cols_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    df['TP_MODALIDADE_ENSINO'] = df['TP_MODALIDADE_ENSINO'].map({1: 'Presencial', 2: 'EAD'})
    
    # Registrar o DataFrame como uma tabela no DuckDB para consultas SQL
    _conn.register('mec_data', df)
    return df

# Conexão e carregamento de dados
conn = get_db_connection()
df_inicial = carrega_dados_iniciais(conn)

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.title("Filtros")

# Utiliza os valores únicos do dataframe inicial para popular os filtros
filtro_ue = st.sidebar.multiselect('UF da IES', sorted(df_inicial['SG_UF_IES'].dropna().unique()))
filtro_municipio = st.sidebar.multiselect('Município do Curso', sorted(df_inicial['NO_MUNICIPIO'].dropna().unique()))
filtro_cursos = st.sidebar.multiselect('Nome do Curso', sorted(df_inicial['NO_CURSO'].dropna().unique()))
filtro_org_academia = st.sidebar.multiselect('Instituição de Ensino', sorted(df_inicial['NO_IES'].dropna().unique()))
filtro_rede = st.sidebar.multiselect('Tipo de Rede', ['Pública', 'Privada'])
# NOVO FILTRO: Modalidade de Ensino
filtro_modalidade = st.sidebar.multiselect('Modalidade de Ensino', ['Presencial', 'EAD'])
filtro_situacao = st.sidebar.selectbox('Situação do Curso', ['Todos'] + list(df_inicial['Situação'].dropna().unique()))

def aplica_filtros_sql(conn):
    """
    Constrói e executa uma query SQL no DuckDB para aplicar os filtros.
    Isso é ordens de magnitude mais rápido que usar filtros do Pandas.
    """
    base_query = "SELECT * FROM mec_data"
    clauses = ["1=1"]  # Inicia com uma cláusula verdadeira para facilitar a concatenação

    if filtro_ue:
        clauses.append(f"SG_UF_IES IN {tuple(filtro_ue)}")
    if filtro_municipio:
        clauses.append(f"NO_MUNICIPIO IN {tuple(filtro_municipio)}")
    if filtro_cursos:
        clauses.append(f"NO_CURSO IN {tuple(filtro_cursos)}")
    if filtro_org_academia:
        clauses.append(f"NO_IES IN {tuple(filtro_org_academia)}")
    if filtro_rede:
        clauses.append(f"TP_REDE IN {tuple(filtro_rede)}")
    if filtro_modalidade:
        clauses.append(f"TP_MODALIDADE_ENSINO IN {tuple(filtro_modalidade)}")
    if filtro_situacao != 'Todos':
        clauses.append(f"Situação = '{filtro_situacao}'")

    query = f"{base_query} WHERE {' AND '.join(clauses)}"
    return conn.execute(query).fetchdf()

# Chama a função que aplica os filtros em tempo real no dataframe
df_filtrada = aplica_filtros_sql(conn)

# Função que monta a barra lateral, paginação automática
def cria_aggrid(df, columns, key, column_config=None):
    gb = GridOptionsBuilder.from_dataframe(df[columns])
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection('single', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
    gb.configure_default_column(sorteable=True, filterable=True, resizable=True, width=120)
    
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
        key=key,
        # O parâmetro 'recarrega_dados' não existe mais como 'allow_unsafe_jscode'
        allow_unsafe_jscode=True # Necessário para algumas funcionalidades avançadas do AgGrid
    )

# --- VISUALIZAÇÕES ---

st.header("Ranking das IES")
ies_colunas = ['NO_IES', 'SG_UF_IES', 'NO_MUNICIPIO_IES', 'TP_REDE', 'CI', 'CI-EaD', 'IGC', 'Ano CI', 'Ano CI-EaD', 'Ano IGC']
if not df_filtrada.empty:
    ies_df = df_filtrada.drop_duplicates(subset=['CO_IES'])[ies_colunas]
else:
    ies_df = pd.DataFrame(columns=ies_colunas)

config_colunas_ies = {
    'NO_IES': {'headerName': 'Nome da Instituição', 'width': 300},
    'SG_UF_IES': {'headerName': 'UF IES', 'width': 100},
    'NO_MUNICIPIO_IES': {'headerName': 'Município IES', 'width': 200},
    'TP_REDE': {'headerName': 'Rede', 'width': 100}
}
cria_aggrid(ies_df, ies_colunas, 'tabela_ies', config_colunas_ies)

st.header("Ranking dos Cursos")
cursos_colunas = ['NO_CURSO', 'NO_IES', 'TP_MODALIDADE_ENSINO', 'NO_MUNICIPIO', 'CC', 'Ano CC', 'CPC', 'ENADE', 'Ano ENADE', 'IDD', 'Situação']
cursos_df = df_filtrada[cursos_colunas] if not df_filtrada.empty else pd.DataFrame(columns=cursos_colunas)

cursos_colunas_config = {
    'NO_CURSO': {'headerName': 'Nome do Curso', 'width': 300},
    'NO_IES': {'headerName': 'Nome da Instituição', 'width': 250},
    'NO_MUNICIPIO': {'headerName': 'Município Curso', 'width': 200},
    'TP_MODALIDADE_ENSINO': {'headerName': 'Modalidade', 'width': 120},
}
cria_aggrid(cursos_df, cursos_colunas, 'tabela_cursos', cursos_colunas_config)

st.write(f"Total de registros encontrados: {len(df_filtrada)}")

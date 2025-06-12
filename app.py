import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

# Aparência da página
st.set_page_config(layout="wide", page_title="Análise de Dados do MEC", initial_sidebar_state="expanded")

# Cabeçalho
st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Faculdade Exame Saint Paul - Projeto Extensionista: Análise Educacional e Apoio à Escolha de Cursos com Base nos Dados do INEP</h3>
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

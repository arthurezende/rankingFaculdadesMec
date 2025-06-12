# pages/Analise_Avancada.py

import streamlit as st
import pandas as pd
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Análise Avançada - Análise MEC")

# --- FUNÇÕES (Replicadas para independência) ---
@st.cache_resource
def get_db_connection_analise():
    return duckdb.connect(database=':memory:', read_only=False)

@st.cache_data
def carrega_dados_iniciais_analise(_conn, arquivo_parquet='dados_mec.parquet', arquivo_csv='dados_reduzidos_100_mil_linhas.csv'):
    df = None
    try:
        df = pd.read_parquet(arquivo_parquet)
    except Exception:
        try:
            df = pd.read_csv(arquivo_csv, encoding='utf-8', low_memory=False)
        except FileNotFoundError:
            st.error("Arquivo de dados não encontrado.")
            st.stop()

    cols_numericas = ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD', 'QT_VG_TOTAL', 'QT_INSCRITO_TOTAL']
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    df['TP_MODALIDADE_ENSINO'] = df['TP_MODALIDADE_ENSINO'].map({1: 'Presencial', 2: 'EAD'})
    df['TP_GRAU_ACADEMICO'] = df['TP_GRAU_ACADEMICO'].astype(float).map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})

    _conn.register('mec_data_analise', df)
    return df

# --- CARREGAMENTO INICIAL PARA ESTA PÁGINA ---
conn_analise = get_db_connection_analise()
df_inicial_analise = carrega_dados_iniciais_analise(conn_analise)

# --- BARRA LATERAL DE FILTROS PARA ESTA PÁGINA ---
st.sidebar.title("Filtros da Análise")
st.sidebar.info("Estes filtros são independentes e se aplicam apenas aos gráficos nesta página.")

filtro_area = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial_analise['NO_CINE_AREA_ESPECIFICA'].dropna().unique()), key='analise_filtro_area')
filtro_uf_grafico = st.sidebar.multiselect('UF do Curso', sorted(df_inicial_analise['SG_UF'].dropna().unique()), key='analise_filtro_uf')
filtro_rede_grafico = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial_analise['TP_REDE'].dropna().unique()), key='analise_filtro_rede')
filtro_modalidade_grafico = st.sidebar.multiselect('Modalidade', sorted(df_inicial_analise['TP_MODALIDADE_ENSINO'].dropna().unique()), key='analise_filtro_modalidade')

# --- LÓGICA DE FILTRAGEM PARA GRÁFICOS ---
def aplica_filtros_graficos(conn):
    base_query = "SELECT * FROM mec_data_analise"
    clauses = []
    params = []

    def add_clause(field, values):
        if values:
            clauses.append(f"{field} IN ({','.join(['?'] * len(values))})")
            params.extend(values)

    add_clause('NO_CINE_AREA_ESPECIFICA', filtro_area)
    add_clause('SG_UF', filtro_uf_grafico)
    add_clause('TP_REDE', filtro_rede_grafico)
    add_clause('TP_MODALIDADE_ENSINO', filtro_modalidade_grafico)

    if clauses:
        query = f"{base_query} WHERE {' AND '.join(clauses)}"
    else:
        query = base_query
    
    return conn.execute(query, params).fetchdf()

df_filtrada_analise = aplica_filtros_graficos(conn_analise)

# --- LAYOUT PRINCIPAL ---
st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Análise Visual e Insights</h3>
    </div>
    """,
    unsafe_allow_html=True
)

if not df_filtrada_analise.empty:
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Top 15 Cursos por Quantidade")
        cursos_counts = df_filtrada_analise['NO_CURSO'].value_counts().head(15)
        st.bar_chart(cursos_counts)

    with col_graf2:
        st.subheader("Cursos por Modalidade")
        modalidade_counts = df_filtrada_analise['TP_MODALIDADE_ENSINO'].value_counts()
        st.bar_chart(modalidade_counts)

    st.subheader("Análise de Concorrência (Candidato/Vaga)")
    st.markdown("Esta tabela mostra a relação entre o número de inscritos e vagas. Use os filtros na barra lateral para refinar.")
    
    df_concorrencia = df_filtrada_analise[['NO_CURSO', 'NO_IES', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']].copy()
    df_concorrencia.dropna(subset=['QT_INSCRITO_TOTAL', 'QT_VG_TOTAL'], inplace=True)
    df_concorrencia = df_concorrencia[(df_concorrencia['QT_VG_TOTAL'] > 0) & (df_concorrencia['QT_INSCRITO_TOTAL'] > 0)]
    
    if not df_concorrencia.empty:
        df_concorrencia['Candidatos por Vaga'] = (df_concorrencia['QT_INSCRITO_TOTAL'] / df_concorrencia['QT_VG_TOTAL']).round(2)
        df_concorrencia_view = df_concorrencia.sort_values(by='Candidatos por Vaga', ascending=False)
        
        gb = GridOptionsBuilder.from_dataframe(df_concorrencia_view[['NO_CURSO', 'NO_IES', 'Candidatos por Vaga', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']])
        gb.configure_column('NO_CURSO', headerName='Curso', width=350)
        gb.configure_column('NO_IES', headerName='Instituição', width=300)
        gb.configure_pagination(paginationAutoPageSize=True)

        AgGrid(df_concorrencia_view, gridOptions=gb.build(), fit_columns_on_grid_load=True, theme='streamlit', key='tabela_concorrencia', height=400)
    else:
        st.warning("Não há dados de inscritos/vagas para os filtros selecionados.")
else:
    st.warning("Nenhum dado encontrado. Tente remover alguns filtros na barra lateral.")
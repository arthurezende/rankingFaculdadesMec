# pages/Analise_Avancada.py

import streamlit as st
import pandas as pd
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide", page_title="Análise Avançada - Análise MEC")

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

    cols_numericas = ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD', 'QT_VG_TOTAL', 'QT_INSCRITO_TOTAL', 'CO_IES']
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    df['TP_MODALIDADE_ENSINO'] = df['TP_MODALIDADE_ENSINO'].map({1: 'Presencial', 2: 'EAD'})
    df['TP_GRAU_ACADEMICO'] = df['TP_GRAU_ACADEMICO'].astype(float).map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})

    _conn.register('mec_data_analise', df)
    return df

conn_analise = get_db_connection_analise()
df_inicial_analise = carrega_dados_iniciais_analise(conn_analise)

st.sidebar.title("Filtros da Análise")
st.sidebar.info("Estes filtros se aplicam apenas aos gráficos e tabelas nesta página.")

filtro_area = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial_analise['NO_CINE_AREA_ESPECIFICA'].dropna().unique()), key='analise_filtro_area')
filtro_uf_grafico = st.sidebar.multiselect('UF do Curso', sorted(df_inicial_analise['SG_UF'].dropna().unique()), key='analise_filtro_uf')
filtro_rede_grafico = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial_analise['TP_REDE'].dropna().unique()), key='analise_filtro_rede')
filtro_modalidade_grafico = st.sidebar.multiselect('Modalidade', sorted(df_inicial_analise['TP_MODALIDADE_ENSINO'].dropna().unique()), key='analise_filtro_modalidade')

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

st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Análise Visual e Insights</h3>
    </div>
    """,
    unsafe_allow_html=True
)

if not df_filtrada_analise.empty:
    
    # --- ANÁLISE DE CONCORRÊNCIA COMO PRIMEIRO ITEM ---
    st.header("Análise de Concorrência (Candidato/Vaga)")
    st.markdown("Esta tabela mostra a relação entre o número de inscritos e vagas. Use os filtros na barra lateral para refinar.")
    
    df_concorrencia = df_filtrada_analise[['NO_CURSO', 'NO_IES', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']].copy()
    df_concorrencia.dropna(subset=['QT_INSCRITO_TOTAL', 'QT_VG_TOTAL'], inplace=True)
    df_concorrencia = df_concorrencia[(df_concorrencia['QT_VG_TOTAL'] > 0) & (df_concorrencia['QT_INSCRITO_TOTAL'] > 0)]
    
    if not df_concorrencia.empty:
        df_concorrencia['Candidatos por Vaga'] = (df_concorrencia['QT_INSCRITO_TOTAL'] / df_concorrencia['QT_VG_TOTAL']).round(2)
        df_concorrencia_view = df_concorrencia.sort_values(by='Candidatos por Vaga', ascending=False)
        
        # Coluna UF removida da visualização
        st.dataframe(
            df_concorrencia_view[['NO_CURSO', 'NO_IES', 'Candidatos por Vaga', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']],
            use_container_width=True, height=400,
            column_config={
                "NO_CURSO": "Curso", "NO_IES": "Instituição",
                "QT_INSCRITO_TOTAL": st.column_config.NumberColumn("Inscritos", format="%d"),
                "QT_VG_TOTAL": st.column_config.NumberColumn("Vagas", format="%d")
            }
        )
    else:
        st.warning("Não há dados de inscritos/vagas para os filtros selecionados.")
    
    st.divider()

    # --- GRÁFICOS EM COLUNAS ---
    st.header("Visão Geral dos Cursos")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 15 Cursos por Quantidade")
        cursos_counts = df_filtrada_analise['NO_CURSO'].value_counts().head(15)
        st.bar_chart(cursos_counts, use_container_width=True)

    with col2:
        st.subheader("Cursos por Modalidade")
        modalidade_counts = df_filtrada_analise['TP_MODALIDADE_ENSINO'].value_counts()
        st.bar_chart(modalidade_counts, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 10 Instituições com Mais Cursos")
        top_ies_counts = df_filtrada_analise['NO_IES'].value_counts().head(10)
        st.bar_chart(top_ies_counts)
    
    with col4:
        st.subheader("Cursos por Grau Acadêmico")
        grau_counts = df_filtrada_analise['TP_GRAU_ACADEMICO'].value_counts()
        st.bar_chart(grau_counts, use_container_width=True)

else:
    st.warning("Nenhum dado encontrado. Tente remover alguns filtros na barra lateral.")
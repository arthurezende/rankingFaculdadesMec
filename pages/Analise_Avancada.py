# pages/Analise_Avancada.py
import streamlit as st
import pandas as pd
import duckdb

st.set_page_config(layout="wide", page_title="Análise Avançada - Análise MEC")

@st.cache_resource
def get_db_connection_analise():
    return duckdb.connect(database=':memory:', read_only=False)

@st.cache_data
def carrega_dados_iniciais_analise(_conn, arquivo_csv='dados_reduzidos_100_mil_linhas.csv'):
    try:
        query = f"SELECT * FROM read_csv_auto('{arquivo_csv}')"
        df = _conn.execute(query).fetchdf()
    except Exception as e:
        st.error(f"ERRO CRÍTICO ao carregar dados para análise: {e}")
        st.stop()
    
    df['TP_REDE'] = pd.to_numeric(df['TP_REDE'], errors='coerce').map({1.0: 'Pública', 2.0: 'Privada'})
    df['TP_MODALIDADE_ENSINO'] = pd.to_numeric(df['TP_MODALIDADE_ENSINO'], errors='coerce').map({1.0: 'Presencial', 2.0: 'EAD'})
    return df

conn_analise = get_db_connection_analise()
df_inicial_analise = carrega_dados_iniciais_analise(conn_analise)

st.sidebar.title("Filtros da Análise")
st.sidebar.info("Estes filtros se aplicam apenas aos gráficos e tabelas nesta página.")

filtro_area = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial_analise['NO_CINE_AREA_ESPECIFICA'].dropna().unique()), key='analise_filtro_area')
filtro_uf_grafico = st.sidebar.multiselect('UF do Curso', sorted(df_inicial_analise['SG_UF'].dropna().unique()), key='analise_filtro_uf')
filtro_rede_grafico = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial_analise['TP_REDE'].dropna().unique()), key='analise_filtro_rede')

df_filtrada_analise = df_inicial_analise.copy()
if filtro_area:
    df_filtrada_analise = df_filtrada_analise[df_filtrada_analise['NO_CINE_AREA_ESPECIFICA'].isin(filtro_area)]
if filtro_uf_grafico:
    df_filtrada_analise = df_filtrada_analise[df_filtrada_analise['SG_UF'].isin(filtro_uf_grafico)]
if filtro_rede_grafico:
    df_filtrada_analise = df_filtrada_analise[df_filtrada_analise['TP_REDE'].isin(filtro_rede_grafico)]

st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Análise Visual e Insights</h3>
    </div>
    """,
    unsafe_allow_html=True
)

if not df_filtrada_analise.empty:
    st.header("Análise de Concorrência (Candidato/Vaga)")
    df_concorrencia = df_filtrada_analise[['NO_CURSO', 'NO_IES', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']].copy()
    df_concorrencia.dropna(subset=['QT_INSCRITO_TOTAL', 'QT_VG_TOTAL'], inplace=True)
    df_concorrencia = df_concorrencia[(df_concorrencia['QT_VG_TOTAL'] > 0) & (df_concorrencia['QT_INSCRITO_TOTAL'] > 0)]
    
    if not df_concorrencia.empty:
        df_concorrencia['Candidatos por Vaga'] = (df_concorrencia['QT_INSCRITO_TOTAL'] / df_concorrencia['QT_VG_TOTAL']).round(2)
        df_concorrencia_view = df_concorrencia.sort_values(by='Candidatos por Vaga', ascending=False)
        st.dataframe(
            df_concorrencia_view[['NO_CURSO', 'NO_IES', 'Candidatos por Vaga', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']],
            use_container_width=True, height=400
        )
    else:
        st.warning("Não há dados de concorrência para os filtros selecionados.")
    
    st.divider()

    st.header("Visão Geral dos Cursos")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 15 Cursos por Quantidade")
        st.bar_chart(df_filtrada_analise['NO_CURSO'].value_counts().head(15))
    with col2:
        st.subheader("Cursos por Modalidade")
        st.bar_chart(df_filtrada_analise['TP_MODALIDADE_ENSINO'].value_counts())
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")

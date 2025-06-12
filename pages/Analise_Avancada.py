# pages/Analise_Avancada.py

import streamlit as st
import pandas as pd
import duckdb

# Configuração da página
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

    cols_numericas = ['CI', 'CI-EaD', 'IGC', 'CC', 'CPC', 'ENADE', 'IDD', 'QT_VG_TOTAL', 'QT_INSCRITO_TOTAL', 'CO_IES']
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['TP_REDE'] = df['TP_REDE'].map({1: 'Pública', 2: 'Privada'})
    df['TP_MODALIDADE_ENSINO'] = df['TP_MODALIDADE_ENSINO'].map({1: 'Presencial', 2: 'EAD'})
    df['TP_GRAU_ACADEMICO'] = df['TP_GRAU_ACADEMICO'].astype(float).map({1.0: 'Bacharelado', 2.0: 'Licenciatura', 3.0: 'Tecnológico'})
    
    # Adicionando coordenadas aproximadas para o mapa
    coords = {
        'AC': [-9.97, -67.81], 'AL': [-9.66, -35.73], 'AP': [0.03, -51.06], 'AM': [-3.11, -60.02],
        'BA': [-12.97, -38.50], 'CE': [-3.71, -38.54], 'DF': [-15.78, -47.92], 'ES': [-20.31, -40.33],
        'GO': [-16.68, -49.25], 'MA': [-2.53, -44.30], 'MT': [-15.59, -56.09], 'MS': [-20.44, -54.64],
        'MG': [-19.92, -43.93], 'PA': [-1.45, -48.49], 'PB': [-7.11, -34.86], 'PR': [-25.42, -49.27],
        'PE': [-8.05, -34.88], 'PI': [-5.09, -42.80], 'RJ': [-22.90, -43.17], 'RN': [-5.79, -35.20],
        'RS': [-30.03, -51.22], 'RO': [-8.76, -63.90], 'RR': [2.82, -60.67], 'SC': [-27.59, -48.54],
        'SP': [-23.55, -46.63], 'SE': [-10.91, -37.07], 'TO': [-10.16, -48.33]
    }
    df['lat'] = df['SG_UF'].map(lambda x: coords.get(x, [0,0])[0])
    df['lon'] = df['SG_UF'].map(lambda x: coords.get(x, [0,0])[1])

    _conn.register('mec_data_analise', df)
    return df

# --- CARREGAMENTO INICIAL PARA ESTA PÁGINA ---
conn_analise = get_db_connection_analise()
df_inicial_analise = carrega_dados_iniciais_analise(conn_analise)

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.title("Filtros da Análise")
st.sidebar.info("Estes filtros se aplicam apenas aos gráficos e tabelas nesta página.")

filtro_area = st.sidebar.multiselect('Área de Conhecimento', sorted(df_inicial_analise['NO_CINE_AREA_ESPECIFICA'].dropna().unique()), key='analise_filtro_area')
filtro_uf_grafico = st.sidebar.multiselect('UF do Curso', sorted(df_inicial_analise['SG_UF'].dropna().unique()), key='analise_filtro_uf')
filtro_rede_grafico = st.sidebar.multiselect('Tipo de Rede', sorted(df_inicial_analise['TP_REDE'].dropna().unique()), key='analise_filtro_rede')
filtro_modalidade_grafico = st.sidebar.multiselect('Modalidade', sorted(df_inicial_analise['TP_MODALIDADE_ENSINO'].dropna().unique()), key='analise_filtro_modalidade')

# --- LÓGICA DE FILTRAGEM ---
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

query = f"{base_query} WHERE {' AND '.join(clauses)}" if clauses else base_query
df_filtrada_analise = conn_analise.execute(query, params).fetchdf()

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
    # --- GRÁFICOS EM COLUNAS ---
    st.header("Visão Geral dos Cursos")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cursos por Modalidade")
        modalidade_counts = df_filtrada_analise['TP_MODALIDADE_ENSINO'].value_counts()
        st.bar_chart(modalidade_counts, use_container_width=True)
    
    with col2:
        st.subheader("Cursos por Grau Acadêmico")
        grau_counts = df_filtrada_analise['TP_GRAU_ACADEMICO'].value_counts()
        st.bar_chart(grau_counts, use_container_width=True)

    st.divider()

    # --- NOVO GRÁFICO: MAPA ---
    st.header("Distribuição Geográfica")
    st.subheader("Concentração de Cursos por Estado")
    map_data = df_filtrada_analise[df_filtrada_analise['lat'] != 0][['lat', 'lon']].copy()
    st.map(map_data, zoom=3)

    st.divider()

    # --- NOVOS GRÁFICOS DE RANKING ---
    st.header("Rankings e Comparações")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 10 Instituições com Mais Cursos")
        top_ies_counts = df_filtrada_analise['NO_IES'].value_counts().head(10)
        st.bar_chart(top_ies_counts)
    
    with col4:
        st.subheader("Top 10 Cursos mais Ofertados")
        top_cursos_counts = df_filtrada_analise['NO_CURSO'].value_counts().head(10)
        st.bar_chart(top_cursos_counts)

    st.divider()

    # --- TABELA DE CONCORRÊNCIA ATUALIZADA ---
    st.header("Análise de Concorrência")
    st.markdown("Relação candidato/vaga. Disponível apenas para cursos presenciais com dados informados.")
    
    df_concorrencia = df_filtrada_analise[['NO_CURSO', 'NO_IES', 'SG_UF', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']].copy()
    df_concorrencia.dropna(subset=['QT_INSCRITO_TOTAL', 'QT_VG_TOTAL'], inplace=True)
    df_concorrencia = df_concorrencia[(df_concorrencia['QT_VG_TOTAL'] > 0) & (df_concorrencia['QT_INSCRITO_TOTAL'] > 0)]
    
    if not df_concorrencia.empty:
        df_concorrencia['Candidatos por Vaga'] = (df_concorrencia['QT_INSCRITO_TOTAL'] / df_concorrencia['QT_VG_TOTAL']).round(2)
        df_concorrencia_view = df_concorrencia.sort_values(by='Candidatos por Vaga', ascending=False)
        
        # COLUNA UF ADICIONADA AQUI
        st.dataframe(
            df_concorrencia_view[['NO_CURSO', 'NO_IES', 'SG_UF', 'Candidatos por Vaga', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']],
            use_container_width=True,
            height=400,
            column_config={
                "NO_CURSO": "Curso",
                "NO_IES": "Instituição",
                "SG_UF": st.column_config.TextColumn("UF", width="small"),
                "QT_INSCRITO_TOTAL": st.column_config.NumberColumn("Inscritos", format="%d"),
                "QT_VG_TOTAL": st.column_config.NumberColumn("Vagas", format="%d")
            }
        )
    else:
        st.warning("Não há dados de inscritos/vagas para os filtros selecionados.")
else:
    st.warning("Nenhum dado encontrado. Tente remover alguns filtros na barra lateral.")
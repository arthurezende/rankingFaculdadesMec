import streamlit as st
import pandas as pd
import duckdb
from st_aggrid import AgGrid, GridOptionsBuilder

# --- ADICIONE ESTE BLOCO PARA CORRIGIR A IMPORTAÇÃO ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- FIM DO BLOCO DE CORREÇÃO ---

from pages.shared_functions import get_db_connection, carrega_dados_iniciais, criar_filtros_sidebar, inicializar_session_state, definir_processo_seletivo

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Visão Geral - Análise MEC", initial_sidebar_state="expanded")

# --- CARREGAMENTO E INICIALIZAÇÃO ---
conn = get_db_connection()
if 'df_inicial' not in st.session_state:
    st.session_state.df_inicial = carrega_dados_iniciais(conn)
df_inicial = st.session_state.df_inicial

# Inicializa o session_state para os filtros
inicializar_session_state()

# --- BARRA LATERAL ---
# A barra lateral é criada aqui e seus valores são salvos no session_state
criar_filtros_sidebar(df_inicial)

# --- LÓGICA DE FILTRAGEM ---
# Filtra IES com base nos filtros da barra lateral
query_ies = "SELECT * FROM ies_unicas WHERE IGC >= ? AND NO_IES LIKE ? AND SG_UF_IES LIKE ? AND TP_REDE LIKE ?"
params_ies = [
    st.session_state.filtro_igc,
    f"%{st.session_state.filtro_ies[0]}%" if st.session_state.filtro_ies else "%",
    f"%{st.session_state.filtro_uf_ies[0]}%" if st.session_state.filtro_uf_ies else "%",
    f"%{st.session_state.filtro_rede[0]}%" if st.session_state.filtro_rede else "%",
]
ies_df_filtrado = conn.execute(query_ies, params_ies).fetchdf()
ies_df_filtrado = definir_processo_seletivo(ies_df_filtrado)

# Filtra Cursos com base nos filtros da barra lateral
codigos_ies_filtradas = ies_df_filtrado['CO_IES'].unique().tolist()
# ... (aqui entraria a lógica de filtragem dos cursos se necessário, por enquanto vamos mostrar todos das IES filtradas)
st.session_state.df_filtrada = df_inicial[df_inicial['CO_IES'].isin(codigos_ies_filtradas)]


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

col1, col2 = st.columns(2)
col1.metric("Instituições Encontradas", f"{len(ies_df_filtrado)}")
col2.metric("Cursos Encontrados", f"{len(st.session_state.df_filtrada)}")

st.header("1. Ranking das Instituições de Ensino Superior (IES)")
AgGrid(ies_df_filtrado, fit_columns_on_grid_load=True, theme='streamlit', key='tabela_ies', height=400)

st.header("2. Ranking dos Cursos")
AgGrid(st.session_state.df_filtrada, fit_columns_on_grid_load=True, theme='streamlit', key='tabela_cursos', height=400)
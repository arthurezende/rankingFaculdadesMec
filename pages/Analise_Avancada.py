import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# --- ADICIONE ESTE BLOCO PARA CORRIGIR A IMPORTAÇÃO ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- FIM DO BLOCO DE CORREÇÃO ---

from shared_functions import criar_filtros_sidebar, inicializar_session_state

st.set_page_config(layout="wide", page_title="Análise Avançada")

st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Análise Visual e Insights</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# Inicializa e cria os filtros na barra lateral, mantendo o estado
inicializar_session_state()
if 'df_inicial' in st.session_state:
    criar_filtros_sidebar(st.session_state.df_inicial)
else:
    st.warning("Por favor, acesse a página 'app' primeiro para carregar os dados.")
    st.stop()


# A lógica de filtragem agora é feita diretamente aqui, usando o estado da sessão
df_filtrada = st.session_state.get('df_filtrada', pd.DataFrame())


st.header("Análises Gráficas")
if not df_filtrada.empty:
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Distribuição de Cursos por Estado")
        cursos_por_uf = df_filtrada['SG_UF'].value_counts().sort_values(ascending=False)
        st.bar_chart(cursos_por_uf)

    with col_graf2:
        st.subheader("Distribuição por Área de Conhecimento")
        cursos_por_area = df_filtrada['NO_CINE_AREA_ESPECIFICA'].value_counts().head(15)
        st.bar_chart(cursos_por_area)
        
    # Resto do seu código de análise aqui...
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados. Tente ajustar os filtros na barra lateral.")
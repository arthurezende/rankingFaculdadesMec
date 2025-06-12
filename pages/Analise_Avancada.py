# pages/Analise_Avancada.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# Configuração da página (necessária em cada página do multipage app)
st.set_page_config(layout="wide", page_title="Análise Avançada")

st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Análise Visual e Insights</h3>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("Gráficos e análises baseados nos filtros selecionados na página principal.")

# Verifica se o dataframe filtrado existe no session_state
if 'df_filtrada' in st.session_state and not st.session_state.df_filtrada.empty:
    df_filtrada = st.session_state.df_filtrada
    
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Distribuição de Cursos por Estado")
        cursos_por_uf = df_filtrada['SG_UF'].value_counts().sort_values(ascending=False)
        st.bar_chart(cursos_por_uf)

    with col_graf2:
        st.subheader("Distribuição por Área de Conhecimento")
        cursos_por_area = df_filtrada['NO_CINE_AREA_ESPECIFICA'].value_counts().head(15)
        st.bar_chart(cursos_por_area)

    st.subheader("Análise de Concorrência (Candidato/Vaga)")
    st.markdown("Esta tabela mostra a relação entre o número de inscritos e o número de vagas totais. Disponível apenas para cursos presenciais com dados informados.")
    
    df_concorrencia = df_filtrada[['NO_CURSO', 'NO_IES', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']].copy()
    df_concorrencia.dropna(subset=['QT_INSCRITO_TOTAL', 'QT_VG_TOTAL'], inplace=True)
    df_concorrencia = df_concorrencia[(df_concorrencia['QT_VG_TOTAL'] > 0) & (df_concorrencia['QT_INSCRITO_TOTAL'] > 0)]
    
    if not df_concorrencia.empty:
        df_concorrencia['Candidatos por Vaga'] = (df_concorrencia['QT_INSCRITO_TOTAL'] / df_concorrencia['QT_VG_TOTAL']).round(2)
        df_concorrencia_view = df_concorrencia.sort_values(by='Candidatos por Vaga', ascending=False)
        
        gb = GridOptionsBuilder.from_dataframe(df_concorrencia_view[['NO_CURSO', 'NO_IES', 'Candidatos por Vaga', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']])
        gb.configure_column('NO_CURSO', headerName='Curso', width=350)
        gb.configure_column('NO_IES', headerName='Instituição', width=300)
        gb.configure_column('Candidatos por Vaga', width=150)
        gb.configure_column('QT_INSCRITO_TOTAL', headerName='Inscritos', width=120)
        gb.configure_column('QT_VG_TOTAL', headerName='Vagas', width=100)
        
        AgGrid(
            df_concorrencia_view,
            gridOptions=gb.build(),
            fit_columns_on_grid_load=True,
            theme='streamlit',
            key='tabela_concorrencia',
            height=400
        )
    else:
        st.warning("Não há dados de inscritos/vagas para os filtros selecionados.")
        
else:
    st.warning("Por favor, selecione filtros na página principal ('app.py') para visualizar as análises.")
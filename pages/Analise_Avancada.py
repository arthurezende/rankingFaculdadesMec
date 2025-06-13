# pages/Analise_Avancada.py
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Análise Avançada - Análise MEC")

st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Análise Visual e Insights</h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("Os gráficos abaixo são baseados nos filtros aplicados na página principal.")

# Usa o dataframe filtrado salvo no session_state
if 'df_filtrada_cursos' in st.session_state and not st.session_state.df_filtrada_cursos.empty:
    df_analise = st.session_state.df_filtrada_cursos

    st.header("Análise de Concorrência (Candidato/Vaga)")
    df_concorrencia = df_analise[['NO_CURSO', 'NO_IES', 'QT_INSCRITO_TOTAL', 'QT_VG_TOTAL']].copy()
    df_concorrencia.dropna(subset=['QT_INSCRITO_TOTAL', 'QT_VG_TOTAL'], inplace=True)
    df_concorrencia = df_concorrencia[(df_concorrencia['QT_VG_TOTAL'] > 0) & (df_concorrencia['QT_INSCRITO_TOTAL'] > 0)]
    
    if not df_concorrencia.empty:
        df_concorrencia['Candidatos por Vaga'] = (df_concorrencia['QT_INSCRITO_TOTAL'] / df_concorrencia['QT_VG_TOTAL']).round(2)
        st.dataframe(df_concorrencia.sort_values(by='Candidatos por Vaga', ascending=False), use_container_width=True)
    else:
        st.warning("Não há dados de concorrência para os filtros selecionados.")
    st.divider()

    st.header("Visão Geral dos Cursos")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 15 Cursos por Quantidade")
        st.bar_chart(df_analise['NO_CURSO'].value_counts().head(15))
    with col2:
        st.subheader("Cursos por Modalidade")
        st.bar_chart(df_analise['TP_MODALIDADE_ENSINO'].value_counts())
else:
    st.warning("Por favor, aplique filtros na página principal ('app.py') para ver as análises.")

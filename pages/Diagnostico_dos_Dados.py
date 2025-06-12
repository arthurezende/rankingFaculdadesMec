# pages/Diagnostico_dos_Dados.py

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Diagnóstico dos Dados")

# --- FUNÇÕES ---
# Usamos cache para garantir que os dados sejam carregados apenas uma vez por sessão
@st.cache_data
def carregar_dados_brutos(arquivo_csv='dados_reduzidos_100_mil_linhas.csv'):
    """Carrega o DataFrame bruto do CSV sem processamento adicional."""
    try:
        df = pd.read_csv(arquivo_csv, encoding='utf-8', low_memory=False)
        return df
    except FileNotFoundError:
        st.error(f"ERRO: Arquivo '{arquivo_csv}' não encontrado.")
        return None

# --- LAYOUT PRINCIPAL ---
st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Diagnóstico e Exploração dos Dados Brutos</h3>
    </div>
    """,
    unsafe_allow_html=True
)
st.title("Qualidade e Visão Geral da Base de Dados")
st.markdown("Esta página é uma ferramenta para desenvolvedores e analistas verificarem a integridade dos dados carregados.")

df_bruto = carregar_dados_brutos()

if df_bruto is not None:
    # --- MÉTRICAS GERAIS ---
    st.header("Estatísticas Gerais")
    
    # Cálculos
    total_linhas = len(df_bruto)
    total_colunas = len(df_bruto.columns)
    total_ies_distintas = df_bruto['CO_IES'].nunique()
    total_cursos_distintos = df_bruto['NO_CURSO'].nunique()
    total_ufs_ies = df_bruto['SG_UF_IES'].nunique()
    total_municipios_cursos = df_bruto['NO_MUNICIPIO'].nunique()

    # Exibição em colunas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Linhas (Registros)", f"{total_linhas:,}".replace(",", "."))
    col1.metric("Total de Colunas", f"{total_colunas}")
    col2.metric("Instituições (IES) Únicas", f"{total_ies_distintas:,}".replace(",", "."))
    col2.metric("Cursos (Nomes) Únicos", f"{total_cursos_distintos:,}".replace(",", "."))
    col3.metric("UFs de IES Distintas", f"{total_ufs_ies}")
    col3.metric("Municípios de Cursos Distintos", f"{total_municipios_cursos:,}".replace(",", "."))
    
    st.divider()

    # --- ANÁLISE DE DADOS FALTANTES (CAMPOS VAZIOS) ---
    st.header("Análise de Dados Faltantes (NaN / Nulos)")
    
    missing_data = df_bruto.isnull().sum()
    missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
    
    if not missing_data.empty:
        df_missing = pd.DataFrame({
            'Coluna': missing_data.index,
            'Valores Faltantes': missing_data.values,
            '% Faltante': (missing_data.values / total_linhas * 100).round(2)
        })
        
        st.dataframe(
            df_missing,
            use_container_width=True,
            column_config={
                "Coluna": st.column_config.TextColumn(width="large"),
                "Valores Faltantes": st.column_config.ProgressColumn(
                    "Valores Faltantes",
                    format="%d",
                    min_value=0,
                    max_value=int(missing_data.max())
                ),
                "% Faltante": st.column_config.ProgressColumn(
                    "% Faltante",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )
    else:
        st.success("Ótima notícia! Não foram encontrados dados faltantes na base.")
        
    st.divider()
    
    # --- TABELA COMPLETA COM DADOS BRUTOS ---
    st.header("Explorador de Dados Brutos")
    st.info("A tabela abaixo contém todos os dados carregados, com todas as colunas. Use a paginação e os filtros de coluna para explorar.")

    # Usando AgGrid para melhor performance e funcionalidade com tabelas grandes
    gb = GridOptionsBuilder.from_dataframe(df_bruto)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20) # Paginação manual
    gb.configure_default_column(resizable=True, filterable=True, sortable=True)
    
    AgGrid(
        df_bruto,
        gridOptions=gb.build(),
        height=600,
        width='100%',
        theme='streamlit',
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        key='grid_dados_brutos'
    )
else:
    st.error("Não foi possível carregar os dados para diagnóstico.")
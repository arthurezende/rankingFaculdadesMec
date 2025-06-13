# pages/Diagnostico_dos_Dados.py

import streamlit as st
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Diagnóstico dos Dados")

# --- FUNÇÕES ---
@st.cache_data
def carregar_dados_brutos(arquivo_csv='dados_reduzidos_50_mil_linhas-uf.csv'):
    """Carrega o DataFrame bruto do CSV para análise de qualidade."""
    try:
        df = pd.read_csv(arquivo_csv, encoding='utf-8', low_memory=False)
        return df
    except FileNotFoundError:
        st.error(f"ERRO: Arquivo de dados '{arquivo_csv}' não encontrado para o diagnóstico.")
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
st.markdown("Esta página é uma ferramenta para desenvolvedores e analistas verificarem a integridade e a cobertura dos dados carregados.")

df_bruto = carregar_dados_brutos()

if df_bruto is not None:
    # --- MÉTRICAS GERAIS ---
    st.header("Estatísticas Gerais da Base de Dados")
    
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
            '% Faltante': (missing_data.values / total_linhas * 100)
        })
        
        st.dataframe(
            df_missing,
            use_container_width=True,
            column_config={
                "Coluna": st.column_config.TextColumn("Coluna com Dados Faltantes", width="large"),
                "Valores Faltantes": st.column_config.ProgressColumn(
                    "Valores Faltantes",
                    help="Quantidade de linhas com valor vazio para esta coluna.",
                    format="%d",
                    min_value=0,
                    max_value=int(missing_data.max())
                ),
                "% Faltante": st.column_config.ProgressColumn(
                    "% Faltante",
                    help="Percentual de linhas com valor vazio para esta coluna.",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100
                )
            },
            hide_index=True
        )
    else:
        st.success("Ótima notícia! Não foram encontrados dados faltantes na base.")
        
    st.divider()

    # --- VISUALIZAÇÃO DE AMOSTRA DOS DADOS ---
    st.header("Amostra dos Dados Brutos")
    st.markdown("Exibindo as primeiras 20 linhas da tabela para verificação da estrutura e dos tipos de dados.")
    st.dataframe(df_bruto.head(20), use_container_width=True)

else:
    st.error("Não foi possível carregar os dados para diagnóstico.")

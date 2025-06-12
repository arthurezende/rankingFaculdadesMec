# pages/Entenda_os_Dados.py

import streamlit as st

st.set_page_config(layout="wide", page_title="Entenda os Dados")

st.markdown(
    """
    <div style='background-color: #00008B; padding: 10px; color: white; text-align: center;'>
    <h3>Entendendo os Critérios de Avaliação e os Dados</h3>
    </div>
    """,
    unsafe_allow_html=True
)

st.header("Critérios de Avaliação do MEC")
st.markdown("""
    Para auxiliar na sua escolha, a plataforma utiliza diversas métricas de qualidade do Ministério da Educação (MEC). Veja o que cada uma significa:

    - **CI (Conceito Institucional):** Nota que a instituição recebe após uma avaliação presencial de especialistas do MEC, que analisam itens como o Plano de Desenvolvimento Institucional (PDI), corpo docente, e infraestrutura. Varia de 1 a 5.
    - **CI-EaD (Conceito Institucional EaD):** Mesma avaliação do CI, mas focada especificamente na modalidade de Ensino a Distância.
    - **IGC (Índice Geral de Cursos):** É o indicador de qualidade mais completo, pois considera a média das notas dos cursos de graduação (CPC) e pós-graduação (Mestrado e Doutorado) da instituição nos últimos três anos. É a principal métrica para avaliar a qualidade geral de uma IES.
    - **CPC (Conceito Preliminar de Curso):** Avalia a qualidade dos cursos de graduação. Leva em conta o desempenho dos estudantes no ENADE, a qualidade do corpo docente (proporção de mestres e doutores), e a percepção dos alunos sobre as condições do seu processo formativo (infraestrutura, oportunidades de ampliação da formação, etc.).
    - **ENADE (Conceito ENADE):** Mede o desempenho dos estudantes concluintes dos cursos de graduação em relação aos conteúdos programáticos, habilidades e competências adquiridas em sua formação.
    - **IDD (Indicador de Diferença entre os Desempenhos):** Mede o valor que o curso agregou ao desenvolvimento do estudante, comparando seu desempenho no ENADE (ao final do curso) com seu desempenho no ENEM (no início do curso).

    **Nota:** A ausência de nota (representada por 'SC' - Sem Conceito ou campos vazios) pode significar que o curso é muito novo para ser avaliado ou que não participou do último ciclo avaliativo do ENADE.
""")

st.header("Fonte dos Dados")
st.markdown("""
    Os dados utilizados nesta plataforma são provenientes do **Censo da Educação Superior**, disponibilizados publicamente pelo **Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP)**. A base de dados foi tratada e consolidada para facilitar a exploração e a análise.
""")
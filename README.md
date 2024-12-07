# Projeto de Análise Educacional e Apoio à Escolha de Cursos

## Descrição

Este projeto visa desenvolver uma ferramenta interativa para auxiliar estudantes na escolha de instituições de ensino superior e cursos, com base em dados oficiais do INEP e do MEC. A plataforma oferece análises comparativas de avaliações institucionais, conceitos de curso e índices de qualidade para uma tomada de decisão informada.

Teste: https://rankingfaculdadesmec-appteste.streamlit.app/

## Funcionalidades

- Visualização de rankings de instituições de ensino superior
- Comparação de cursos entre diferentes instituições
- Filtros por localização, tipo de instituição e área de estudo
- Exibição de indicadores de qualidade como CI, IGC, CPC e ENADE

## Tecnologias Utilizadas

- Python
- Pandas para manipulação de dados
- Streamlit para criação da interface web
- Streamlit-AgGrid para exibição de tabelas interativas

## Como Executar

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o aplicativo: `streamlit run app.py`

## Dados Utilizados

O projeto utiliza dados públicos disponibilizados pelo INEP e MEC, incluindo:

- Microdados do Censo da Educação Superior
- Indicadores de Qualidade da Educação Superior
- Cadastro Nacional de Cursos e Instituições de Educação Superior

## Estrutura do Projeto

- `app.py`: Arquivo pri

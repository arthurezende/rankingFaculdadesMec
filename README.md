# Projeto Extensionista: Análise Educacional e Apoio à Escolha de Cursos (MEC/INEP)

## Sobre o projeto

Esta plataforma interativa foi desenvolvida como parte do Projeto Extensionista da Faculdade Exame. O objetivo é fornecer uma ferramenta de análise e consulta de dados sobre Instituições de Ensino Superior (IES) e cursos de graduação no Brasil, utilizando como base os microdados públicos do Censo da Educação Superior, disponibilizados pelo INEP (Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira).

A aplicação permite que estudantes, educadores e pesquisadores explorem o cenário da educação superior no país de forma intuitiva, aplicando filtros dinâmicos para encontrar informações sobre cursos, instituições, qualidade acadêmica e concorrência.

Teste: https://rankingfaculdadesmec-appteste.streamlit.app/

## Membros do Projeto

- Arthur D. Rezende
- Marcos Rogerio
- Tatiana Popp
- Victoria S. Muñoz

## Funcionalidades Principais

A plataforma é estruturada em múltiplas páginas para uma navegação organizada e focada:

### 1. Explorador de Cursos e Instituições (Página Principal)
A tela inicial funciona como um grande painel de exploração, onde o usuário pode:
- **Filtrar IES:** Por UF, nome da instituição e tipo de rede (Pública/Privada).
- **Filtrar Cursos:** Por município, nome específico e modalidade (Presencial/EAD).
- **Visualizar Tabelas Interativas:**
  - **Ranking de IES:** Exibe as instituições filtradas com suas principais notas de qualidade (IGC, CI).
  - **Ranking de Cursos:** Mostra os cursos que atendem aos filtros, com detalhes como notas (CPC, ENADE), grau acadêmico e modalidade.

### 2. Análise Avançada
Uma página dedicada a insights visuais e análises mais profundas sobre os dados filtrados:
- **Gráficos Dinâmicos:** Visualizações sobre a distribuição de cursos por estado, modalidade, grau acadêmico e as instituições com maior oferta de cursos.
- **Análise de Concorrência:** Uma tabela exclusiva que calcula e exibe a relação **candidato por vaga** para os cursos, permitindo identificar os mais e menos concorridos.

### 3. Diagnóstico dos Dados
Uma página técnica para a equipe do projeto e usuários avançados verificarem a integridade da base de dados:
- **Estatísticas Gerais:** Métricas quantitativas sobre o volume de dados (total de linhas, IES únicas, cursos, etc.).
- **Análise de Dados Faltantes:** Uma tabela que identifica colunas com dados nulos e o percentual de preenchimento, essencial para avaliar a qualidade e a cobertura da base.
- **Amostra dos Dados:** Exibe as primeiras 20 linhas da base de dados bruta para verificação da estrutura.

### 4. Entenda os Dados
Página informativa que serve como um guia para o usuário:
- **Dicionário de Métricas:** Explica detalhadamente o significado de cada indicador de qualidade do MEC (IGC, CPC, CI, ENADE, IDD), tornando os dados mais acessíveis.
- **Fonte dos Dados:** Contextualiza a origem e a confiabilidade das informações apresentadas.

### Funcionalidades Complementares

- Visualização de rankings de instituições de ensino superior
- Comparação de cursos entre diferentes instituições
- Filtros por localização, tipo de instituição e área de estudo
- Exibição de indicadores de qualidade como CI, IGC, CPC e ENADE

---

## Evolução do Projeto (Melhorias Implementadas)

Esta versão representa uma evolução significativa em relação ao protótipo original. As principais melhorias foram:

- **Otimização de Performance com DuckDB e Parquet:** O carregamento e a filtragem dos dados, que antes eram feitos com Pandas em um arquivo CSV, foram migrados para um sistema muito mais rápido usando o banco de dados analítico **DuckDB** e o formato de arquivo colunar **Parquet**. Isso permite que o aplicativo manipule grandes volumes de dados (100.000+ linhas) com alta velocidade e responsividade.

- **Estrutura Multipágina:** O aplicativo foi reestruturado para o modelo de múltiplas páginas do Streamlit, com uma navegação clara na barra lateral. Isso organiza o conteúdo de forma lógica (Exploração, Análise, Diagnóstico) e torna o código mais limpo e escalável.

- **Filtros Independentes por Página:** Cada página agora possui seus próprios filtros, dando ao usuário flexibilidade para realizar diferentes tipos de análise sem que uma interfira na outra.

- **Novas Visualizações e Análises:**
  - **Gráficos de Distribuição:** Foram adicionados gráficos de barras na página de Análise Avançada para visualizar a concentração de cursos por estado, modalidade, etc.
  - **Análise de Concorrência:** Foi criada uma tabela que calcula a relação candidato/vaga, uma métrica de alto valor que não existia na versão original.

- **Melhora na Usabilidade:**
  - **Filtros Avançados:** Foram adicionados novos filtros, como por **Área de Conhecimento** e **Grau Acadêmico**.
  - **Contextualização:** Uma página inteira foi dedicada a explicar as métricas do MEC, tornando a plataforma mais útil para o público geral.
  - **Correção de Bugs:** Foi corrigido um bug crítico que limitava a exibição de IES na tabela principal, garantindo que todos os dados da base sejam mostrados corretamente.

---

## Tecnologias Utilizadas

- **Linguagem:** Python
- **Framework Web:** Streamlit
- **Manipulação de Dados:** Pandas
- **Banco de Dados/Consultas:** DuckDB
- **Tabelas Interativas:** Streamlit AgGrid
- **Formato de Dados Otimizado:** Apache Parquet

---

## Como Executar

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o aplicativo: `streamlit run app.py`

---

## Dados Utilizados

O projeto utiliza dados públicos disponibilizados pelo INEP e MEC, incluindo:

- Microdados do Censo da Educação Superior
- Indicadores de Qualidade da Educação Superior
- Cadastro Nacional de Cursos e Instituições de Educação Superior

---

## Estrutura do Projeto

- `app.py`: Arquivo principal do aplicativo Streamlit
- `dados_reduzidos_50_mil_linhas-uf.csv`: Amostra do dataset do MEC combinado com informações de IES e cursos
- `requirements.txt`: Lista de dependências do projeto

---

## Contribuições

Contribuições são bem-vindas! Por favor, leia as diretrizes de contribuição antes de submeter pull requests.

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

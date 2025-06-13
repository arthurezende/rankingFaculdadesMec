# Projeto Extensionista: Análise Educacional e Apoio à Escolha de Cursos

## Sobre o projeto

Esta plataforma interativa foi desenvolvida como parte do Projeto Extensionista da Faculdade Exame. O objetivo é fornecer uma ferramenta de análise e consulta de dados sobre Instituições de Ensino Superior (IES) e cursos de graduação no Brasil, utilizando como base os microdados públicos do Censo da Educação Superior, disponibilizados pelo INEP.

A aplicação permite que estudantes, educadores e pesquisadores explorem o cenário da educação superior no país de forma intuitiva, aplicando filtros dinâmicos para encontrar informações sobre cursos, instituições e seus indicadores de qualidade.

**Acesse a aplicação:** [https://rankingfaculdadesmec-appteste.streamlit.app/](https://rankingfaculdadesmec-appteste.streamlit.app/)

## Membros

- Arthur D. Rezende
- Marcos Rogerio
- Tatiana Popp
- Victoria S. Muñoz

---

## Funcionalidades implementadas

A plataforma foi estruturada em um formato multipágina para uma navegação clara e organizada, com as seguintes seções:

### 1. Explorador de cursos e instituições (Página Principal)
O painel central da aplicação, onde o usuário pode:
- **Filtrar Instituições (IES):** Por Estado (UF), nome específico e tipo de rede (Pública ou Privada).
- **Filtrar Cursos:** Por município de oferta, nome do curso e modalidade (Presencial ou EAD).
- **Visualizar Tabelas Interativas:**
  - **Tabela de IES:** Exibe as instituições que correspondem aos filtros, com suas principais notas de qualidade (IGC, CI) e a UF de origem.
  - **Tabela de Cursos:** Mostra os cursos ofertados pelas IES filtradas, com detalhes como notas (CPC, ENADE), grau acadêmico e modalidade.

### 2. Análise Avançada
Uma página dedicada a insights visuais e análises mais profundas sobre a base de dados:
- **Filtros Independentes:** Permite explorar os dados com filtros próprios para UF, Área do Conhecimento e Tipo de Rede, sem alterar a página principal.
- **Gráficos Dinâmicos:** Visualizações sobre os cursos mais ofertados e a distribuição entre as modalidades Presencial e EAD.
- **Análise de Concorrência:** Uma tabela que calcula e exibe a relação **candidato por vaga** para os cursos, permitindo identificar os mais e menos concorridos.

### 3. Entenda os Dados
Página informativa que serve como um guia para o usuário:
- **Dicionário de Métricas:** Explica detalhadamente o significado de cada indicador de qualidade do MEC (IGC, CPC, CI, ENADE, IDD), tornando os dados mais acessíveis.
- **Fonte dos Dados:** Contextualiza a origem e a confiabilidade das informações apresentadas.

### 4. Diagnóstico dos Dados
Uma página técnica para a equipe do projeto e usuários avançados verificarem a integridade da base de dados:
- **Estatísticas Gerais:** Métricas quantitativas sobre o volume de dados (total de linhas, IES únicas, cursos, etc.).
- **Análise de Dados Faltantes:** Uma tabela que identifica colunas com dados nulos e o percentual de preenchimento.
- **Amostra dos Dados:** Exibe as primeiras 20 linhas da base de dados bruta para verificação da estrutura.

---

## 🚀 Evolução do projeto (melhorias implementadas)

Esta versão representa uma evolução significativa em relação ao protótipo original. As principais melhorias foram:

- **Estrutura Multipágina Profissional:** O aplicativo foi reestruturado para o modelo de múltiplas páginas nativo do Streamlit. Isso organiza o conteúdo de forma lógica, melhora a experiência do usuário e torna o código mais limpo e escalável.

- **Lógica de Filtragem Robusta:** Foi implementada uma lógica de filtragem em duas etapas na página principal, corrigindo um bug que limitava a exibição das instituições. Agora, os filtros de IES e de Cursos funcionam de forma interligada e correta.

- **Novas Páginas de Análise e Diagnóstico:** Foram criadas do zero as páginas "Análise Avançada" e "Diagnóstico dos Dados", que não existiam na versão inicial. Elas agregam valor ao permitir:
  - Visualizações gráficas sobre os dados.
  - Análise inédita da concorrência (relação candidato/vaga).
  - Verificação da qualidade e integridade da base de dados.

- **Usabilidade e Contexto Aprimorados:**
  - A página "Entenda os Dados" foi criada para contextualizar as métricas do MEC, atendendo a uma solicitação direta da equipe.
  - Os filtros foram reorganizados para uma experiência mais intuitiva.

- **Estabilidade do Ambiente:** Após testes com otimizações mais complexas que se mostraram instáveis no ambiente de deploy, o projeto foi consolidado utilizando **Pandas** e o sistema de cache do Streamlit, garantindo estabilidade e performance adequada para o volume de dados atual (50 mil linhas).

---

## Tecnologias Utilizadas

- **Linguagem:** Python
- **Framework Web:** Streamlit
- **Manipulação de Dados:** Pandas
- **Tabelas Interativas:** Streamlit AgGrid

---

## Como Executar Localmente

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/arthurezende/rankingFaculdadesMec.git
    cd rankingFaculdadesMec
    ```
2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Execute o aplicativo:**
    ```bash
    streamlit run app.py
    ```

---

## Estrutura do Projeto

-   `app.py`: Arquivo principal da aplicação (página "Explorador").
-   `pages/`: Diretório contendo os scripts das outras páginas do aplicativo.
-   `dados_reduzidos_50_mil_linhas-uf.csv`: Amostra do dataset utilizado.
-   `requirements.txt`: Lista de dependências Python do projeto.

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

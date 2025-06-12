import pandas as pd

# Nome do arquivo CSV de entrada que você quer usar
ARQUIVO_CSV = 'dados_reduzidos_100_mil_linhas.csv'
# Nome do arquivo Parquet que será gerado
ARQUIVO_PARQUET = 'dados_mec.parquet'

print(f"Iniciando a conversão de '{ARQUIVO_CSV}' para Parquet...")

try:
    # Carrega o dataframe
    df = pd.read_csv(ARQUIVO_CSV, encoding='utf-8', low_memory=False)

    # Salva como Parquet. A engine 'pyarrow' é recomendada.
    df.to_parquet(ARQUIVO_PARQUET, engine='pyarrow', compression='snappy')

    print(f"Arquivo '{ARQUIVO_PARQUET}' criado com sucesso a partir de {len(df)} linhas!")

except FileNotFoundError:
    print(f"ERRO: O arquivo de origem '{ARQUIVO_CSV}' não foi encontrado. Verifique o nome e a localização do arquivo.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")

# Ferramentas importadas
import argparse
import os
import sys

from dotenv import load_dotenv


def carregar_chave_api() -> str:
    """Le a chave da API do arquivo .env e encerra o programa se nao existir."""
    load_dotenv()

    chave = os.getenv("FOOTBALL_DATA_TOKEN")
    if not chave:
        print("Erro: FOOTBALL_DATA_TOKEN nao encontrada. Verifique o arquivo .env.")
        # Encerra com codigo 1 para que automacoes detectem a falha.
        sys.exit(1)

    # Nunca imprimir o valor da chave: prints viram screenshots e logs.
    print("Chave de API encontrada.")
    return chave


def montar_parser() -> argparse.ArgumentParser:
    """Monta as opcoes que o programa aceita na linha de comando."""
    parser = argparse.ArgumentParser(
        prog="verdao-ops",
        description="Central de dados do Palmeiras no Brasileirao.",
    )
    parser.add_argument("--proximos", action="store_true", help="Mostra os proximos jogos")
    parser.add_argument("--resultados", action="store_true", help="Mostra os ultimos resultados")
    parser.add_argument("--tabela", action="store_true", help="Mostra a tabela de classificacao")
    parser.add_argument("--relatorio", action="store_true", help="Gera relatorio em HTML")
    return parser


def main() -> None:
    """Orquestra o programa: le os argumentos e carrega a chave."""
    parser = montar_parser()
    args = parser.parse_args()

    carregar_chave_api()

    if not any([args.proximos, args.resultados, args.tabela, args.relatorio]):
        parser.print_help()


# So executa quando este arquivo e o programa principal, nao quando importado.
if __name__ == "__main__":
    main()
import argparse
import os
import sys

from dotenv import load_dotenv


def carregar_chave_api() -> str:
    load_dotenv()
    chave = os.getenv("FOOTBALL_DATA_TOKEN")
    if not chave:
        print("Erro: FOOTBALL_DATA_TOKEN nao encontrada. Verifique o arquivo .env.")
        sys.exit(1)
    print("Chave de API encontrada.")
    return chave


def montar_parser() -> argparse.ArgumentParser:
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
    parser = montar_parser()
    args = parser.parse_args()

    carregar_chave_api()

    if not any([args.proximos, args.resultados, args.tabela, args.relatorio]):
        parser.print_help()


if __name__ == "__main__":
    main()

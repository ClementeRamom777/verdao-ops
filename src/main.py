# Ferramentas importadas
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from rich.console import Console

import api_client
import cache
import relatorio
from config import Config, ErroConfig, carregar_config
from modelos import Classificacao, Partida

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
logger = logging.getLogger(__name__)


def configurar_logging() -> None:
    """Configura o registro em arquivo: falhas ficam documentadas mesmo quando

    a tela mostra so um resumo. Nunca registra a chave de API.
    """
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / "verdao_ops.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )


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


def comando_proximos(chave: str, config: Config, console: Console) -> None:
    """Busca (com cache) e exibe os proximos jogos do time configurado."""
    dados = cache.obter_dados(
        "proximos",
        config.cache_minutos,
        lambda: api_client.buscar_partidas_time(
            chave, config.time_id, status="SCHEDULED", limite=config.proximos_jogos
        ),
        console,
    )
    if dados is None:
        return

    partidas = [Partida.da_api(item, config.fuso) for item in dados.get("matches", [])]
    partidas.sort(key=lambda partida: partida.data_hora)
    relatorio.exibir_partidas(console, partidas, "Proximos jogos")


def comando_resultados(chave: str, config: Config, console: Console) -> None:
    """Busca (com cache) e exibe os ultimos resultados do time configurado."""
    dados = cache.obter_dados(
        "resultados",
        config.cache_minutos,
        lambda: api_client.buscar_partidas_time(
            chave, config.time_id, status="FINISHED", limite=config.ultimos_jogos
        ),
        console,
    )
    if dados is None:
        return

    partidas = [Partida.da_api(item, config.fuso) for item in dados.get("matches", [])]
    partidas.sort(key=lambda partida: partida.data_hora, reverse=True)
    relatorio.exibir_partidas(console, partidas, "Ultimos resultados")


def comando_tabela(chave: str, config: Config, console: Console) -> None:
    """Busca (com cache) e exibe a tabela de classificacao, com o time destacado."""
    dados = cache.obter_dados(
        "tabela",
        config.cache_minutos,
        lambda: api_client.buscar_classificacao(chave, config.competicao),
        console,
    )
    if dados is None:
        return

    grupos = dados.get("standings", [])
    grupo_geral = next((grupo for grupo in grupos if grupo.get("type") == "TOTAL"), None)
    if grupo_geral is None:
        console.print("[yellow]Classificacao indisponivel na resposta da API.[/yellow]")
        return

    classificacoes = [Classificacao.da_api(item) for item in grupo_geral.get("table", [])]
    relatorio.exibir_classificacao(console, classificacoes, config.time_id)


def comando_relatorio(chave: str, config: Config, console: Console) -> None:
    """Gera relatorio.html com proximos jogos, resultados e classificacao."""
    dados_proximos = cache.obter_dados(
        "proximos",
        config.cache_minutos,
        lambda: api_client.buscar_partidas_time(
            chave, config.time_id, status="SCHEDULED", limite=config.proximos_jogos
        ),
        console,
    )
    dados_resultados = cache.obter_dados(
        "resultados",
        config.cache_minutos,
        lambda: api_client.buscar_partidas_time(
            chave, config.time_id, status="FINISHED", limite=config.ultimos_jogos
        ),
        console,
    )
    dados_tabela = cache.obter_dados(
        "tabela",
        config.cache_minutos,
        lambda: api_client.buscar_classificacao(chave, config.competicao),
        console,
    )

    proximos: list[Partida] = []
    if dados_proximos is not None:
        proximos = sorted(
            (Partida.da_api(item, config.fuso) for item in dados_proximos.get("matches", [])),
            key=lambda partida: partida.data_hora,
        )

    resultados: list[Partida] = []
    if dados_resultados is not None:
        resultados = sorted(
            (Partida.da_api(item, config.fuso) for item in dados_resultados.get("matches", [])),
            key=lambda partida: partida.data_hora,
            reverse=True,
        )

    classificacoes: list[Classificacao] = []
    if dados_tabela is not None:
        grupo_geral = next((g for g in dados_tabela.get("standings", []) if g.get("type") == "TOTAL"), None)
        if grupo_geral is not None:
            classificacoes = [Classificacao.da_api(item) for item in grupo_geral.get("table", [])]

    if not proximos and not resultados and not classificacoes:
        console.print("[red]Sem dados disponiveis (API fora do ar e sem cache). Relatorio nao foi gerado.[/red]")
        logger.error("Relatorio nao gerado: nenhuma fonte de dados disponivel (API e cache falharam).")
        return

    gerado_em = datetime.now(ZoneInfo(config.fuso)).strftime("%d/%m/%Y %H:%M")
    caminho_saida = Path(__file__).resolve().parent.parent / "relatorio.html"
    caminho_final = relatorio.gerar_html(
        proximos, resultados, classificacoes, config.time_id, gerado_em, caminho_saida
    )

    console.print(f"[green]Relatorio gerado em: {caminho_final}[/green]")
    logger.info("Relatorio HTML gerado em %s", caminho_final)


def main() -> None:
    """Orquestra o programa: le os argumentos, carrega chave/config e despacha comandos."""
    configurar_logging()

    parser = montar_parser()
    args = parser.parse_args()

    chave = carregar_chave_api()

    try:
        config = carregar_config()
    except ErroConfig as erro:
        print(f"Erro de configuracao: {erro}")
        logger.error("Falha ao carregar config.yaml: %s", erro)
        sys.exit(1)

    if not any([args.proximos, args.resultados, args.tabela, args.relatorio]):
        parser.print_help()
        return

    console = Console()

    if args.proximos:
        comando_proximos(chave, config, console)
    if args.resultados:
        comando_resultados(chave, config, console)
    if args.tabela:
        comando_tabela(chave, config, console)
    if args.relatorio:
        comando_relatorio(chave, config, console)


# So executa quando este arquivo e o programa principal, nao quando importado.
if __name__ == "__main__":
    main()
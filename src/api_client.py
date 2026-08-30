import logging
import os
import sys

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.football-data.org/v4"
TIMEOUT_SEGUNDOS = 10

logger = logging.getLogger(__name__)


class ErroAutenticacao(Exception):
    pass


class ErroRede(Exception):
    pass


class ErroApi(Exception):
    pass


def _fazer_requisicao(url: str, chave: str, parametros: dict | None = None) -> dict:
    """Faz um GET autenticado na API e traduz falhas em excecoes claras.

    Centraliza o tratamento de erro para que todo endpoint (times, partidas,
    classificacao) reaja da mesma forma a queda de rede, timeout ou erro HTTP.
    """
    headers = {"X-Auth-Token": chave}
    logger.info("GET %s parametros=%s", url, parametros)

    try:
        resposta = requests.get(url, headers=headers, params=parametros, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.ConnectionError as erro:
        logger.error("Falha de conexao ao chamar %s: %s", url, erro)
        raise ErroRede("Sem conexao com a API. Verifique sua internet.") from erro
    except requests.exceptions.Timeout as erro:
        logger.error("Timeout ao chamar %s: %s", url, erro)
        raise ErroRede("A API demorou demais para responder.") from erro

    if resposta.status_code == 200:
        return resposta.json()

    mensagem = ""
    try:
        mensagem = resposta.json().get("message", "")
    except ValueError:
        pass

    if resposta.status_code in (400, 401, 403) and "token" in mensagem.lower():
        logger.error("Erro de autenticacao (status %s) em %s", resposta.status_code, url)
        raise ErroAutenticacao(mensagem or "Chave de API invalida ou ausente.")

    logger.error("A API respondeu status %s em %s: %s", resposta.status_code, url, resposta.text)
    raise ErroApi(f"A API respondeu com erro (status {resposta.status_code}): {resposta.text}")


def buscar_times_competicao(chave: str, competicao: str = "BSA") -> dict:
    url = f"{BASE_URL}/competitions/{competicao}/teams"
    return _fazer_requisicao(url, chave)


def buscar_partidas_time(
    chave: str,
    time_id: int,
    status: str | None = None,
    limite: int | None = None,
) -> dict:
    """Busca partidas de um time. `status` filtra (ex: 'SCHEDULED', 'FINISHED')."""
    url = f"{BASE_URL}/teams/{time_id}/matches"
    parametros = {}
    if status:
        parametros["status"] = status
    if limite:
        parametros["limit"] = limite
    return _fazer_requisicao(url, chave, parametros)


def buscar_classificacao(chave: str, competicao: str = "BSA") -> dict:
    """Busca a tabela de classificacao (standings) de uma competicao."""
    url = f"{BASE_URL}/competitions/{competicao}/standings"
    return _fazer_requisicao(url, chave)


def encontrar_time(times: list, nome: str) -> dict | None:
    for time in times:
        if nome.lower() in time.get("name", "").lower():
            return time
    return None


def main() -> None:
    load_dotenv()
    chave = os.getenv("FOOTBALL_DATA_TOKEN")
    if not chave:
        print("Erro: FOOTBALL_DATA_TOKEN nao encontrada. Verifique o arquivo .env.")
        sys.exit(1)

    try:
        dados = buscar_times_competicao(chave)
    except ErroAutenticacao as erro:
        print(f"Erro de autenticacao: {erro}")
        sys.exit(1)
    except ErroRede as erro:
        print(f"Erro de rede: {erro}")
        sys.exit(1)
    except ErroApi as erro:
        print(f"Erro da API: {erro}")
        sys.exit(1)

    palmeiras = encontrar_time(dados.get("teams", []), "Palmeiras")
    if palmeiras is None:
        print("Palmeiras nao encontrado na resposta da API.")
        sys.exit(1)

    print("Time encontrado (resposta crua):")
    print(palmeiras)


if __name__ == "__main__":
    main()

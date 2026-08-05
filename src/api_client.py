import os
import sys

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.football-data.org/v4"
TIMEOUT_SEGUNDOS = 10


class ErroAutenticacao(Exception):
    pass


class ErroRede(Exception):
    pass


class ErroApi(Exception):
    pass


def buscar_times_competicao(chave: str, competicao: str = "BSA") -> dict:
    url = f"{BASE_URL}/competitions/{competicao}/teams"
    headers = {"X-Auth-Token": chave}

    try:
        resposta = requests.get(url, headers=headers, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.ConnectionError as erro:
        raise ErroRede("Sem conexao com a API. Verifique sua internet.") from erro
    except requests.exceptions.Timeout as erro:
        raise ErroRede("A API demorou demais para responder.") from erro

    if resposta.status_code == 200:
        return resposta.json()

    mensagem = ""
    try:
        mensagem = resposta.json().get("message", "")
    except ValueError:
        pass

    if resposta.status_code in (400, 401, 403) and "token" in mensagem.lower():
        raise ErroAutenticacao(mensagem or "Chave de API invalida ou ausente.")

    raise ErroApi(f"A API respondeu com erro (status {resposta.status_code}): {resposta.text}")

    return resposta.json()


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

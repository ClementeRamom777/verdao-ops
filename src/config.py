"""Leitura e validacao do config.yaml: preferencias ficam fora do codigo."""

from dataclasses import dataclass
from pathlib import Path

import yaml

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "config.yaml"

CHAVES_OBRIGATORIAS = (
    "time_id",
    "competicao",
    "proximos_jogos",
    "ultimos_jogos",
    "cache_minutos",
    "fuso",
)


class ErroConfig(Exception):
    """Erro ao ler ou validar o config.yaml."""


@dataclass
class Config:
    time_id: int
    competicao: str
    proximos_jogos: int
    ultimos_jogos: int
    cache_minutos: int
    fuso: str


def carregar_config(caminho: Path | str = CAMINHO_PADRAO) -> Config:
    """Le o config.yaml e devolve um objeto Config validado.

    Levanta ErroConfig com mensagem clara se o arquivo nao existir,
    estiver mal formado ou faltar alguma chave obrigatoria.
    """
    caminho = Path(caminho)

    if not caminho.exists():
        raise ErroConfig(f"Arquivo de configuracao nao encontrado: {caminho}")

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = yaml.safe_load(arquivo)
    except yaml.YAMLError as erro:
        raise ErroConfig(f"config.yaml mal formado: {erro}") from erro

    if not isinstance(dados, dict):
        raise ErroConfig("config.yaml vazio ou em formato invalido.")

    faltando = [chave for chave in CHAVES_OBRIGATORIAS if chave not in dados]
    if faltando:
        raise ErroConfig(f"config.yaml esta faltando as chaves: {', '.join(faltando)}")

    try:
        return Config(
            time_id=int(dados["time_id"]),
            competicao=str(dados["competicao"]),
            proximos_jogos=int(dados["proximos_jogos"]),
            ultimos_jogos=int(dados["ultimos_jogos"]),
            cache_minutos=int(dados["cache_minutos"]),
            fuso=str(dados["fuso"]),
        )
    except (TypeError, ValueError) as erro:
        raise ErroConfig(f"Valor invalido no config.yaml: {erro}") from erro

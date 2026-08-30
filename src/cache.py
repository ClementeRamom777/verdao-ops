"""Cache local em arquivo JSON: evita estourar o limite da API e da resiliencia
ao programa quando a API falha (fora do ar, limite excedido, sem internet).

Este modulo nao conhece api_client: recebe uma funcao `buscar` qualquer e so
se preocupa com "tem cache valido?", "a busca funcionou?" e "o que fazer se
nao funcionou?". Isso permite testar a logica de cache sem rede nenhuma.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

logger = logging.getLogger(__name__)


def _caminho_cache(nome_cache: str) -> Path:
    return CACHE_DIR / f"{nome_cache}.json"


def salvar(nome_cache: str, dados: Any) -> None:
    """Grava `dados` no cache, com o carimbo de tempo de agora (UTC)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conteudo = {
        "salvo_em": datetime.now(timezone.utc).isoformat(),
        "dados": dados,
    }
    with _caminho_cache(nome_cache).open("w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)


def ler(nome_cache: str) -> tuple[Any, datetime] | None:
    """Le o cache salvo. Devolve (dados, salvo_em) ou None se nao houver

    cache utilizavel (arquivo ausente ou corrompido conta como "sem cache").
    """
    caminho = _caminho_cache(nome_cache)
    if not caminho.exists():
        return None

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
        salvo_em = datetime.fromisoformat(conteudo["salvo_em"])
        return conteudo["dados"], salvo_em
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return None


def formatar_idade(idade: timedelta) -> str:
    """Converte um timedelta em texto curto para exibir ao usuario."""
    minutos_totais = int(idade.total_seconds() // 60)

    if minutos_totais < 1:
        return "menos de 1 minuto"
    if minutos_totais < 60:
        return f"{minutos_totais} min"

    horas, minutos = divmod(minutos_totais, 60)
    if horas < 24:
        return f"{horas}h{minutos:02d}min" if minutos else f"{horas}h"

    dias, horas = divmod(horas, 24)
    return f"{dias}d{horas}h" if horas else f"{dias}d"


def obter_dados(
    nome_cache: str,
    cache_minutos: int,
    buscar: Callable[[], Any],
    console: Console,
) -> Any | None:
    """Obtem dados usando cache quando valido, API quando necessario, e cache

    antigo como fallback se a API falhar. Sempre avisa na tela a origem do
    dado quando ele nao e uma resposta fresca da API.

    Devolve None apenas quando a API falha e nao ha nenhum cache disponivel.
    """
    entrada = ler(nome_cache)

    if entrada is not None:
        dados_cache, salvo_em = entrada
        idade = datetime.now(timezone.utc) - salvo_em
        if idade <= timedelta(minutes=cache_minutos):
            logger.info("Cache '%s' valido (idade %s), API nao foi chamada.", nome_cache, formatar_idade(idade))
            console.print(f"[cyan]Dado em cache (de {formatar_idade(idade)} atras).[/cyan]")
            return dados_cache

    try:
        dados_novos = buscar()
    except Exception as erro:  # a origem exata do erro nao importa aqui
        if entrada is not None:
            dados_cache, salvo_em = entrada
            idade = datetime.now(timezone.utc) - salvo_em
            logger.warning("Busca falhou para '%s' (%s). Usando cache de %s atras.", nome_cache, erro, formatar_idade(idade))
            console.print(
                f"[yellow]Aviso: nao foi possivel falar com a API ({erro}). "
                f"Mostrando cache desatualizado, de {formatar_idade(idade)} atras.[/yellow]"
            )
            return dados_cache

        logger.error("Busca falhou para '%s' (%s) e nao ha cache disponivel.", nome_cache, erro)
        console.print(f"[red]Erro: {erro}[/red]")
        console.print("[red]Nao ha cache local para usar como alternativa.[/red]")
        return None

    logger.info("Busca de '%s' bem-sucedida, cache atualizado.", nome_cache)
    salvar(nome_cache, dados_novos)
    return dados_novos

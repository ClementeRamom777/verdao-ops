"""Saida para o usuario: tabelas no terminal com rich e relatorio em HTML com Jinja2."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console
from rich.table import Table

from modelos import Classificacao, Partida

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _destacar(nome: str) -> str:
    """Deixa o nome do Palmeiras em destaque nas tabelas de partidas."""
    if "palmeiras" in nome.lower():
        return f"[bold green]{nome}[/bold green]"
    return nome


def montar_tabela_partidas(partidas: list[Partida], titulo: str) -> Table:
    """Monta uma tabela rich a partir de uma lista de Partida."""
    tabela = Table(title=titulo, header_style="bold green")
    tabela.add_column("Data/Hora (Brasilia)")
    tabela.add_column("Mandante")
    tabela.add_column("Placar", justify="center")
    tabela.add_column("Visitante")
    tabela.add_column("Rodada", justify="center")

    for partida in partidas:
        data_str = partida.data_hora.strftime("%d/%m/%Y %H:%M")
        placar = f"{partida.gols_mandante} x {partida.gols_visitante}" if partida.foi_disputada else "a definir"
        tabela.add_row(
            data_str,
            _destacar(partida.mandante),
            placar,
            _destacar(partida.visitante),
            str(partida.rodada) if partida.rodada is not None else "-",
        )

    return tabela


def exibir_partidas(console: Console, partidas: list[Partida], titulo: str) -> None:
    """Imprime a tabela de partidas no terminal, ou um aviso se a lista vier vazia."""
    if not partidas:
        console.print(f"[yellow]Nenhuma partida encontrada ({titulo}).[/yellow]")
        return
    console.print(montar_tabela_partidas(partidas, titulo))


def montar_tabela_classificacao(classificacoes: list[Classificacao], time_id_destaque: int) -> Table:
    """Monta a tabela de classificacao, com a linha de `time_id_destaque` em

    destaque (usado para realcar o Palmeiras).
    """
    tabela = Table(title="Classificacao - Brasileirao Serie A", header_style="bold green")
    tabela.add_column("Pos", justify="right")
    tabela.add_column("Time")
    tabela.add_column("Pts", justify="right")
    tabela.add_column("J", justify="right")
    tabela.add_column("V", justify="right")
    tabela.add_column("E", justify="right")
    tabela.add_column("D", justify="right")
    tabela.add_column("GP", justify="right")
    tabela.add_column("GC", justify="right")
    tabela.add_column("SG", justify="right")

    for c in classificacoes:
        estilo = "bold green" if c.time_id == time_id_destaque else None
        tabela.add_row(
            str(c.posicao),
            c.time,
            str(c.pontos),
            str(c.jogos),
            str(c.vitorias),
            str(c.empates),
            str(c.derrotas),
            str(c.gols_pro),
            str(c.gols_contra),
            str(c.saldo_gols),
            style=estilo,
        )

    return tabela


def exibir_classificacao(console: Console, classificacoes: list[Classificacao], time_id_destaque: int) -> None:
    """Imprime a tabela de classificacao, ou um aviso se ela vier vazia."""
    if not classificacoes:
        console.print("[yellow]Classificacao indisponivel.[/yellow]")
        return
    console.print(montar_tabela_classificacao(classificacoes, time_id_destaque))


def _linha_partida(partida: Partida) -> dict:
    """Formata uma Partida em campos ja prontos para o template HTML."""
    placar = f"{partida.gols_mandante} x {partida.gols_visitante}" if partida.foi_disputada else "a definir"
    return {
        "data_hora": partida.data_hora.strftime("%d/%m/%Y %H:%M"),
        "mandante": partida.mandante,
        "visitante": partida.visitante,
        "placar": placar,
        "rodada": partida.rodada if partida.rodada is not None else "-",
        "destaque_mandante": "palmeiras" in partida.mandante.lower(),
        "destaque_visitante": "palmeiras" in partida.visitante.lower(),
    }


def _linha_classificacao(classificacao: Classificacao, time_id_destaque: int) -> dict:
    """Formata uma Classificacao em campos prontos para o template HTML."""
    return {
        "posicao": classificacao.posicao,
        "time": classificacao.time,
        "pontos": classificacao.pontos,
        "jogos": classificacao.jogos,
        "vitorias": classificacao.vitorias,
        "empates": classificacao.empates,
        "derrotas": classificacao.derrotas,
        "gols_pro": classificacao.gols_pro,
        "gols_contra": classificacao.gols_contra,
        "saldo_gols": classificacao.saldo_gols,
        "destaque": classificacao.time_id == time_id_destaque,
    }


def gerar_html(
    proximos: list[Partida],
    resultados: list[Partida],
    classificacoes: list[Classificacao],
    time_id_destaque: int,
    gerado_em: str,
    caminho_saida: Path,
) -> Path:
    """Renderiza o relatorio.html (Jinja2) com os dados fornecidos e grava em disco.

    Devolve o caminho absoluto do arquivo gerado.
    """
    ambiente = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = ambiente.get_template("relatorio.html")

    html = template.render(
        gerado_em=gerado_em,
        proximos=[_linha_partida(p) for p in proximos],
        resultados=[_linha_partida(p) for p in resultados],
        classificacao=[_linha_classificacao(c, time_id_destaque) for c in classificacoes],
    )

    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(html, encoding="utf-8")
    return caminho_saida.resolve()

"""Modelos de dados: formas estruturadas do que a API devolve como JSON cru."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass
class Partida:
    """Uma partida do time acompanhado, ja convertida para o fuso configurado."""

    id: int
    competicao: str
    rodada: int | None
    status: str
    data_hora: datetime
    mandante: str
    visitante: str
    gols_mandante: int | None
    gols_visitante: int | None

    @classmethod
    def da_api(cls, dado: dict, fuso: str) -> "Partida":
        """Constroi uma Partida a partir do dicionario cru retornado pela API.

        `dado` segue o formato de `/v4/teams/{id}/matches` (um item de "matches").
        `fuso` e o nome IANA do fuso horario para exibicao, ex: "America/Sao_Paulo".
        """
        utc_date = dado["utcDate"].replace("Z", "+00:00")
        data_hora_utc = datetime.fromisoformat(utc_date)
        data_hora_local = data_hora_utc.astimezone(ZoneInfo(fuso))

        placar = dado.get("score", {}).get("fullTime", {})

        return cls(
            id=dado["id"],
            competicao=dado.get("competition", {}).get("name", ""),
            rodada=dado.get("matchday"),
            status=dado.get("status", ""),
            data_hora=data_hora_local,
            mandante=dado.get("homeTeam", {}).get("shortName") or dado.get("homeTeam", {}).get("name", ""),
            visitante=dado.get("awayTeam", {}).get("shortName") or dado.get("awayTeam", {}).get("name", ""),
            gols_mandante=placar.get("home"),
            gols_visitante=placar.get("away"),
        )

    @property
    def foi_disputada(self) -> bool:
        """True quando a partida ja tem placar final registrado."""
        return self.gols_mandante is not None and self.gols_visitante is not None


@dataclass
class Classificacao:
    """Uma linha da tabela de classificacao de uma competicao."""

    posicao: int
    time_id: int
    time: str
    jogos: int
    vitorias: int
    empates: int
    derrotas: int
    pontos: int
    gols_pro: int
    gols_contra: int
    saldo_gols: int

    @classmethod
    def da_api(cls, dado: dict) -> "Classificacao":
        """Constroi uma Classificacao a partir de um item de "table" em

        `/v4/competitions/{competicao}/standings`.
        """
        time = dado.get("team", {})
        return cls(
            posicao=dado["position"],
            time_id=time.get("id", 0),
            time=time.get("shortName") or time.get("name", ""),
            jogos=dado.get("playedGames", 0),
            vitorias=dado.get("won", 0),
            empates=dado.get("draw", 0),
            derrotas=dado.get("lost", 0),
            pontos=dado.get("points", 0),
            gols_pro=dado.get("goalsFor", 0),
            gols_contra=dado.get("goalsAgainst", 0),
            saldo_gols=dado.get("goalDifference", 0),
        )

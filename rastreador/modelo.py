"""Modelo de dominio do rastreador.

Define a entidade `Tarefa` e os status validos. A conversao de e para
dicionario mantem as chaves no formato exigido pelo enunciado do desafio
(`id`, `description`, `status`, `createdAt`, `updatedAt`), enquanto o codigo
Python usa nomes em portugues.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


class Status:
    """Status possiveis de uma tarefa."""

    A_FAZER = "todo"
    EM_ANDAMENTO = "in-progress"
    CONCLUIDA = "done"


STATUS_VALIDOS = (Status.A_FAZER, Status.EM_ANDAMENTO, Status.CONCLUIDA)

ROTULOS_STATUS = {
    Status.A_FAZER: "a fazer",
    Status.EM_ANDAMENTO: "em andamento",
    Status.CONCLUIDA: "concluida",
}


def agora() -> str:
    """Devolve o instante atual em UTC no formato ISO 8601 (segundos)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Tarefa:
    """Representa uma tarefa persistida no arquivo JSON."""

    identificador: int
    descricao: str
    status: str = Status.A_FAZER
    criada_em: str = ""
    atualizada_em: str = ""

    def __post_init__(self) -> None:
        instante = agora()
        if not self.criada_em:
            self.criada_em = instante
        if not self.atualizada_em:
            self.atualizada_em = self.criada_em

    @property
    def rotulo_status(self) -> str:
        """Nome do status em portugues, usado na exibicao."""
        return ROTULOS_STATUS.get(self.status, self.status)

    def para_dicionario(self) -> Dict[str, Any]:
        """Serializa a tarefa usando as chaves definidas no desafio."""
        return {
            "id": self.identificador,
            "description": self.descricao,
            "status": self.status,
            "createdAt": self.criada_em,
            "updatedAt": self.atualizada_em,
        }

    @classmethod
    def de_dicionario(cls, dados: Dict[str, Any]) -> "Tarefa":
        """Reconstroi uma tarefa a partir do dicionario lido do JSON."""
        return cls(
            identificador=int(dados["id"]),
            descricao=str(dados["description"]),
            status=str(dados.get("status", Status.A_FAZER)),
            criada_em=str(dados.get("createdAt", "")),
            atualizada_em=str(dados.get("updatedAt", "")),
        )

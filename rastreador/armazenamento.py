"""Persistencia das tarefas em um arquivo JSON.

O repositorio cria o arquivo automaticamente quando ele nao existe e grava as
alteracoes de forma atomica: o conteudo e escrito em um arquivo temporario que
depois substitui o original, evitando um JSON corrompido caso o processo seja
interrompido no meio da escrita.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import List

from rastreador.modelo import Tarefa

ARQUIVO_PADRAO = "tarefas.json"


class ErroDeArmazenamento(Exception):
    """Falha ao ler ou gravar o arquivo de tarefas."""


class RepositorioJson:
    """Le e grava a lista de tarefas em um arquivo JSON local."""

    def __init__(self, caminho: str | os.PathLike[str] = ARQUIVO_PADRAO) -> None:
        self.caminho = Path(caminho)

    def carregar(self) -> List[Tarefa]:
        """Devolve todas as tarefas do arquivo, ou uma lista vazia."""
        if not self.caminho.exists():
            return []

        try:
            conteudo = self.caminho.read_text(encoding="utf-8").strip()
        except OSError as erro:
            raise ErroDeArmazenamento(
                f"nao foi possivel ler '{self.caminho}': {erro}"
            ) from erro

        if not conteudo:
            return []

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError as erro:
            raise ErroDeArmazenamento(
                f"o arquivo '{self.caminho}' nao contem um JSON valido: {erro}"
            ) from erro

        if not isinstance(dados, list):
            raise ErroDeArmazenamento(
                f"o arquivo '{self.caminho}' deveria conter uma lista de tarefas"
            )

        try:
            return [Tarefa.de_dicionario(item) for item in dados]
        except (KeyError, TypeError, ValueError) as erro:
            raise ErroDeArmazenamento(
                f"registro invalido em '{self.caminho}': {erro}"
            ) from erro

    def salvar(self, tarefas: List[Tarefa]) -> None:
        """Grava a lista completa de tarefas, substituindo o conteudo atual."""
        dados = [tarefa.para_dicionario() for tarefa in tarefas]
        destino = self.caminho.resolve()
        diretorio = destino.parent
        diretorio.mkdir(parents=True, exist_ok=True)

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=diretorio,
                prefix=".tarefas-",
                suffix=".tmp",
                delete=False,
            ) as temporario:
                json.dump(dados, temporario, ensure_ascii=False, indent=2)
                temporario.write("\n")
                caminho_temporario = temporario.name
            os.replace(caminho_temporario, destino)
        except OSError as erro:
            raise ErroDeArmazenamento(
                f"nao foi possivel gravar '{self.caminho}': {erro}"
            ) from erro

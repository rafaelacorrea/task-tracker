"""Regras de negocio do rastreador de tarefas.

O servico concentra as operacoes de adicionar, atualizar, remover, mudar o
status e listar tarefas. Ele nao imprime nada na tela: erros previstos viram
`ErroDeTarefa` e a camada de linha de comando decide como exibi-los.
"""

from __future__ import annotations

from typing import List, Optional

from rastreador.armazenamento import ErroDeArmazenamento, RepositorioJson
from rastreador.modelo import STATUS_VALIDOS, Status, Tarefa, agora


class ErroDeTarefa(Exception):
    """Operacao invalida solicitada pelo usuario."""


class ServicoDeTarefas:
    """Executa as operacoes sobre a colecao de tarefas."""

    def __init__(self, repositorio: Optional[RepositorioJson] = None) -> None:
        self.repositorio = repositorio or RepositorioJson()

    def _carregar(self) -> List[Tarefa]:
        try:
            return self.repositorio.carregar()
        except ErroDeArmazenamento as erro:
            raise ErroDeTarefa(str(erro)) from erro

    def _salvar(self, tarefas: List[Tarefa]) -> None:
        try:
            self.repositorio.salvar(tarefas)
        except ErroDeArmazenamento as erro:
            raise ErroDeTarefa(str(erro)) from erro

    @staticmethod
    def _proximo_identificador(tarefas: List[Tarefa]) -> int:
        """Gera o proximo id a partir do maior id ja existente na lista."""
        if not tarefas:
            return 1
        return max(tarefa.identificador for tarefa in tarefas) + 1

    @staticmethod
    def _validar_descricao(descricao: str) -> str:
        texto = (descricao or "").strip()
        if not texto:
            raise ErroDeTarefa("a descricao da tarefa nao pode ficar vazia")
        return texto

    def _buscar(self, tarefas: List[Tarefa], identificador: int) -> Tarefa:
        for tarefa in tarefas:
            if tarefa.identificador == identificador:
                return tarefa
        raise ErroDeTarefa(f"nenhuma tarefa encontrada com o id {identificador}")

    def adicionar(self, descricao: str) -> Tarefa:
        """Cria uma tarefa com status 'todo' e devolve o registro criado."""
        texto = self._validar_descricao(descricao)
        tarefas = self._carregar()
        tarefa = Tarefa(
            identificador=self._proximo_identificador(tarefas),
            descricao=texto,
        )
        tarefas.append(tarefa)
        self._salvar(tarefas)
        return tarefa

    def atualizar(self, identificador: int, descricao: str) -> Tarefa:
        """Troca a descricao de uma tarefa existente."""
        texto = self._validar_descricao(descricao)
        tarefas = self._carregar()
        tarefa = self._buscar(tarefas, identificador)
        tarefa.descricao = texto
        tarefa.atualizada_em = agora()
        self._salvar(tarefas)
        return tarefa

    def remover(self, identificador: int) -> Tarefa:
        """Remove uma tarefa e devolve o registro excluido."""
        tarefas = self._carregar()
        tarefa = self._buscar(tarefas, identificador)
        tarefas = [item for item in tarefas if item.identificador != identificador]
        self._salvar(tarefas)
        return tarefa

    def mudar_status(self, identificador: int, status: str) -> Tarefa:
        """Aplica um novo status a uma tarefa existente."""
        if status not in STATUS_VALIDOS:
            validos = ", ".join(STATUS_VALIDOS)
            raise ErroDeTarefa(f"status invalido '{status}'; use um destes: {validos}")
        tarefas = self._carregar()
        tarefa = self._buscar(tarefas, identificador)
        tarefa.status = status
        tarefa.atualizada_em = agora()
        self._salvar(tarefas)
        return tarefa

    def marcar_em_andamento(self, identificador: int) -> Tarefa:
        """Atalho para mudar o status para 'in-progress'."""
        return self.mudar_status(identificador, Status.EM_ANDAMENTO)

    def marcar_concluida(self, identificador: int) -> Tarefa:
        """Atalho para mudar o status para 'done'."""
        return self.mudar_status(identificador, Status.CONCLUIDA)

    def listar(self, status: Optional[str] = None) -> List[Tarefa]:
        """Lista as tarefas, opcionalmente filtrando por status."""
        if status is not None and status not in STATUS_VALIDOS:
            validos = ", ".join(STATUS_VALIDOS)
            raise ErroDeTarefa(f"status invalido '{status}'; use um destes: {validos}")
        tarefas = self._carregar()
        if status is None:
            return tarefas
        return [tarefa for tarefa in tarefas if tarefa.status == status]

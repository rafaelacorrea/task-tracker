"""Pacote do Rastreador de Tarefas.

Expoe os componentes principais da aplicacao para uso programatico:

    from rastreador import ServicoDeTarefas, RepositorioJson

O pacote nao depende de nenhuma biblioteca externa, apenas da biblioteca
padrao do Python.
"""

from rastreador.modelo import STATUS_VALIDOS, Status, Tarefa
from rastreador.armazenamento import RepositorioJson
from rastreador.servico import ErroDeTarefa, ServicoDeTarefas

__all__ = [
    "STATUS_VALIDOS",
    "ErroDeTarefa",
    "RepositorioJson",
    "ServicoDeTarefas",
    "Status",
    "Tarefa",
]

__version__ = "1.0.0"

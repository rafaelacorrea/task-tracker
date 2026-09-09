"""Camada de linha de comando do rastreador de tarefas.

Traduz os argumentos recebidos no terminal em chamadas ao `ServicoDeTarefas` e
formata a saida em portugues. Toda a analise de argumentos usa `argparse`, da
biblioteca padrao.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from rastreador.armazenamento import ARQUIVO_PADRAO, RepositorioJson
from rastreador.modelo import STATUS_VALIDOS, Status, Tarefa
from rastreador.servico import ErroDeTarefa, ServicoDeTarefas

PROGRAMA = "task-cli"

DESCRICAO = (
    "Rastreador de tarefas em linha de comando. As tarefas ficam guardadas em "
    "um arquivo JSON no diretorio atual."
)

EXEMPLOS = """\
Exemplos de uso:
  task-cli add "Comprar mantimentos"
  task-cli update 1 "Comprar mantimentos e cozinhar o jantar"
  task-cli delete 1
  task-cli mark-in-progress 1
  task-cli mark-done 1
  task-cli list
  task-cli list todo
  task-cli list in-progress
  task-cli list done
"""


def construir_analisador() -> argparse.ArgumentParser:
    """Monta o analisador de argumentos com todos os subcomandos."""
    analisador = argparse.ArgumentParser(
        prog=PROGRAMA,
        description=DESCRICAO,
        epilog=EXEMPLOS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    analisador.add_argument(
        "--arquivo",
        default=ARQUIVO_PADRAO,
        metavar="CAMINHO",
        help=f"arquivo JSON usado para guardar as tarefas (padrao: {ARQUIVO_PADRAO})",
    )

    subcomandos = analisador.add_subparsers(dest="comando", metavar="comando")

    adicionar = subcomandos.add_parser("add", help="cria uma nova tarefa")
    adicionar.add_argument("descricao", help="texto que descreve a tarefa")

    atualizar = subcomandos.add_parser("update", help="altera a descricao de uma tarefa")
    atualizar.add_argument("id", type=int, help="identificador da tarefa")
    atualizar.add_argument("descricao", help="nova descricao da tarefa")

    remover = subcomandos.add_parser("delete", help="remove uma tarefa")
    remover.add_argument("id", type=int, help="identificador da tarefa")

    em_andamento = subcomandos.add_parser(
        "mark-in-progress", help="marca uma tarefa como em andamento"
    )
    em_andamento.add_argument("id", type=int, help="identificador da tarefa")

    concluida = subcomandos.add_parser(
        "mark-done", help="marca uma tarefa como concluida"
    )
    concluida.add_argument("id", type=int, help="identificador da tarefa")

    listar = subcomandos.add_parser("list", help="lista as tarefas")
    listar.add_argument(
        "status",
        nargs="?",
        choices=list(STATUS_VALIDOS),
        help="filtra pelo status; sem filtro, lista todas as tarefas",
    )

    return analisador


def formatar_tarefa(tarefa: Tarefa) -> str:
    """Formata uma unica tarefa em uma linha legivel."""
    return f"[{tarefa.identificador}] {tarefa.descricao} ({tarefa.rotulo_status})"


def formatar_lista(tarefas: List[Tarefa]) -> str:
    """Monta uma tabela alinhada com as tarefas informadas."""
    if not tarefas:
        return "Nenhuma tarefa encontrada."

    largura_id = max(len("ID"), *(len(str(t.identificador)) for t in tarefas))
    largura_status = max(len("STATUS"), *(len(t.rotulo_status) for t in tarefas))
    largura_descricao = max(len("DESCRICAO"), *(len(t.descricao) for t in tarefas))

    linhas = [
        f"{'ID':<{largura_id}}  {'DESCRICAO':<{largura_descricao}}  "
        f"{'STATUS':<{largura_status}}  ATUALIZADA EM",
        f"{'-' * largura_id}  {'-' * largura_descricao}  "
        f"{'-' * largura_status}  {'-' * len('ATUALIZADA EM')}",
    ]
    for tarefa in tarefas:
        linhas.append(
            f"{tarefa.identificador:<{largura_id}}  "
            f"{tarefa.descricao:<{largura_descricao}}  "
            f"{tarefa.rotulo_status:<{largura_status}}  "
            f"{tarefa.atualizada_em}"
        )
    total = "1 tarefa" if len(tarefas) == 1 else f"{len(tarefas)} tarefas"
    linhas.append("")
    linhas.append(f"Total: {total}.")
    return "\n".join(linhas)


def executar(argumentos: argparse.Namespace, servico: ServicoDeTarefas) -> str:
    """Executa o subcomando escolhido e devolve o texto a ser exibido."""
    comando = argumentos.comando

    if comando == "add":
        tarefa = servico.adicionar(argumentos.descricao)
        return f"Tarefa adicionada com sucesso (ID: {tarefa.identificador})."

    if comando == "update":
        tarefa = servico.atualizar(argumentos.id, argumentos.descricao)
        return f"Tarefa {tarefa.identificador} atualizada com sucesso."

    if comando == "delete":
        tarefa = servico.remover(argumentos.id)
        return f"Tarefa {tarefa.identificador} removida com sucesso."

    if comando == "mark-in-progress":
        tarefa = servico.marcar_em_andamento(argumentos.id)
        return f"Tarefa {tarefa.identificador} marcada como em andamento."

    if comando == "mark-done":
        tarefa = servico.marcar_concluida(argumentos.id)
        return f"Tarefa {tarefa.identificador} marcada como concluida."

    if comando == "list":
        return formatar_lista(servico.listar(argumentos.status))

    raise ErroDeTarefa(f"comando desconhecido: {comando}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Ponto de entrada da aplicacao. Devolve o codigo de saida do processo."""
    analisador = construir_analisador()
    argumentos = analisador.parse_args(argv)

    if not argumentos.comando:
        analisador.print_help()
        return 1

    servico = ServicoDeTarefas(RepositorioJson(argumentos.arquivo))

    try:
        print(executar(argumentos, servico))
    except ErroDeTarefa as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    return 0

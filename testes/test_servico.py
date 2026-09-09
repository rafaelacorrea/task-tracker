"""Testes das regras de negocio do `ServicoDeTarefas`."""

import json
import tempfile
import unittest
from pathlib import Path

from rastreador.armazenamento import RepositorioJson
from rastreador.modelo import Status
from rastreador.servico import ErroDeTarefa, ServicoDeTarefas


class TesteServicoDeTarefas(unittest.TestCase):
    """Cada teste roda sobre um arquivo JSON temporario e isolado."""

    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.diretorio.name) / "tarefas.json"
        self.servico = ServicoDeTarefas(RepositorioJson(self.arquivo))

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def test_arquivo_e_criado_na_primeira_adicao(self) -> None:
        self.assertFalse(self.arquivo.exists())
        self.servico.adicionar("Comprar mantimentos")
        self.assertTrue(self.arquivo.exists())

    def test_adicionar_gera_ids_sequenciais(self) -> None:
        primeira = self.servico.adicionar("Comprar mantimentos")
        segunda = self.servico.adicionar("Lavar a louca")
        self.assertEqual(primeira.identificador, 1)
        self.assertEqual(segunda.identificador, 2)
        self.assertEqual(primeira.status, Status.A_FAZER)

    def test_adicionar_recusa_descricao_vazia(self) -> None:
        with self.assertRaises(ErroDeTarefa):
            self.servico.adicionar("   ")

    def test_atualizar_troca_a_descricao(self) -> None:
        tarefa = self.servico.adicionar("Comprar mantimentos")
        atualizada = self.servico.atualizar(
            tarefa.identificador, "Comprar mantimentos e cozinhar o jantar"
        )
        self.assertEqual(
            atualizada.descricao, "Comprar mantimentos e cozinhar o jantar"
        )

    def test_atualizar_id_inexistente_falha(self) -> None:
        with self.assertRaises(ErroDeTarefa):
            self.servico.atualizar(99, "Qualquer coisa")

    def test_remover_apaga_apenas_a_tarefa_indicada(self) -> None:
        self.servico.adicionar("Comprar mantimentos")
        segunda = self.servico.adicionar("Lavar a louca")
        self.servico.remover(segunda.identificador)
        restantes = [t.identificador for t in self.servico.listar()]
        self.assertEqual(restantes, [1])

    def test_novo_id_nao_colide_apos_remocao_no_meio(self) -> None:
        self.servico.adicionar("Primeira")
        segunda = self.servico.adicionar("Segunda")
        self.servico.adicionar("Terceira")
        self.servico.remover(segunda.identificador)
        quarta = self.servico.adicionar("Quarta")
        identificadores = [t.identificador for t in self.servico.listar()]
        self.assertEqual(quarta.identificador, 4)
        self.assertEqual(identificadores, [1, 3, 4])

    def test_marcar_em_andamento_e_concluida(self) -> None:
        tarefa = self.servico.adicionar("Estudar Python")
        self.assertEqual(
            self.servico.marcar_em_andamento(tarefa.identificador).status,
            Status.EM_ANDAMENTO,
        )
        self.assertEqual(
            self.servico.marcar_concluida(tarefa.identificador).status,
            Status.CONCLUIDA,
        )

    def test_listar_filtra_por_status(self) -> None:
        a_fazer = self.servico.adicionar("Comprar mantimentos")
        andamento = self.servico.adicionar("Estudar Python")
        concluida = self.servico.adicionar("Lavar a louca")
        self.servico.marcar_em_andamento(andamento.identificador)
        self.servico.marcar_concluida(concluida.identificador)

        self.assertEqual(
            [t.identificador for t in self.servico.listar(Status.A_FAZER)],
            [a_fazer.identificador],
        )
        self.assertEqual(
            [t.identificador for t in self.servico.listar(Status.EM_ANDAMENTO)],
            [andamento.identificador],
        )
        self.assertEqual(
            [t.identificador for t in self.servico.listar(Status.CONCLUIDA)],
            [concluida.identificador],
        )
        self.assertEqual(len(self.servico.listar()), 3)

    def test_listar_com_status_invalido_falha(self) -> None:
        with self.assertRaises(ErroDeTarefa):
            self.servico.listar("arquivada")

    def test_arquivo_json_usa_as_chaves_do_desafio(self) -> None:
        self.servico.adicionar("Comprar mantimentos")
        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(dados[0]),
            ["createdAt", "description", "id", "status", "updatedAt"],
        )

    def test_json_invalido_gera_erro_tratado(self) -> None:
        self.arquivo.write_text("{ isso nao e json", encoding="utf-8")
        with self.assertRaises(ErroDeTarefa):
            self.servico.listar()


if __name__ == "__main__":
    unittest.main()

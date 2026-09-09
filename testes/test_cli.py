"""Testes da camada de linha de comando."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from rastreador.cli import main


class TesteCli(unittest.TestCase):
    """Executa o `main` como o terminal faria e inspeciona a saida."""

    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.arquivo = str(Path(self.diretorio.name) / "tarefas.json")

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def rodar(self, *argumentos: str):
        """Roda um comando e devolve (codigo, saida padrao, saida de erro)."""
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(["--arquivo", self.arquivo, *argumentos])
        return codigo, saida.getvalue(), erro.getvalue()

    def test_fluxo_completo(self) -> None:
        codigo, saida, _ = self.rodar("add", "Comprar mantimentos")
        self.assertEqual(codigo, 0)
        self.assertIn("ID: 1", saida)

        self.rodar("add", "Estudar Python")
        self.rodar("mark-in-progress", "2")

        codigo, saida, _ = self.rodar("list", "in-progress")
        self.assertEqual(codigo, 0)
        self.assertIn("Estudar Python", saida)
        self.assertNotIn("Comprar mantimentos", saida)

        codigo, saida, _ = self.rodar("delete", "1")
        self.assertEqual(codigo, 0)
        self.assertIn("removida", saida)

    def test_lista_vazia(self) -> None:
        codigo, saida, _ = self.rodar("list")
        self.assertEqual(codigo, 0)
        self.assertIn("Nenhuma tarefa encontrada.", saida)

    def test_id_inexistente_retorna_codigo_de_erro(self) -> None:
        codigo, _, erro = self.rodar("mark-done", "42")
        self.assertEqual(codigo, 1)
        self.assertIn("nenhuma tarefa encontrada", erro)

    def test_sem_comando_mostra_ajuda(self) -> None:
        codigo, saida, _ = self.rodar()
        self.assertEqual(codigo, 1)
        self.assertIn("Exemplos de uso", saida)


if __name__ == "__main__":
    unittest.main()

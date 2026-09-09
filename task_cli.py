#!/usr/bin/env python3
"""Executavel do rastreador de tarefas.

Uso:
    python task_cli.py add "Comprar mantimentos"

Consulte o README.md para a lista completa de comandos.
"""

import sys

from rastreador.cli import main

if __name__ == "__main__":
    sys.exit(main())

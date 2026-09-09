#!/usr/bin/env python3
"""Gera a demonstracao animada usada no README.

O script executa os comandos reais do rastreador em um diretorio temporario,
captura a saida de verdade e desenha um terminal quadro a quadro com efeito de
digitacao. O resultado e gravado em `docs/demonstracao.gif`.

Uso:
    python scripts/gerar_gif.py [caminho/de/saida.gif]

Requisitos: Pillow (apenas para gerar o GIF; a aplicacao em si nao depende
de nenhuma biblioteca externa).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SAIDA_PADRAO = RAIZ / "docs" / "demonstracao.gif"

# Dimensoes e cores da janela desenhada.
LARGURA, ALTURA = 940, 600
MARGEM_X, MARGEM_Y = 24, 58
ALTURA_LINHA = 22
LINHAS_VISIVEIS = (ALTURA - MARGEM_Y - 16) // ALTURA_LINHA

FUNDO = (13, 17, 23)
BARRA = (22, 27, 34)
BORDA = (48, 54, 61)
TITULO = (139, 148, 158)
TEXTO = (201, 209, 217)
PROMPT = (126, 231, 135)
COMANDO = (233, 233, 233)
SUCESSO = (126, 231, 135)
DESTAQUE = (121, 192, 255)
ERRO = (255, 123, 114)
CURSOR = (201, 209, 217)
SEMAFORO = ((255, 95, 86), (255, 189, 46), (39, 201, 63))

PROMPT_TEXTO = "PS C:\\tarefas> "

# Ritmo da animacao, em milissegundos por quadro.
MS_DIGITACAO = 90
# Caracteres revelados por quadro: mais de um por vez deixa o GIF bem menor.
PASSO_DIGITACAO = 3
MS_ANTES_DA_SAIDA = 320
MS_DEPOIS_DA_SAIDA = 1100
MS_FINAL = 2600

CAMINHOS_DE_FONTE = (
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\cour.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
)

Linha = Tuple[str, Tuple[int, int, int]]


def carregar_fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    """Devolve a primeira fonte monoespacada disponivel no sistema."""
    for caminho in CAMINHOS_DE_FONTE:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    raise SystemExit("nenhuma fonte monoespacada encontrada no sistema")


FONTE = carregar_fonte(16)
FONTE_TITULO = carregar_fonte(14)


def rodar(arquivo: Path, argumentos: Sequence[str]) -> List[str]:
    """Executa o CLI de verdade e devolve as linhas de saida."""
    processo = subprocess.run(
        [sys.executable, str(RAIZ / "task_cli.py"), "--arquivo", str(arquivo), *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    bruto = (processo.stdout + processo.stderr).replace("\r\n", "\n")
    return bruto.rstrip("\n").split("\n")


def colorir(linha: str) -> Linha:
    """Escolhe a cor de uma linha de saida conforme o seu conteudo."""
    if linha.startswith("Erro:"):
        return linha, ERRO
    if linha.startswith("Tarefa "):
        return linha, SUCESSO
    if linha.startswith("ID ") or set(linha.strip()) <= {"-", " "} and linha.strip():
        return linha, DESTAQUE
    if linha.startswith("Total:") or linha.startswith("Nenhuma"):
        return linha, TITULO
    return linha, TEXTO


def moldura(linhas: List[Linha], digitando: str = "", cursor: bool = True) -> Image.Image:
    """Desenha um quadro do terminal com o historico e a linha em digitacao."""
    imagem = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    desenho = ImageDraw.Draw(imagem)

    desenho.rectangle([0, 0, LARGURA - 1, 34], fill=BARRA)
    desenho.line([0, 35, LARGURA, 35], fill=BORDA)
    for indice, cor in enumerate(SEMAFORO):
        centro = 22 + indice * 20
        desenho.ellipse([centro - 6, 11, centro + 6, 23], fill=cor)
    desenho.text(
        (LARGURA // 2, 17),
        "Rastreador de Tarefas - Python",
        font=FONTE_TITULO,
        fill=TITULO,
        anchor="mm",
    )

    visiveis = linhas[-LINHAS_VISIVEIS:] if digitando == "" else linhas[-(LINHAS_VISIVEIS - 1):]
    y = MARGEM_Y
    for texto, cor in visiveis:
        desenho.text((MARGEM_X, y), texto, font=FONTE, fill=cor)
        y += ALTURA_LINHA

    if digitando != "" or cursor:
        desenho.text((MARGEM_X, y), PROMPT_TEXTO, font=FONTE, fill=PROMPT)
        deslocamento = MARGEM_X + int(desenho.textlength(PROMPT_TEXTO, font=FONTE))
        desenho.text((deslocamento, y), digitando, font=FONTE, fill=COMANDO)
        if cursor:
            largura_digitado = int(desenho.textlength(digitando, font=FONTE))
            x = deslocamento + largura_digitado
            desenho.rectangle([x + 1, y + 2, x + 9, y + 18], fill=CURSOR)

    return imagem


def montar(saida: Path) -> None:
    """Roda o roteiro completo e grava o GIF no caminho informado."""
    roteiro = [
        ["add", "Comprar mantimentos"],
        ["add", "Estudar Python"],
        ["add", "Lavar a louca"],
        ["list"],
        ["mark-in-progress", "2"],
        ["mark-done", "3"],
        ["list", "in-progress"],
        ["update", "1", "Comprar mantimentos e cozinhar o jantar"],
        ["delete", "3"],
        ["list"],
        ["mark-done", "42"],
    ]

    quadros: List[Image.Image] = []
    duracoes: List[int] = []
    historico: List[Linha] = [
        ("Rastreador de tarefas em Python - biblioteca padrao, sem dependencias.", TITULO),
        ("", TEXTO),
    ]

    quadros.append(moldura(historico))
    duracoes.append(1200)

    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / "tarefas.json"

        for argumentos in roteiro:
            comando = "task-cli " + " ".join(
                f'"{parte}"' if " " in parte else parte for parte in argumentos
            )

            for tamanho in range(PASSO_DIGITACAO, len(comando) + PASSO_DIGITACAO, PASSO_DIGITACAO):
                quadros.append(moldura(historico, comando[:tamanho]))
                duracoes.append(MS_DIGITACAO)
            duracoes[-1] = MS_ANTES_DA_SAIDA

            historico.append((PROMPT_TEXTO + comando, COMANDO))
            for linha in rodar(arquivo, argumentos):
                historico.append(colorir(linha))
            historico.append(("", TEXTO))

            quadros.append(moldura(historico))
            duracoes.append(MS_DEPOIS_DA_SAIDA)

    duracoes[-1] = MS_FINAL

    saida.parent.mkdir(parents=True, exist_ok=True)
    reduzidos = [
        quadro.convert("P", palette=Image.Palette.ADAPTIVE, colors=16) for quadro in quadros
    ]
    reduzidos[0].save(
        saida,
        save_all=True,
        append_images=reduzidos[1:],
        duration=duracoes,
        loop=0,
        optimize=True,
        disposal=2,
    )
    tamanho_kb = saida.stat().st_size / 1024
    print(f"GIF gravado em {saida} ({len(quadros)} quadros, {tamanho_kb:.0f} KB)")


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else SAIDA_PADRAO
    montar(destino)

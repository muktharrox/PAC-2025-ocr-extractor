"""Gera documentos RGP sintéticos (PF e PJ) em PDF (texto nativo) e PNG (imagem).

Serve para testar o pipeline de ponta a ponta SEM precisar de documentos reais.
- O PDF tem texto pesquisável -> processável sem nenhum OCR instalado.
- O PNG é uma imagem -> exige um motor de OCR (rapidocr/tesseract).

Uso:
    python -m tools.generate_synthetic_docs            # gera tudo em dataset/
    python -m tools.generate_synthetic_docs --pdf-only
"""
from __future__ import annotations

import argparse
import json
import os

# --------------------------------------------------------------------------
# Geração de CPF/CNPJ válidos (dígitos verificadores corretos) para os exemplos
# --------------------------------------------------------------------------
_CNPJ_W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_CNPJ_W2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def _cpf_digits(base9: str) -> str:
    d = base9
    for length in (9, 10):
        total = sum(int(d[i]) * ((length + 1) - i) for i in range(length))
        chk = (total * 10) % 11
        chk = 0 if chk == 10 else chk
        d += str(chk)
    return d


def make_cpf(base9: str) -> str:
    d = _cpf_digits(base9)
    return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


def _cnpj_digits(base12: str) -> str:
    def dv(ds: str, ws: list[int]) -> int:
        total = sum(int(x) * w for x, w in zip(ds, ws))
        r = total % 11
        return 0 if r < 2 else 11 - r

    d = base12
    d += str(dv(d, _CNPJ_W1))
    d += str(dv(d, _CNPJ_W2))
    return d


def make_cnpj(base12: str) -> str:
    d = _cnpj_digits(base12)
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


# Valores de exemplo (válidos por construção).
CPF_PF = make_cpf("123456789")
CPF_REP = make_cpf("987654321")
CNPJ_PJ = make_cnpj("112223330001")


# --------------------------------------------------------------------------
# Conteúdo dos documentos
# --------------------------------------------------------------------------
_HEADER = [
    "REPUBLICA FEDERATIVA DO BRASIL",
    "MINISTERIO DA PESCA E AQUICULTURA",
    "REGISTRO GERAL DA ATIVIDADE PESQUEIRA - RGP",
    "CERTIFICADO DE REGISTRO DE EMBARCACAO PESQUEIRA",
    "",
]


def document_lines(kind: str) -> list[str]:
    common = _HEADER + [
        "Numero do Processo: 21050.003108/99-98",
        "Numero RGP: SC-0004633-8",
        "Codigo da Frota: 3.09.001",
        "Inscricao Autoridade Naval: 443-007738-0",
        "",
        "DADOS DA EMBARCACAO",
        "Nome da Embarcacao: LEALMAR",
        "Ano de Construcao: 1984",
        "Numero de Tripulantes: 4",
        "Comprimento: 21,44",
        "Arqueacao Bruta: 91",
        "Potencia do Motor: 300",
        "Material do Casco: Aco",
        "Propulsao: Motor",
        "Combustivel: Diesel",
        "",
        "IDENTIFICACAO DO INTERESSADO",
    ]
    if kind == "pj":
        return common + [
            "Razao Social: Comercio de Pescados Palhoca Ltda Me",
            f"CNPJ: {CNPJ_PJ}",
            "Representante Legal: Celio Alecio Martins",
            f"CPF: {CPF_REP}",
            "",
            "VALIDADE",
            "Inicio: 12/11/2018",
            "Termino: 12/11/2023",
        ]
    return common + [
        "Nome: Joao da Silva Pescador",
        f"CPF: {CPF_PF}",
        "Endereco: Rua das Redes, 100",
        "Bairro: Centro",
        "Cidade: Palhoca",
        "UF: SC",
        "",
        "VALIDADE",
        "Inicio: 12/11/2018",
        "Termino: 12/11/2023",
    ]


def expected_json(kind: str) -> dict:
    base = {
        "tipo_documento": "RGP_PJ" if kind == "pj" else "RGP_PF",
        "numero_processo": "21050.003108/99-98",
        "numero_rgp": "SC-0004633-8",
        "codigo_frota": "3.09.001",
        "inscricao_autoridade_naval": "443-007738-0",
        "embarcacao": {
            "nome": "LEALMAR",
            "ano_construcao": 1984,
            "numero_tripulantes": 4,
            "comprimento_metros": 21.44,
            "arqueacao_bruta": 91.0,
            "potencia_motor_hp": 300.0,
            "material_casco": "Aco",
            "propulsao": "Motor",
            "combustivel": "Diesel",
        },
        "validade": {"inicio": "2018-11-12", "fim": "2023-11-12"},
    }
    if kind == "pj":
        base["interessado"] = {
            "tipo": "PJ",
            "razao_social": "Comercio de Pescados Palhoca Ltda Me",
            "cnpj": CNPJ_PJ,
            "representante_legal": {"nome": "Celio Alecio Martins", "cpf": CPF_REP},
        }
    else:
        base["interessado"] = {"tipo": "PF", "nome": "Joao da Silva Pescador", "cpf": CPF_PF}
    return base


# --------------------------------------------------------------------------
# Renderização
# --------------------------------------------------------------------------
def build_pdf_from_lines(lines: list[str]) -> bytes:
    from fpdf import FPDF  # type: ignore
    from fpdf.enums import XPos, YPos  # type: ignore

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        if line.strip():
            pdf.multi_cell(0, 7, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.ln(4)
    return bytes(pdf.output())


def build_pdf_bytes(kind: str) -> bytes:
    return build_pdf_from_lines(document_lines(kind))


def _load_font(size: int):
    from PIL import ImageFont  # type: ignore

    for path in (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def build_png_bytes(kind: str) -> bytes:
    import io

    from PIL import Image, ImageDraw  # type: ignore

    width, height = 1240, 1754  # ~A4 a 150 DPI
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = _load_font(24)
    y = 50
    for line in document_lines(kind):
        draw.text((70, y), line, fill="black", font=font)
        y += 36
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera documentos RGP sintéticos.")
    parser.add_argument("--pdf-only", action="store_true", help="não gerar PNG")
    parser.add_argument("--out", default=None, help="diretório base (default: ../dataset)")
    args = parser.parse_args()

    base_dir = args.out or os.path.join(os.path.dirname(__file__), "..", "dataset")
    base_dir = os.path.abspath(base_dir)

    for kind in ("pf", "pj"):
        folder = os.path.join(base_dir, kind)
        os.makedirs(folder, exist_ok=True)
        # PDF
        with open(os.path.join(folder, f"sintetico_{kind}.pdf"), "wb") as fh:
            fh.write(build_pdf_bytes(kind))
        # JSON esperado
        with open(os.path.join(folder, f"sintetico_{kind}.json"), "w", encoding="utf-8") as fh:
            json.dump(expected_json(kind), fh, ensure_ascii=False, indent=2)
        # PNG
        if not args.pdf_only:
            try:
                with open(os.path.join(folder, f"sintetico_{kind}.png"), "wb") as fh:
                    fh.write(build_png_bytes(kind))
            except Exception as exc:  # pragma: no cover
                print(f"[aviso] PNG não gerado para {kind}: {exc}")
        print(f"[ok] documentos sintéticos de {kind.upper()} em {folder}")


if __name__ == "__main__":
    main()

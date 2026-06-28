# RGP Extractor

Serviço **local e gratuito** para extrair dados de documentos RGP (Registro
Geral da Atividade Pesqueira) — pessoa física e jurídica — a partir de **PDF,
PNG ou JPG**, retornando um **JSON estruturado** com validação determinística
(CPF, CNPJ, RGP, datas, número de processo) e confiança por campo.

Sem APIs pagas. Todo o processamento roda na sua máquina/servidor.

---

## Como rodar (escolha um caminho)

### 1. Teste rápido nesta máquina — SEM OCR (recomendado para validar agora)

O caminho **"PDF com texto nativo"** não precisa de Tesseract nem de RapidOCR.
Funciona só com as dependências do núcleo.

```powershell
# na pasta do projeto
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# gera documentos sintéticos (PF e PJ) em dataset/ para você testar
python -m tools.generate_synthetic_docs --pdf-only

# roda a bateria de testes
pytest

# sobe a API
uvicorn app.main:app --reload
```

Ou simplesmente:

```powershell
./run_local.ps1
```

Depois abra a documentação interativa em **http://localhost:8000/api/doc** e
envie `dataset/pj/sintetico_pj.pdf` no endpoint `POST /api/v1/extract`.

### 2. Com OCR (imagens PNG/JPG e PDFs escaneados)

```powershell
pip install -r requirements-ocr.txt
python -m tools.generate_synthetic_docs        # gera também os PNGs
./run_local.ps1 -WithOcr
```

O motor padrão é o **RapidOCR** (modelos PP-OCR da família PaddleOCR via ONNX),
que instala 100% por `pip` e funciona offline. O **Tesseract** é opcional
(instale o binário e `pytesseract`, e configure `RGP_OCR_ENGINES=tesseract`).

> Este projeto **não usa Docker** — roda direto com Python + venv. Para colocar
> em um servidor, basta `uvicorn app.main:app --host 0.0.0.0 --port 8000`
> (atrás de um proxy reverso, ou como serviço do Windows / `systemd` no Linux).

---

## Endpoints

| Método | Rota                                            | Descrição                         |
|--------|-------------------------------------------------|-----------------------------------|
| GET    | `/health`                                       | status + motores de OCR ativos    |
| POST   | `/api/v1/extract`                               | envia o arquivo, recebe o JSON    |
| GET    | `/api/v1/documents/{id}`                        | consulta resultado salvo          |
| PUT    | `/api/v1/documents/{id}/fields/{campo}`         | correção manual de um campo       |

Exemplo de chamada:

```bash
curl -F "file=@dataset/pj/sintetico_pj.pdf" http://localhost:8000/api/v1/extract
```

---

## Arquitetura

```
app/
├── documents/      # carregar/validar PDF e imagem (magic bytes, limites)
├── image_processing/  # pré-processamento (cinza, denoise, deskew) — OpenCV opcional
├── ocr/            # motores plugáveis (rapidocr, tesseract) + seleção automática
├── classification/ # PF x PJ por palavras-chave + CPF/CNPJ válidos
├── extraction/     # parser por rótulos+regex, normalização, montagem do resultado
├── validators/     # CPF, CNPJ, RGP, datas, nº de processo, UF (determinísticos)
├── quality/        # confiança por campo e do documento + decisão de revisão
├── schemas/        # modelos Pydantic de entrada/saída
├── pipeline.py     # orquestra: bytes -> JSON
└── main.py         # FastAPI
tools/generate_synthetic_docs.py  # gera documentos de teste (PF/PJ)
tests/              # validadores, parser, classificador, pipeline e API
```

Fluxo: **arquivo → validação → (texto nativo do PDF | OCR da imagem) →
classificação PF/PJ → extração por rótulos → normalização → validação →
confiança → JSON**.

---

## Decisões de projeto (diferenças em relação ao PLANO.md)

Estas escolhas foram feitas para o sistema ser **testável imediatamente** nesta
máquina (Windows, sem Tesseract e sem Docker) e por **ainda não haver
documentos reais**:

1. **OCR padrão = RapidOCR** (pip, sem dependência de sistema) em vez do
   Tesseract. O Tesseract continua suportado como motor alternativo.
2. **Extração por rótulos + regex** em vez de templates por coordenada. Os
   templates por coordenada (Fases 4 e 6 do plano) exigem documentos de
   referência para mapear posições — quando houver amostras reais, a extração
   por coordenadas pode ser plugada sem alterar o restante do pipeline.
3. **Gerador de documentos sintéticos** para permitir teste de ponta a ponta
   sem documentos reais.
4. **Caminho de texto nativo** (PDF pesquisável) processa **sem nenhum OCR**.

O que **já** atende ao MVP do plano (seção 10): aceita PDF/PNG/JPG, identifica
PF/PJ, extrai os campos principais, valida CPF/CNPJ/datas/RGP, retorna JSON,
marca campos duvidosos, processa localmente, sem API paga, com testes
automatizados.

---

## Integração com o backend Node.js (PAC)

O Node não executa OCR; ele envia o arquivo para este serviço:

```javascript
const form = new FormData();
form.append("file", arquivo);
const resp = await fetch("http://rgp-extractor:8000/api/v1/extract", {
  method: "POST",
  body: form,
});
const resultado = await resp.json();
```

---

## Próximos passos (homologação)

- Coletar documentos reais (PF e PJ, várias qualidades) em `dataset/`.
- Mapear templates por coordenada para os layouts recorrentes.
- Ajustar limiares de confiança (`RGP_CONF_*`) com base nos acertos por campo.
- Reprocessamento com segundo motor (Tesseract↔RapidOCR) em campos duvidosos.

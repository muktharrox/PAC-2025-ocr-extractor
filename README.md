# PAC RGP Extractor

API **NestJS** que recebe um certificado **RGP** (Registro Geral da Atividade Pesqueira — MAPA/Secretaria de Aquicultura e Pesca), em **PDF ou imagem**, e devolve os dados **estruturados em JSON** usando o LLM **Google Gemini** (`gemini-2.5-flash`) com visão.

Cobre os dois modelos do documento:

- **Pessoa Física** — Nome + CPF
- **Pessoa Jurídica** — Razão Social + CNPJ + representante legal

## Como funciona

1. Upload do arquivo em `POST /api/v1/extract` (multipart, campo `file`).
2. O PDF é enviado **inline** ao Gemini (sem OCR local, sem rasterização). O modelo lê texto + imagem de cada página.
3. A resposta é forçada a um schema (**Structured Output**) e validada defensivamente com Zod.
4. **Validadores determinísticos** conferem CPF/CNPJ (mód-11), RGP e datas, normalizam os valores e sinalizam o que precisa de revisão.
5. Retorna um envelope JSON: `{ success, document_type, data, validations, warnings, processing }`.

## Requisitos

- Node.js 20+
- Uma chave de API do Gemini ([Google AI Studio](https://aistudio.google.com/apikey))

## Instalação

```bash
npm install
cp .env.example .env   # preencha GEMINI_API_KEY
```

## Execução

```bash
npm run start:dev      # http://localhost:3001
```

- **Swagger:** http://localhost:3001/api/doc
- **Health:** `GET http://localhost:3001/api/v1/health`

### Exemplo (curl)

```bash
curl -F "file=@Lealmar RGP 12.11.23.pdf" http://localhost:3001/api/v1/extract
```

## Variáveis de ambiente

| Variável             | Default            | Descrição                                                        |
| -------------------- | ------------------ | ---------------------------------------------------------------- |
| `GEMINI_API_KEY`     | —                  | Obrigatória. Chave do Google AI Studio.                          |
| `GEMINI_MODEL`       | `gemini-2.5-flash` | Modelo usado.                                                    |
| `GEMINI_MAX_RETRIES` | `2`                | Tentativas extras em caso de falha de parsing/transient.         |
| `PORT`               | `3001`             | Porta HTTP.                                                      |
| `CORS_ORIGIN`        | `*`                | Origem permitida no CORS.                                        |
| `MAX_UPLOAD_MB`      | `20`               | Limite de tamanho do upload.                                     |

## Testes

```bash
npm test           # unit (validadores, schema, use case) — não chama a API
npm run test:e2e   # e2e do controller com o gateway Gemini mockado
npm run smoke:real # OPCIONAL: chama a API Gemini de verdade (consome cota)
```

## Formato da resposta

```jsonc
{
  "success": true,
  "document_type": "RGP_PJ",            // RGP_PF | RGP_PJ | NAO_IDENTIFICADO
  "data": {
    "tipo_pessoa": "PJ",
    "numero_rgp": "SC-0004633-8",
    "nome_embarcacao": "LEALMAR",
    "razao_social": "COMÉRCIO DE PESCADOS PALHOÇA LTDA ME",
    "cnpj": "05.383.614/0001-13",
    "especie_alvo": ["..."],
    "fauna_acompanhante": ["..."],
    "data_inicio_validade": "2018-11-12",
    "data_termino_validade": "2023-11-12"
    // ... demais campos (null quando ausentes)
  },
  "validations": [
    { "campo": "cnpj", "valor": "05.383.614/0001-13", "valido": true, "normalizado": "05.383.614/0001-13", "mensagem": null }
  ],
  "warnings": [],
  "processing": { "model": "gemini-2.5-flash", "input_tokens": 0, "output_tokens": 0, "pages": 1, "used_native_text": false, "duration_ms": 0 }
}
```

## Arquitetura

Clean Architecture (4 camadas), espelhando o backend principal `back`:

```
src/
├── domain/          # entities (IRgpCertificado, IExtractResult) + gateway (ILlmRgpGateway)
├── application/     # AppError + ExtractRgpUseCase (retry, validações, envelope)
├── infrastructure/  # GeminiRgpAdapter, schema Zod, validators (cpf/cnpj/rgp/dates), providers
└── presentation/    # controller, DTOs, módulos, filtro de erro, main.ts (swagger)
```

O gateway `ILlmRgpGateway` é **agnóstico de provedor** — trocar Gemini por outro LLM é só implementar outro adapter.

## Integração futura com o `back`

Defina `OCR_EXTRACTOR_URL=http://localhost:3001` no `back` e chame `POST /api/v1/extract` via `axios`, mantendo a chave Gemini fora do backend principal.

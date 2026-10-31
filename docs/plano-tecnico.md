# Plano técnico — MVP de preenchimento de minutas

> Estado: proposta para aprovação. Nenhum código de aplicação foi ainda escrito.

## Âmbito confirmado com a utilizadora

Objetivo: a utilizadora guarda as suas minutas na aplicação; em cada processo escolhe uma minuta,
junta os documentos (Cartão de Cidadão, caderneta, certidão, DUC…), revê os campos preenchidos e
obtém o documento pronto a **imprimir ou guardar em PDF**.

| Decisão | Escolha |
|---|---|
| Leitura do Cartão de Cidadão | **Digitalização** (PDF frente e verso), não leitor de cartões |
| Minutas no MVP | **Uma**: escritura de compra e venda. Outras depois, com o mesmo mecanismo |
| Formato dos documentos de origem | **PDF** (digitalizado ou com texto). Imagens ficam fora do MVP |
| Resultado | `.docx` preenchido + **PDF** e impressão (via Word instalado) — passa a fazer parte do MVP |
| Biblioteca de minutas | As minutas preparadas são copiadas para a pasta de dados da aplicação, para ficarem "guardadas lá" |

### O que cada documento pode fornecer

| Documento | Campos | Notas |
|---|---|---|
| Cartão de Cidadão (digitalizado) | nome completo, n.º do documento, validade, data de nascimento, filiação, nacionalidade, NIF | A zona MRZ do verso (3 linhas normalizadas, com dígitos de controlo) serve para validar n.º, datas e nome. O nome com acentos vem da frente. NIF validado pelo dígito de controlo. **Não contém estado civil, regime de bens nem morada.** |
| Caderneta predial | artigo matricial, freguesia, concelho, VPT, descrição/composição | Normalmente PDF com texto (Portal das Finanças) — extração por regras, sem OCR |
| Certidão permanente | n.º da ficha, inscrições (AP. n.º/data), sujeitos ativos, código de acesso | Normalmente PDF com texto |
| DUC (IMT, Imposto do Selo) | n.º do DUC, valor, imposto | Normalmente PDF com texto |
| Outros (estado civil, morada, pagamento, mediadora) | — | Preenchimento manual ou documentos adicionais; assinalados como "em falta" |

Nota a confirmar pela utilizadora: enquadramento legal da digitalização e conservação de cópias do
Cartão de Cidadão dos clientes.

## 0. Análise da minuta (escritura de compra e venda, cartório notarial)

O ficheiro analisado não é versionado (contém dados de um caso). Resumo técnico:

**Formato:** `.docx` de uma secção, A4, Times New Roman 14 pt, cerca de 305 runs. Sem tabelas, caixas
de texto, campos Word, controlos de conteúdo, imagens, comentários nem revisões controladas. Tem
cabeçalho próprio (cartório, notária, `Livro:____ Fls.:____`), notas de rodapé/fim vazias e um realce.

**Convenções notariais que têm de ser preservadas:**

- Parágrafos com **limites esquerdo/direito** (as linhas verticais da margem do livro).
- **Tabulações com preenchimento de sublinhados** (posição 7938) e linhas de `____` para "trancar"
  espaços em branco. A aplicação não pode remover nem recalcular estes elementos. Uma vantagem:
  a tabulação com preenchimento ajusta-se sozinha ao comprimento do texto inserido.
- Números e datas **por extenso** (ex.: data do ato) e valores em algarismos (`€ 54.380,00`).

**Estado atual da minuta:** é um **rascunho meio preenchido** de um caso concreto, não um modelo limpo.

- Os campos por preencher estão marcados com `?????` de comprimento variável (11 ocorrências).
- **Esses marcadores estão partidos em 2 ou 3 runs** — é exatamente o problema de "split runs" que
  se descreve na secção 4, confirmado no ficheiro real.
- Há dados do caso já escritos (data, lote, freguesia, inscrição AP., VPT, alvará) que, num modelo
  reutilizável, também têm de passar a ser placeholders.
- A identificação dos outorgantes está **incompleta/truncada** (ex.: `“A, e tendo verificado…` e um
  nome isolado no SEGUNDO outorgante). Falta o bloco completo com nome, estado civil, regime,
  morada, NIF e CC.

**Campos variáveis identificados:**

| Bloco | Campo | Hoje na minuta |
|---|---|---|
| Ato | data por extenso, livro, folhas | preenchido / `____` no cabeçalho |
| 1.º outorgante | sociedade vendedora (firma, NIPC, sede, matrícula), sócios-gerentes (nome, estado civil, morada, NIF, CC) | truncado |
| 1.º outorgante | consulta ao RCBE | texto fixo |
| 2.º outorgante | compradora (nome, estado civil, regime de bens, morada, NIF, CC) | truncado |
| Preço | preço (algarismos e extenso) | `?????` |
| Imóvel | natureza/composição, lote, lugar, freguesia, concelho | preenchido |
| Imóvel | n.º da ficha da descrição predial | `?????` |
| Imóvel | inscrição da aquisição (AP. n.º e data) | preenchido |
| Imóvel | artigo matricial | `?????` |
| Imóvel | VPT | preenchido |
| Imóvel | registo do loteamento (AP.) | `?????` |
| Mediação | mediadora (nome, licença AMI) | `?????` |
| Pagamento | meio de pagamento (cheque/transferência, banco, n.º) | `?????` |
| Título urbanístico | alvará n.º, data de emissão, entidade | parcialmente preenchido / `?????` |
| Arquivo | DUC Imposto do Selo verba 1.1 TGIS: n.º e valor | `?????` |
| Arquivo | DUC IMT: n.º e valor | `?????` |
| Exibido | código de acesso da certidão permanente | `?????` |
| Exibido | data de obtenção da caderneta predial | preenchido |

**Concordância de género/número:** o texto tem "a segunda outorgante", "os primeiros outorgantes",
"vendem", "a compradora". **A aplicação não altera esse texto.** Se o escritório precisar de variantes
(um comprador, vários compradores), isso faz-se com modelos diferentes ou, numa fase posterior,
com blocos condicionais escritos pelo próprio solicitador.

**Consequência para o MVP:** a Fase 1 tem de incluir um passo de **preparação do modelo**:

1. Partir de uma versão limpa da minuta e substituir cada `?????` e cada dado do caso por um
   placeholder `{{ ... }}`, escrito de uma só vez no Word (ou colado como texto simples) para não
   ficar partido.
2. A aplicação verifica o modelo e recusa-o se ainda houver `??` ou placeholders partidos,
   indicando onde estão.
3. Opcional (Fase 1b): um assistente que deteta sequências `?{3,}` e propõe convertê-las em
   placeholders, juntando os runs. O texto à volta não é alterado e o utilizador confirma cada um.

## 1. Arquitetura

```
┌──────────────────────────── Tauri 2 (processo principal, Rust) ────────────────────────────┐
│  Janela WebView2 ── React + TypeScript + Vite (UI)                                         │
│        │ invoke("engine_call", {method, params})                                           │
│  Rust: arranca o sidecar, faz proxy das chamadas, restringe permissões (capabilities)      │
│        │ JSON-RPC 2.0 por stdin/stdout (sem portas de rede abertas)                        │
│  Sidecar Python (empacotado com PyInstaller)                                               │
│    ├─ templates: análise e preenchimento de .docx (docxtpl)                                │
│    ├─ ingest: PDF (texto nativo) → se não houver texto, render + OCR (Tesseract por)       │
│    ├─ extraction: regras determinísticas + normalização + validação (NIF, CC, valores…)    │
│    ├─ db: SQLite (metadados, caminhos, valores confirmados)                                │
│    └─ ai (desativado por defeito, fase posterior)                                          │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

Decisões:

- **Python como "motor" único.** Toda a lógica de domínio (docx, OCR, regras, BD) vive em Python, que
  tem as melhores bibliotecas para isto. O Rust fica fino: só ciclo de vida do sidecar e segurança.
- **stdin/stdout em vez de servidor HTTP local.** Não abre portas; nenhum outro processo do PC consegue
  falar com o motor.
- **SQLite gerido pelo Python** (um só escritor, migrações num só sítio).
- **Tipos partilhados:** modelos Pydantic no Python → JSON Schema → tipos TypeScript gerados
  (`json-schema-to-typescript`). Evita divergência entre UI e motor.

### Avaliação das tecnologias propostas

| Tecnologia | Avaliação |
|---|---|
| React + TS + Vite | Adequado. |
| Tauri 2 | Adequado. Requer Rust + MSVC Build Tools para compilar; o utilizador final não precisa. |
| Python | Adequado como sidecar. Requer Python 3.12 para desenvolvimento. |
| Tesseract (`por`) | Adequado. Para o MVP: instalação separada com caminho configurável; na fase de instalador, incluí-lo no pacote. |
| PyMuPDF | Tecnicamente o melhor, **mas é AGPL-3.0** (ou licença comercial paga). Para uso interno de um escritório não há problema prático; se a aplicação vier a ser distribuída/vendida a terceiros, há obrigações. Alternativa sem esse risco: **pypdfium2** (Apache/BSD), suficiente para extrair texto e renderizar páginas para OCR. **Decisão pendente tua.** |
| docxtpl vs python-docx | **docxtpl** (usa python-docx por baixo). Substitui placeholders `{{ }}` preservando a formatação do run, trata cabeçalhos/rodapés e já corrige parte dos placeholders partidos pelo Word. python-docx puro obrigaria a reimplementar isso. Uso restrito: só variáveis simples no MVP, sem lógica Jinja no texto jurídico. |
| SQLite | Adequado. |
| Exportação PDF | Word está instalado → automação via COM (`pywin32`), que dá o resultado mais fiel. LibreOffice como alternativa. Fora do MVP. |

## 2. Estrutura de pastas

```
minutas-solicitadoria/
├─ apps/desktop/
│  ├─ src/                    # React
│  │  ├─ pages/               # Dashboard, Processo, Documentos, Revisão, Gerar, Histórico
│  │  ├─ components/
│  │  ├─ engine/              # cliente tipado para o motor (invoke → JSON-RPC)
│  │  └─ types/generated/     # tipos gerados a partir do JSON Schema
│  └─ src-tauri/
│     ├─ src/                 # spawn do sidecar, proxy, comandos
│     ├─ capabilities/        # permissões mínimas (fs, dialog)
│     └─ binaries/            # sidecar empacotado (gerado, não versionado)
├─ engine/
│  ├─ pyproject.toml
│  ├─ src/minutas_engine/
│  │  ├─ main.py              # loop JSON-RPC
│  │  ├─ rpc/                 # handlers por domínio
│  │  ├─ models/              # Pydantic (fonte dos tipos partilhados)
│  │  ├─ db/                  # ligação, migrações SQL
│  │  ├─ templates/           # scan.py (placeholders), render.py
│  │  ├─ ingest/              # pdf.py, image.py, ocr.py
│  │  ├─ extraction/          # rules/, normalize.py, validate.py, resolve.py
│  │  ├─ fields/catalog.yaml  # catálogo de campos
│  │  └─ logging.py           # logs sem dados pessoais
│  └─ tests/                  # apenas dados sintéticos
├─ docs/
└─ scripts/                   # build do sidecar, geração de tipos
```

## 3. Representação dos campos

### 3.1 Placeholders na minuta

- Sintaxe: `{{ nome_do_campo }}`, nomes em `snake_case`, ASCII, sem acentos.
- Partes numeradas: `{{ vendedor_1_nome }}`, `{{ comprador_1_nif }}`, `{{ comprador_2_nif }}`.
- O solicitador insere os placeholders no Word uma vez; a minuta "preparada" é guardada como modelo.
- Ao importar, a aplicação **analisa** o documento (corpo, tabelas, cabeçalhos, rodapés, caixas de
  texto) e mostra: placeholders encontrados, placeholders desconhecidos (não estão no catálogo),
  placeholders malformados/partidos, e qualquer `{%`/`{#` que possa interferir.

### 3.2 Catálogo de campos (`fields/catalog.yaml`)

```yaml
- key: comprador_1_nif
  label: "NIF do comprador 1"
  group: comprador_1
  type: nif            # text | nif | cc | money | date | address | enum | multiline
  required: true
- key: preco_extenso
  label: "Preço por extenso"
  type: text
  derived_from: preco  # calculado deterministicamente a partir de 'preco', sempre revisto
```

Placeholders que não estejam no catálogo continuam a funcionar como texto livre (preenchimento manual).

### 3.3 Dados extraídos

```ts
type Candidate = {
  fieldKey: string;
  value: string;              // tal como aparece no documento
  normalized: string;         // ex.: NIF sem espaços, valor em cêntimos
  method: "rule" | "ai" | "manual" | "derived";
  confidence: number;         // 0–1
  source?: { documentId: string; page: number; snippet: string; bbox?: [number, number, number, number] };
  validation: "ok" | "invalid" | "not_applicable";  // ex.: dígito de controlo do NIF
};

type FieldState = {
  fieldKey: string;
  candidates: Candidate[];
  status: "missing" | "suggested" | "low_confidence" | "conflict" | "confirmed" | "left_blank";
  confirmedValue?: string;    // só preenchido por ação humana
};
```

Regras de resolução:

1. Sem candidatos → `missing`.
2. Candidatos com valores normalizados diferentes → `conflict`; **nenhum é pré-selecionado**.
3. Um valor, confiança ≥ limiar e validação ok → `suggested` (pré-preenchido, mas por confirmar).
4. Caso contrário → `low_confidence`, campo vazio com a sugestão visível ao lado.
5. A geração só avança quando todos os campos estão `confirmed` ou explicitamente `left_blank`.

## 4. Riscos de preservação da formatação

| Risco | Mitigação |
|---|---|
| O Word parte `{{nome}}` em vários runs (corretor, edição, histórico de revisões) | docxtpl trata parte dos casos; o nosso scanner deteta os restantes e indica ao utilizador onde reescrever o placeholder de uma só vez. |
| Placeholders em cabeçalhos, rodapés, caixas de texto, notas de rodapé | Scanner percorre todas as partes; teste específico para cada uma. |
| Formatação do valor | O valor herda a formatação do primeiro carácter do placeholder (negrito, maiúsculas, tipo de letra). Documentar. |
| Quebras de linha no valor (moradas) | Usar `RichText`/quebras explícitas em campos `multiline`. |
| Caracteres especiais (`&`, `<`, aspas) | `autoescape=True`. |
| Valor em falta gera texto vazio silencioso | Validação prévia: não se gera sem todos os campos resolvidos; render com `StrictUndefined`. |
| Revisões controladas / comentários na minuta | Avisar na importação; recomendar aceitar alterações antes de preparar o modelo. |
| Campos Word (DATA, REF, numeração automática) | Não são tocados; avisar que o Word pode atualizá-los ao abrir. |
| Ficheiros `.doc` antigos / modo de compatibilidade | Só `.docx`; pedir conversão no Word. |
| Concordância de género/número | Fora do MVP; o texto da minuta nunca é alterado pela aplicação. |
| Sobrescrever a minuta original | Escrita para ficheiro temporário + renomear; bloqueio se o destino for igual à origem; hash SHA-256 da minuta antes/depois. |

## 5. Segurança e privacidade (aplicado ao MVP)

- Tudo local. Nenhuma chamada de rede no MVP.
- BD guarda: processos, caminhos e hash dos ficheiros, lista de placeholders, valores confirmados e
  pequenos excertos de evidência (a linha onde o valor foi encontrado). **Não guarda o texto OCR
  integral.** O texto OCR fica em memória durante a sessão (decisão a rever se o OCR for demasiado lento).
- Logs técnicos só com IDs, contagens e tempos — nunca valores, nomes de ficheiro ou excertos.
- BD e dados em `%APPDATA%\MinutasSolicitadoria`, com ACL do utilizador. Recomendação documentada de
  BitLocker e de cópias de segurança (a BD contém dados pessoais).
- Capabilities do Tauri restringidas a diálogos de ficheiro e às pastas escolhidas.
- Avisos permanentes no ecrã de revisão e de geração: "Valide todos os dados e o documento final."
- O projeto é concebido tendo em conta o RGPD; não afirma conformidade sem análise específica.
- IA (fase posterior): desligada por defeito, consentimento explícito por processo mostrando o que será
  enviado, chave de API guardada no Gestor de Credenciais do Windows, resposta em JSON validado que
  apenas gera `Candidate`s com `method: "ai"` — nunca toca na minuta. Uma subscrição Claude/ChatGPT
  não dá acesso à API; a API é paga à parte.

## 6. Plano por fases

| Fase | Entrega | Resultado utilizável |
|---|---|---|
| **0. Esqueleto** | Tauri + React a arrancar o sidecar Python; `ping` JSON-RPC; lint/testes; scripts de build | App abre e fala com o motor |
| **1. Minutas e geração** | Biblioteca de minutas (importar `.docx`, validar placeholders), formulário manual, gerar `.docx` + **PDF** (Word) numa pasta escolhida, abrir para imprimir | **Preenchimento manual ponta-a-ponta, pronto a imprimir** |
| **2. Processos** | SQLite, criar/listar processos, associar minuta e documentos, histórico de gerados, dashboard | Trabalho organizado por processo |
| **3. PDFs e OCR** | PDF com texto vs. digitalizado (deteção por página); OCR `por` com progresso; visualizar texto por página | Texto extraído localmente |
| **4. Extração por tipo de documento** | Classificação do documento + extratores: **Cartão de Cidadão** (frente + MRZ), DUC, caderneta predial, certidão permanente; validações (NIF, MRZ); conflitos; ecrã de revisão com origem | Campos sugeridos e revistos pela utilizadora |
| 5. Pós-MVP | Outras minutas, instalador com Tesseract incluído, IA opcional, blocos repetidos/condicionais | — |

Cada fase começa com a lista exata de ficheiros que serão criados/alterados, para aprovação.

## 7. Pré-requisitos de desenvolvimento (em falta nesta máquina)

- Rust (`rustup`) + Microsoft C++ Build Tools
- Python 3.12
- Tesseract OCR com `por.traineddata`
- (Opcional) GitHub CLI `gh`

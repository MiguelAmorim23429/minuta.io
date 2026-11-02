# Preparar uma minuta

## Como a aplicação sabe o que preencher

Cada espaço a preencher é um **campo** escrito entre chavetas duplas:

```
… pelo preço de {{ preco }}, vendem à segunda outorgante …
```

- Nomes em minúsculas, sem acentos nem espaços: `comprador_1_nome`, `duc_imt_valor`.
- O mesmo campo pode aparecer várias vezes; todas as ocorrências recebem o mesmo valor.
- O valor fica com a formatação do campo no Word (negrito, tamanho, tipo de letra).
- Campos podem estar no corpo, cabeçalhos e rodapés. Notas de rodapé não são preenchidas.

A lista de campos conhecidos (com nomes legíveis e grupos) está em
[`engine/src/minuta_engine/fields/catalog.yaml`](../engine/src/minuta_engine/fields/catalog.yaml).
Campos que não estejam no catálogo também funcionam: aparecem em "Outros campos".

## Minutas com `?????`

Se a minuta marca os espaços com `?????`, não é preciso editá-la à mão:

1. Importe a minuta em **Minutas → Importar minuta**.
2. No ecrã de revisão, escolha o campo correspondente a cada `?????`.
3. Carregue em **Converter**. Só o marcador é substituído; o texto da minuta não muda.

A conversão é feita na cópia guardada pela aplicação; o ficheiro original nunca é alterado.

## Dados de um caso concreto que ficaram escritos

Se a minuta tiver nomes, datas ou números de um caso anterior, use **Editar no Word** no ecrã
de revisão, substitua-os por `{{ nome_do_campo }}` (escrito de seguida, de uma só vez), grave
e carregue em **Analisar novamente**.

## O que a aplicação nunca faz

- Alterar cláusulas, a estrutura ou a formatação da minuta.
- Gerar um documento com campos por preencher — cada campo tem de ter valor ou ser marcado
  explicitamente como "Deixar em branco".
- Sobrescrever documentos existentes: se o nome já existir, cria `Nome (2).docx`.

# Dashboard individual de frequência — Curso Técnico em Enfermagem

Painel interativo no Google Sheets para acompanhar a frequência de cada aluno das
Turmas A e B do Curso Técnico em Enfermagem (ETSAL / UNCISAL) e a aptidão ao
auxílio estudantil. O auxílio exige frequência mínima de 75% em cada parcela.

O painel é feito só com fórmulas, validação de dados e gráficos nativos.
Não usa Apps Script, então funciona para quem tem acesso de leitura à planilha.

## O que o painel mostra

| Bloco | Conteúdo |
|---|---|
| Filtros vinculados | **Turma → Status → Aluno**. A lista de alunos mostra só quem pertence à turma e ao status escolhidos. Também há filtros de **Período** (parcela, curso completo ou intervalo personalizado) e **Disciplina**. |
| Ficha do aluno | Matrícula, código, turma e turno, status, data de ingresso, e-mail |
| Indicadores (12) | Frequência no período, presenças, faltas não justificadas, abonos, situação da meta, margem de faltas na parcela atual, parcelas aptas, valor apto acumulado, posição na turma, média da turma, dias de bloqueio/evasão, último lançamento |
| Gráficos | Evolução por parcela (aluno × média da turma × meta), presenças/faltas/abonos por mês, distribuição das situações |
| Calendário | Mês do último lançamento do período, com o código da situação de cada dia letivo |
| Tabelas | Aptidão nas 24 parcelas; ocorrências do período (faltas, abonos e bloqueios, com documento e observação) |

Se o aluno escolhido deixar de pertencer aos filtros (por exemplo, depois de trocar
a turma), o campo fica vermelho e aparece um aviso pedindo nova seleção.

## Como funciona

```
REGISTROS ─┐
ALUNOS ────┤
BASE FREQUÊNCIA ─┼──► CALC_DASH (oculta) ──► DASHBOARD DO ALUNO
CRONOGRAMA ──────┤        chaves + blocos       filtros, KPIs, gráficos
PARÂMETROS / FERIADOS ┘
```

- **`CALC_DASH`** é uma aba oculta que concentra todos os cálculos. Ela guarda:
  - chaves de valor único em `A:B`;
  - listas dinâmicas para as validações;
  - uma cópia filtrada dos lançamentos do aluno no período;
  - as séries dos gráficos.
- **`DASHBOARD DO ALUNO`** só lê `CALC_DASH`. As únicas células editáveis são os filtros das linhas 5 e 6. O resto da aba tem proteção de aviso.
- A frequência e a aptidão por parcela vêm da `BASE FREQUÊNCIA`, a mesma base dos relatórios oficiais. Assim, o painel nunca diverge do que é pago.

Detalhes de cada célula estão em [`docs/arquitetura.md`](docs/arquitetura.md).
O plano e as decisões de projeto estão em [`docs/plano.md`](docs/plano.md).

## Estrutura do repositório

```
build/layout.py     gerador das requisições (Sheets API batchUpdate)
docs/arquitetura.md mapa de células, fórmulas e dependências
docs/plano.md       plano, decisões e pendências
```

O gerador contém só estrutura, fórmulas e formatação. **Nenhum dado de aluno
fica no repositório.** Os JSON gerados em `build/` são ignorados pelo git.

## Gerar e aplicar

Requer Python 3.9+ e nenhuma dependência externa.

```bash
python3 build/layout.py estrutura > build/lote1.json   # cria as abas e escreve as fórmulas
python3 build/layout.py formato1  > build/lote2_1.json # formatos, larguras, mesclagens
python3 build/layout.py formato2  > build/lote2_2.json # mesclagens e estilos
python3 build/layout.py formato3  > build/lote2_3.json # bordas, validações, cond. format, proteção
python3 build/layout.py graficos  > build/lote3.json   # 3 gráficos
```

Envie cada arquivo, nesta ordem, como o corpo `requests` de
[`spreadsheets.batchUpdate`](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate)
na planilha de frequência. Pode usar qualquer cliente: API Explorer, `google-api-python-client`, Apps Script `Sheets.Spreadsheets.batchUpdate`, etc.
O lote `formato` (sem número) gera tudo de uma vez. Ele foi dividido em três só para caber no limite de payload do conector usado.

> **Atenção:** o lote `estrutura` usa `addSheet` com IDs fixos (`910010` e `910011`).
> Para reaplicar do zero, apague antes as abas `DASHBOARD DO ALUNO` e `CALC_DASH`.

### Pré-requisitos da planilha

O painel espera a estrutura atual da planilha de frequência:

- `REGISTROS`: dados a partir da linha 3. B = data, D = matrícula, H = disciplina, I = turno, J = aulas, K = situação, L = impacto, M = nº doc, N = status justif., Q = observações.
- `ALUNOS` (A:J), `BASE FREQUÊNCIA` (parcelas em G:AD, aptidão em AF:BC, lista de períodos em BS5:BS40), `CRONOGRAMA DE PAGAMENTOS` (C8:E31), `PARÂMETROS` (meta em B2, valor em B4, h/a em B5, códigos em A7:C15) e `FERIADOS`.

A planilha usa a localidade pt_BR. Por isso as fórmulas usam `;` como separador e
`HSTACK`/`VSTACK` no lugar de literais `{}`.

## Limitações conhecidas

- **Segmentações (slicers) não fazem cascata** no Google Sheets. Por isso os filtros são listas suspensas que apontam para listas dinâmicas. Ao trocar a turma, o aluno anterior não é limpo automaticamente; o painel mostra um aviso. Limpar o campo automaticamente exigiria um gatilho `onEdit` em Apps Script.
- O filtro de **Disciplina** depende do preenchimento da coluna H de `REGISTROS`. Hoje cerca de 45% dos lançamentos têm disciplina, e nenhum de outubro.
- A **margem de faltas** é uma estimativa: dias letivos previstos na parcela atual (excluindo feriados) × h/a × 25%, menos as faltas já registradas.

## Licença

[MIT](LICENSE)

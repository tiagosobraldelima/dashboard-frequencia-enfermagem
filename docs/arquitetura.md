# Arquitetura

Duas abas são criadas na planilha de frequência:

| Aba | sheetId | Visível | Papel |
|---|---|---|---|
| `DASHBOARD DO ALUNO` | 910010 | sim (1ª aba) | Interface: filtros, ficha, KPIs, gráficos, calendário, tabelas |
| `CALC_DASH` | 910011 | oculta | Todos os cálculos; o dashboard só lê esta aba |

A fonte única das fórmulas é `build/layout.py`, nas listas `CALC_KEYS`, `CALC_EXTRA`, `CALC_BLOCKS` e `DASH_CELLS`.

## Fluxo dos filtros

```
B5 Turma ─┐
D5 Status ┴─► CALC_DASH!M2 (lista "NOME — matrícula", ordenada)
                    │  validação ONE_OF_RANGE
                    ▼
              F5 Aluno ─► B2 ─► B3 válido? ─► B4 matrícula ─► P2 lançamentos do aluno
J5 Período ─► B5/B6 início/fim ───────────────────────────────┘        │
C6/E6 intervalo personalizado ─┘                                       ▼
L5 Disciplina ◄─ N2 (disciplinas do aluno no período)       KPIs, séries, calendário
```

Se o aluno em `F5` não estiver mais na lista `M2`, `B3` fica FALSO e `B4` fica vazio.
Nesse caso todos os blocos mostram "—" e o aviso em `F6` pede nova seleção.

## CALC_DASH — chaves (A:B)

| Célula | Chave | Origem |
|---|---|---|
| B2 | Aluno selecionado | `DASHBOARD!F5` |
| B3 | Aluno válido p/ filtros | `B2` está em `M2:M300` |
| B4 | Matrícula | dígitos finais de `B2` |
| B5 / B6 | Início / fim do período | `J5` → `BASE FREQUÊNCIA!AE2:AE3`, `CRONOGRAMA` ou `C6`/`E6` |
| B7 | Disciplina | `L5` ("Todas" por padrão) |
| B8 | Linha na BASE FREQUÊNCIA | MATCH da matrícula em `A5:A204` |
| B9 | Coluna do período na BASE | MATCH de `J5` em `G4:AE4` |
| B10 | Turma do aluno | `G32` |
| B11 / B12 / B13 | Meta / h/a por dia / valor da parcela | `PARÂMETROS` B2 / B5 / B4 |
| B14 / B15 | Total h/a / faltas h/a no período | soma sobre `P2:W` |
| B16 | Frequência | `(B14 − B15) / B14` |
| B17–B21 | Dias lançados, presenças, faltas, abonos, bloqueio/evasão | contagens sobre `S`/`T` |
| B22 | Situação da meta | Abaixo da meta / Em risco (margem `BASE!BL2`) / Atingida |
| B23 | Dias letivos previstos na parcela atual | NETWORKDAYS(B36; B37; feriados) |
| B24 | Margem de faltas na parcela atual (dias) | `(B23·B12·(1−B11) − B38) / B12` |
| B25 / B26 | Parcelas aptas / apuradas | linha `B8` de `BASE!AF:BC` |
| B27 | Valor apto | `B25 · B13` |
| B28–B30 | Média, posição e total da turma no período | coluna `B9` da BASE, filtrada pela turma |
| B31 | Último lançamento | `BASE FREQUÊNCIA!B2` |
| B32:K32 | Cadastro do aluno (ALUNOS A:J) | FILTER por matrícula |
| B33 | Turno | 1º turno em `REGISTROS!I` |
| B34 | Mês do calendário | 1º dia do mês do último lançamento no período |
| B35–B38 | Parcela atual: nome, início, fim, faltas h/a | `CRONOGRAMA` contendo `B31`; SUMIFS em `REGISTROS` |

## CALC_DASH — blocos

| Faixa | Conteúdo | Usado por |
|---|---|---|
| `M2:M` | Lista de alunos vinculada a turma + status | validação de `F5` |
| `N2:N` | "Todas" + disciplinas do aluno no período | validação de `L5` |
| `P2:W` | Lançamentos do aluno no período (Data, Disciplina, Aulas, Situação, Impacto, Doc, Status justif., Obs.) | KPIs, calendário, ocorrências |
| `Y1:AB` | Parcela × aluno × média da turma × meta (só parcelas iniciadas) | gráfico de linha |
| `AD1:AG` | Mês × presenças × faltas × abonos | colunas empilhadas |
| `AI1:AJ` | Situação × dias | rosca |
| `AL2:AP7` | Datas do calendário (seg–sex, 6 semanas) | `DASHBOARD!B42` |
| `AL10:AP15` | Código da situação de cada data (`PARÂMETROS!A7:B15`) | `DASHBOARD!B42` |
| `AR2:AV25` | Aptidão nas 24 parcelas | `DASHBOARD!B56` |

## DASHBOARD DO ALUNO — layout (B:M, 12 colunas de 108 px)

| Linhas | Bloco |
|---|---|
| 1–2 | Título e subtítulo |
| 4–6 | Filtros: B5 Turma, D5 Status, F5 Aluno, J5 Período, L5 Disciplina; C6/E6 intervalo; F6 aviso |
| 8–10 | Nome e ficha do aluno |
| 12–19 | Indicadores em duas fileiras de 6 blocos (rótulo / valor / sublinha) |
| 21–38 | Gráfico de linha (B22) e colunas empilhadas (H22) |
| 40–47 | Calendário (B42, derramado em B42:F47) + legenda (G42:G47) · rosca (H41) |
| 54–79 | Aptidão por parcela (B56, derramado) |
| 54–140 | Ocorrências do período (H56, derramado) |

## Convenções e armadilhas

- **Localidade pt_BR.** Os nomes das funções ficam em inglês, mas o separador é `;`. Literais de matriz `{a;b}` são evitados; use `HSTACK`/`VSTACK`.
- **ARRAYFORMULA em LET.** Comparações de intervalo dentro de `LET` (por exemplo, `ini<=$B$31`) precisam estar envolvidas em `ARRAYFORMULA`; sem isso retornam `#N/A`.
- **Formatação condicional não referencia outra aba.** Por isso as regras que comparam com a meta usam `INDIRECT("CALC_DASH!B11")`.
- **Matrícula como texto.** `REGISTROS!D` e `ALUNOS!B` misturam número e texto. As comparações usam `TO_TEXT(...)` dos dois lados.
- **Proteção** é só de aviso (`warningOnly`). Ela não impede a edição; serve para evitar sobrescrita acidental.

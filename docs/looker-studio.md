# Guia de montagem no Looker Studio

Este guia monta o dashboard individual de frequência no **Looker Studio**. Lá, os filtros
funcionam para usuários com acesso só de leitura, e cada pessoa tem a própria seleção.

Tempo estimado: 30 a 40 minutos. Faça a montagem com a conta dona da planilha de frequência.

## 1. As fontes de dados

A planilha tem duas abas preparadas para o Looker Studio. As duas são preenchidas por
fórmula, então não precisam de manutenção. **Não edite essas abas.**

| Aba | Uma linha por | Usar para |
|---|---|---|
| `LS_REGISTROS` | lançamento de `REGISTROS` | indicadores do período, gráfico mensal, calendário, ocorrências |
| `LS_PARCELAS` | aluno × parcela já iniciada | frequência oficial, aptidão, valor apto, média e posição na turma |

`LS_PARCELAS` traz a frequência e a aptidão **oficiais**, copiadas da `BASE FREQUÊNCIA`.
Para aptidão e valor, use sempre essa aba. A aptidão já leva em conta bloqueios que não
aparecem só pela frequência: um aluno desistente pode ter 100% na parcela e estar "Não Apto".

**Conferência feita em 29/10/2026.** Recalculei a frequência pelos lançamentos e comparei
com a `BASE FREQUÊNCIA`: 232 das 240 combinações de aluno e parcela bateram exatamente.
As 8 restantes são de alunos que deixaram de frequentar ou desistiram, na parcela do
desligamento. A base deixa a frequência em branco e o cálculo pelos lançamentos dá 0%,
porque os únicos dias letivos registrados foram faltas.

### Criar as fontes

1. Acesse [lookerstudio.google.com](https://lookerstudio.google.com), clique em **Criar → Fonte de dados** e escolha o conector **Planilhas Google**.
2. Selecione a planilha de frequência e a aba **LS_REGISTROS**. Deixe marcado **Usar a primeira linha como cabeçalhos** e clique em **Conectar**.
3. Revise os tipos dos campos conforme a tabela abaixo, renomeie a fonte para `LS_REGISTROS` e clique em **Criar relatório**.
4. No relatório, use **Recurso → Gerenciar fontes de dados adicionadas → Adicionar uma fonte de dados** e repita o processo com a aba **LS_PARCELAS**.

Em **Recurso → Gerenciar fontes de dados → Editar**, ajuste a **Atualização dos dados** das duas fontes para **15 minutos**.

### Tipos de campo

**LS_REGISTROS**

| Campo | Tipo | Agregação |
|---|---|---|
| DATA | Data (AAAAMMDD) | — |
| Nº PARCELA | Número | Nenhuma |
| MATRÍCULA | **Texto** (troque de Número para Texto) | — |
| AULAS, HA LETIVA, HA FALTA, PRESENÇA, FALTA, ABONO, BLOQUEIO | Número | Soma |
| demais | Texto | — |

**LS_PARCELAS**

| Campo | Tipo | Agregação |
|---|---|---|
| MATRÍCULA | **Texto** | — |
| Nº PARCELA, POSIÇÃO NA TURMA | Número | Nenhuma |
| INÍCIO, FIM, ÚLTIMO LANÇAMENTO | Data | — |
| FREQUÊNCIA, MÉDIA DA TURMA, META | Percentual | Média |
| APTO | Número | Soma |
| VALOR APTO | Moeda (BRL) | Soma |
| demais | Texto | — |

### Campos calculados

Crie-os em **Editar fonte de dados → Adicionar um campo**.

**Em LS_REGISTROS**

| Nome | Fórmula | Tipo |
|---|---|---|
| Frequência no período | `1 - SUM(HA FALTA) / SUM(HA LETIVA)` | Percentual |
| Dias lançados | `SUM(PRESENÇA) + SUM(FALTA) + SUM(ABONO)` | Número |
| Situação da meta | `CASE WHEN 1 - SUM(HA FALTA) / SUM(HA LETIVA) < 0.75 THEN "Abaixo da meta" WHEN 1 - SUM(HA FALTA) / SUM(HA LETIVA) < 0.80 THEN "Em risco" ELSE "Atingida" END` | Texto |
| Mês | `DATETIME_TRUNC(DATA, MONTH)` | Data (Ano/Mês) |
| É ocorrência | `CASE WHEN IMPACTO IN ("Computa Presença", "Dia Não Letivo") THEN "Não" ELSE "Sim" END` | Texto |

O limite de "Em risco" (80%) é a meta mais a margem definida em `BASE FREQUÊNCIA!BL2`, hoje 5 p.p. Se a margem mudar, atualize o 0.80.

**Em LS_PARCELAS**

| Nome | Fórmula | Tipo |
|---|---|---|
| Parcelas aptas (apuradas) | `SUM(CASE WHEN PARCELA EM CURSO = "Não" THEN APTO ELSE 0 END)` | Número |
| Parcelas apuradas | `SUM(CASE WHEN PARCELA EM CURSO = "Não" THEN 1 ELSE 0 END)` | Número |
| Valor apto (apuradas) | `SUM(CASE WHEN PARCELA EM CURSO = "Não" THEN VALOR APTO ELSE 0 END)` | Moeda (BRL) |

## 2. Layout da página

Use **Tema e layout → Tema**: fundo branco, cor principal `#1E3A8A`, fonte **Inter**.
Tamanho da tela: **Personalizado, 1200 × 1800**.

```
┌──────────────────────────────────────────────────────────────────────┐
│ DASHBOARD INDIVIDUAL DE FREQUÊNCIA                (texto, 24 px)     │
│ [TURMA ▾] [STATUS ATUAL ▾] [ALUNO ▾────────] [PARCELA ▾] [Período] │
├──────────────────────────────────────────────────────────────────────┤
│ Freq. no período │ Presenças │ Faltas │ Abonos │ Situação │ Dias     │
│ Parcelas aptas   │ Valor apto │ Média da turma │ Último lançamento   │
├──────────────────────────────────┬───────────────────────────────────┤
│ Frequência por parcela (linha)   │ Presenças/faltas/abonos por mês   │
├──────────────────────────────────┼───────────────────────────────────┤
│ Aptidão por parcela (tabela)     │ Distribuição das situações (rosca)│
├──────────────────────────────────┴───────────────────────────────────┤
│ Ocorrências do período (tabela)                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 3. Filtros vinculados

Crie os controles em **Adicionar um controle → Lista suspensa**, todos com a fonte **LS_REGISTROS**:

| Controle | Campo de controle | Configuração |
|---|---|---|
| Turma | TURMA | Seleção única; padrão "Turma A" |
| Status | STATUS ATUAL | Seleção múltipla; padrão "Matriculado" |
| Aluno | ALUNO | **Seleção única**; pesquisa ativada |
| Parcela | PARCELA | Seleção múltipla; ordenar por Nº PARCELA, crescente |
| Período | — | Use **Controle de período** (filtra pela DATA); padrão "Automático" |

**A cascata é automática.** Controles da mesma fonte de dados filtram uns aos outros:
escolhida a turma, a lista de alunos mostra só os alunos dela.

**Filtrar a outra fonte.** Os controles também filtram os gráficos da `LS_PARCELAS`,
porque os campos têm o mesmo nome e tipo nas duas abas (TURMA, STATUS ATUAL, ALUNO,
MATRÍCULA, PARCELA). **Teste depois de montar:** troque o aluno e confira se a tabela de
aptidão muda. Se não mudar, ajuste o tipo do campo (MATRÍCULA como Texto nas duas
fontes, por exemplo) ou monte a tabela a partir de uma **combinação de dados**
(LS_PARCELAS + LS_REGISTROS, unida por MATRÍCULA).

## 4. Componentes

### Indicadores (Visão geral)

Fonte LS_REGISTROS, exceto quando indicado:

| Visão geral | Métrica | Observação |
|---|---|---|
| Frequência no período | Frequência no período | Formatação condicional: vermelho se < 75% |
| Presenças | PRESENÇA (Soma) | |
| Faltas não justificadas | FALTA (Soma) | |
| Abonos | ABONO (Soma) | |
| Dias lançados | Dias lançados | |
| Situação da meta | Tabela 1×1 com a métrica Situação da meta | Visão geral não exibe texto |
| Parcelas aptas | Parcelas aptas (apuradas) | Fonte LS_PARCELAS |
| Valor apto acumulado | Valor apto (apuradas) | Fonte LS_PARCELAS |
| Último lançamento | MAX(DATA) | |

### Gráficos

| Componente | Fonte | Configuração |
|---|---|---|
| Frequência por parcela | LS_PARCELAS | **Gráfico de linhas.** Dimensão: PARCELA (ordenar por Nº PARCELA). Métricas: FREQUÊNCIA, MÉDIA DA TURMA, META (linha tracejada vermelha). Eixo Y de 0 a 100% |
| Presenças, faltas e abonos por mês | LS_REGISTROS | **Colunas empilhadas.** Dimensão: Mês. Métricas: PRESENÇA, FALTA, ABONO. Cores verde `#16A34A`, vermelho `#DC2626` e âmbar `#F59E0B` |
| Distribuição das situações | LS_REGISTROS | **Rosca.** Dimensão: SITUAÇÃO. Métrica: contagem de registros. Filtro: excluir IMPACTO = "Dia Não Letivo" |
| Aptidão por parcela | LS_PARCELAS | **Tabela.** Dimensões: PARCELA, INÍCIO, FIM, APTIDÃO, PARCELA EM CURSO. Métricas: FREQUÊNCIA, MÉDIA DA TURMA. Formatação condicional em APTIDÃO: Apto em verde, Não Apto em vermelho |
| Ocorrências do período | LS_REGISTROS | **Tabela.** Dimensões: DATA, SITUAÇÃO, DISCIPLINA, Nº DOC, STATUS JUSTIFICATIVA, OBSERVAÇÕES. Filtro: É ocorrência = "Sim". Ordenar por DATA, decrescente |
| Calendário (opcional) | LS_REGISTROS | **Tabela dinâmica.** Linhas: semana (`WEEK(DATA)`). Colunas: dia da semana (`WEEKDAY(DATA)`). Métrica: `MAX(CÓDIGO)`, com formatação condicional por código |

**Período e aptidão.** O controle de período não deve cortar as parcelas. Nos componentes
da `LS_PARCELAS`, abra **Configurar → Período padrão → Personalizado** e marque um
intervalo que cubra o curso inteiro, de 27/07/2026 a 31/07/2028.

## 5. Compartilhamento

1. Clique em **Compartilhar → Convidar pessoas** e adicione os mesmos usuários da planilha como **Leitor**. **Não use "Qualquer pessoa com o link"**: o relatório mostra dados pessoais de alunos.
2. Nas duas fontes de dados, em **Credenciais**, mantenha **Credenciais do proprietário**. Assim, os leitores veem os dados sem precisar de outro acesso.
3. Em **Compartilhar → Configurações**, ative **Desativar download, impressão e cópia para leitores** se preferir que ninguém exporte os dados. Avalie conforme a LGPD e a política da instituição.

## 6. Checklist de validação

- [ ] Com "Turma B", a lista de alunos mostra só alunos da Turma B
- [ ] Com Status "Deixou de Frequentar", só aparecem esses alunos
- [ ] Para um aluno, a Frequência no período com "Curso completo" (sem filtro de parcela) é igual à coluna **Curso completo** da `BASE FREQUÊNCIA`
- [ ] Parcelas aptas e valor apto batem com o relatório de pagamento
- [ ] A tabela de aptidão muda ao trocar o aluno (filtro entre as duas fontes)
- [ ] Um usuário Leitor da planilha consegue abrir o relatório e trocar o aluno

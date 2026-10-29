# Plano e decisões

## Objetivo

Criar um dashboard interativo para análise individual dos alunos das Turmas A e B.
Os filtros devem ser vinculados: ao escolher uma turma, a lista de alunos mostra
só os alunos daquela turma.

## Decisões

| Tema | Decisão | Motivo |
|---|---|---|
| Tecnologia | Fórmulas + validação de dados + gráficos nativos, sem Apps Script | Funciona para todos os usuários sem autorização de script; nada para manter fora da planilha |
| Filtros em cascata | Listas suspensas `ONE_OF_RANGE` apontando para `FILTER` dinâmico | Segmentações (slicers) do Sheets não fazem cascata |
| Status padrão | "Matriculado", com opção "Todos" | Foco em quem ainda recebe o auxílio |
| Fonte da frequência | `BASE FREQUÊNCIA` (mesma dos relatórios oficiais) | O painel não pode divergir do pagamento |
| Cálculos | Aba oculta `CALC_DASH` | Dashboard limpo; fórmulas auditáveis num só lugar |
| Margem de faltas | Calculada na parcela atual, não no curso todo | No curso completo (111 dias) a margem era grande demais para orientar o aluno |
| Acesso da equipe | Relatório no Looker Studio sobre abas de dados geradas por fórmula | Todos os usuários têm acesso só de leitura, e os filtros da planilha exigem edição; o Looker dá seleção individual sem mudar permissões |
| Visual | Mesma paleta e fonte (Inter) da planilha de pagamentos | Consistência entre as planilhas da coordenação |

## Etapas

- [x] Análise completa da planilha (registros, relatórios, bases auxiliares)
- [x] Lote 1: criação das abas e de todas as fórmulas
- [x] Validação dos números contra a `BASE FREQUÊNCIA`. Exemplo: aluno de teste com 60 dias, 50 presenças, 8 faltas, 2 abonos, 86,7% e 4/4 parcelas aptas, idêntico à base.
- [x] Lote 2: formatação, filtros vinculados, formatação condicional, proteção
- [x] Lote 3: gráficos (linha, colunas empilhadas, rosca)
- [x] Teste da cascata: com "Turma B", a lista mostra só alunos da Turma B, e o aluno da Turma A fica marcado como inválido, com aviso
- [x] Publicação no GitHub e no GitHub Pages
- [x] Abas de dados do Looker Studio (`LS_REGISTROS`, `LS_PARCELAS`). Conferência dos 60 alunos: 232 de 240 combinações de aluno e parcela idênticas à `BASE FREQUÊNCIA`; as 8 restantes são parcelas de desligamento (base em branco, cálculo pelos lançamentos = 0%)
- [ ] Montagem do relatório no Looker Studio (manual, ver [guia](looker-studio.md))

## Pendências e melhorias possíveis

- **Qualidade dos dados** (fora do painel, na planilha de origem):
  - preencher a disciplina em `REGISTROS!H`; cerca de 45% dos lançamentos têm disciplina, e nenhum de outubro;
  - completar as 20 datas com lançamentos parciais e o dia útil sem nenhum registro;
  - corrigir a célula de STATUS JUSTIFICATIVA que contém uma data;
  - ajustar a `AUDITORIA`, que conta as 104 linhas de Feriado como erro.
- **Opcional:** gatilho `onEdit` em Apps Script para limpar `F5` ao trocar a turma ou o status.
- **Opcional:** visão comparativa da turma (ranking e alunos em risco) numa segunda aba.

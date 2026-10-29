"""Gera os lotes de requisições (Sheets API batchUpdate) do DASHBOARD DO ALUNO.

Uso:  python3 build/layout.py <lote>   ->  imprime o JSON do lote (estrutura | formato | graficos)

Nenhum dado de aluno fica neste arquivo: só estrutura, fórmulas e formatação.
As fórmulas usam o separador ';' (planilha em pt_BR).
"""
import json
import sys

DASH, CALC = 910010, 910011
DN, CN = "'DASHBOARD DO ALUNO'", "CALC_DASH"
D = lambda a1: f"{DN}!{a1}"          # referência ao dashboard
BF = "'BASE FREQUÊNCIA'"
CR = "'CRONOGRAMA DE PAGAMENTOS'"

# ---------- paleta (mesma da planilha de pagamentos) ----------
NAVY, INK, TEXT, MUTED, LINE = "#1E3A8A", "#0F172A", "#334155", "#64748B", "#E2E8F0"
SURF, HEAD, WHITE = "#F8FAFC", "#F1F5F9", "#FFFFFF"
GREEN, GREEN_BG, RED, RED_BG = "#15803D", "#DCFCE7", "#B91C1C", "#FEE2E2"
AMBER, AMBER_BG, BLUE_BG, GRAY_BG, PURPLE, PURPLE_BG = "#B45309", "#FEF3C7", "#DBEAFE", "#E5E7EB", "#6D28D9", "#EDE9FE"
FONT = "Inter"


def C(h):
    h = h.lstrip("#")
    return {"rgbColor": {k: round(int(h[i:i + 2], 16) / 255, 3) for k, i in (("red", 0), ("green", 2), ("blue", 4))}}


def col(a):  # 'AB' -> 27
    n = 0
    for ch in a:
        n = n * 26 + ord(ch) - 64
    return n - 1


def cell_ref(a1):
    letters = "".join(c for c in a1 if c.isalpha())
    return int(a1[len(letters):]) - 1, col(letters)


def G(sid, a1):
    """'B5:C6' -> GridRange (0-based, fim exclusivo)."""
    a, _, b = a1.partition(":")
    r0, c0 = cell_ref(a)
    r1, c1 = cell_ref(b or a)
    return {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1 + 1, "startColumnIndex": c0, "endColumnIndex": c1 + 1}


def val(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return {"numberValue": v}
    if isinstance(v, str) and v.startswith("="):
        return {"formulaValue": v}
    return {"stringValue": v}


def put(sid, a1, v):
    r, c = cell_ref(a1)
    return {"updateCells": {"start": {"sheetId": sid, "rowIndex": r, "columnIndex": c},
                            "rows": [{"values": [{"userEnteredValue": val(v)}]}], "fields": "userEnteredValue"}}


def put_row(sid, a1, values):
    r, c = cell_ref(a1)
    return {"updateCells": {"start": {"sheetId": sid, "rowIndex": r, "columnIndex": c},
                            "rows": [{"values": [{"userEnteredValue": val(v)} if v is not None else {} for v in values]}],
                            "fields": "userEnteredValue"}}


def put_col(sid, a1, values):
    r, c = cell_ref(a1)
    return {"updateCells": {"start": {"sheetId": sid, "rowIndex": r, "columnIndex": c},
                            "rows": [{"values": [{"userEnteredValue": val(v)}]} for v in values], "fields": "userEnteredValue"}}


# =====================================================================
# CALC_DASH — chaves (coluna A/B) e blocos auxiliares
# =====================================================================
REG = lambda c: f"REGISTROS!${c}$3:${c}"
MAT_TXT = "ARRAYFORMULA(TO_TEXT(REGISTROS!$D$3:$D))"

CALC_KEYS = [
    ("Aluno selecionado", f"={D('$F$5')}"),
    ("Aluno válido p/ filtros", "=AND($B$2<>\"\";COUNTIF($M$2:$M$300;$B$2)>0)"),
    ("Matrícula", "=IF($B$3;REGEXEXTRACT($B$2;\"(\\d+)\\s*$\");\"\")"),
    ("Início do período", f"=LET(p;{D('$J$5')};IFS(p=\"Curso completo\";{BF}!$AE$2;p=\"Intervalo personalizado\";IF(AND(ISNUMBER({D('$C$6')});ISNUMBER({D('$E$6')});{D('$C$6')}<={D('$E$6')});{D('$C$6')};\"\");TRUE;IFERROR(XLOOKUP(p;{CR}!$C$8:$C$31;{CR}!$D$8:$D$31);\"\")))"),
    ("Fim do período", f"=LET(p;{D('$J$5')};IFS(p=\"Curso completo\";{BF}!$AE$3;p=\"Intervalo personalizado\";IF(AND(ISNUMBER({D('$C$6')});ISNUMBER({D('$E$6')});{D('$C$6')}<={D('$E$6')});{D('$E$6')};\"\");TRUE;IFERROR(XLOOKUP(p;{CR}!$C$8:$C$31;{CR}!$E$8:$E$31);\"\")))"),
    ("Disciplina", f"=IF(OR({D('$L$5')}=\"\";{D('$L$5')}=\"Todas\");\"Todas\";{D('$L$5')})"),
    ("Linha na BASE FREQUÊNCIA", f"=IF($B$4=\"\";\"\";IFERROR(MATCH($B$4;ARRAYFORMULA(TO_TEXT({BF}!$A$5:$A$204));0);\"\"))"),
    ("Coluna do período na BASE", f"=IFERROR(MATCH({D('$J$5')};{BF}!$G$4:$AE$4;0);\"\")"),
    ("Turma do aluno", "=IF($B$4=\"\";\"\";$G$32)"),
    ("Meta", "='PARÂMETROS'!$B$2"),
    ("H/A por dia", "='PARÂMETROS'!$B$5"),
    ("Valor da parcela", "='PARÂMETROS'!$B$4"),
    ("Total h/a no período", "=SUMIFS($R$2:$R;$T$2:$T;\"<>Dia Não Letivo\";$P$2:$P;\"<>\")"),
    ("Faltas h/a", "=SUMIFS($R$2:$R;$T$2:$T;\"Computa Falta\")"),
    ("Frequência", "=IF($B$14>0;($B$14-$B$15)/$B$14;\"\")"),
    ("Dias lançados", "=COUNTIFS($P$2:$P;\"<>\";$S$2:$S;\"<>\";$T$2:$T;\"<>Dia Não Letivo\")"),
    ("Presenças", "=COUNTIF($T$2:$T;\"Computa Presença\")"),
    ("Faltas", "=COUNTIF($T$2:$T;\"Computa Falta\")"),
    ("Abonos", "=COUNTIF($T$2:$T;\"Justificada*\")"),
    ("Bloqueio / evasão", "=COUNTIF($T$2:$T;\"Bloqueio de Benefício\")+COUNTIF($T$2:$T;\"Cancelamento\")"),
    ("Situação da meta", f"=IF($B$16=\"\";\"Sem registros\";IF($B$16<$B$11;\"Abaixo da meta\";IF($B$16<$B$11+{BF}!$BL$2;\"Em risco\";\"Atingida\")))"),
    ("Dias letivos previstos na parcela atual", "=IF($B$35=\"\";\"\";NETWORKDAYS($B$36;$B$37;FILTER(FERIADOS!$A$2:$A;FERIADOS!$E$2:$E=\"Não\")))"),
    ("Margem de faltas na parcela atual (dias)", "=IF(OR($B$23=\"\";$B$4=\"\");\"\";MAX(0;ROUNDDOWN(($B$23*$B$12*(1-$B$11)-$B$38)/$B$12;0)))"),
    ("Parcelas aptas", f"=IF($B$8=\"\";\"\";COUNTIF(INDEX({BF}!$AF$5:$BC$204;$B$8;0);\"Apto\"))"),
    ("Parcelas apuradas", f"=IF($B$8=\"\";\"\";COUNTIF(INDEX({BF}!$AF$5:$BC$204;$B$8;0);\"<>Aguardando\"))"),
    ("Valor apto", "=IF($B$25=\"\";\"\";$B$25*$B$13)"),
    ("Média da turma no período", f"=IF(OR($B$9=\"\";$B$10=\"\");\"\";IFERROR(AVERAGEIFS(INDEX({BF}!$G$5:$AE$204;0;$B$9);{BF}!$D$5:$D$204;$B$10);\"\"))"),
    ("Posição na turma", f"=IF(OR($B$8=\"\";$B$9=\"\";$B$10=\"\");\"\";LET(c;INDEX({BF}!$G$5:$AE$204;0;$B$9);f;INDEX(c;$B$8);IF(NOT(ISNUMBER(f));\"\";COUNTIFS(c;\">\"&f;{BF}!$D$5:$D$204;$B$10)+1)))"),
    ("Alunos da turma com frequência", f"=IF(OR($B$9=\"\";$B$10=\"\");\"\";COUNTIFS({BF}!$D$5:$D$204;$B$10;INDEX({BF}!$G$5:$AE$204;0;$B$9);\">=0\"))"),
    ("Último lançamento", f"={BF}!$B$2"),
]
# linha 32: cadastro (B32:K32) | 33: turno | 34: mês do calendário
CALC_EXTRA = [
    ("A32", "Cadastro (ALUNOS A:J)"),
    ("B32", "=IF($B$4=\"\";\"\";IFERROR(FILTER(ALUNOS!$A$2:$J;ARRAYFORMULA(TO_TEXT(ALUNOS!$B$2:$B))=$B$4);\"\"))"),
    ("A33", "Turno"),
    ("B33", f"=IF($B$4=\"\";\"\";IFERROR(INDEX(FILTER({REG('I')};{MAT_TXT}=$B$4;{REG('I')}<>\"\");1);\"\"))"),
    ("A34", "Mês do calendário"),
    ("B34", "=IF(COUNT($P$2:$P)=0;\"\";EOMONTH(MAX($P$2:$P);-1)+1)"),
    ("A35", "Parcela atual (contém o último lançamento)"),
    ("B35", f"=IFERROR(ARRAYFORMULA(XLOOKUP(1;({CR}!$D$8:$D$31<=$B$31)*({CR}!$E$8:$E$31>=$B$31);{CR}!$C$8:$C$31));\"\")"),
    ("A36", "Início da parcela atual"),
    ("B36", f"=IF($B$35=\"\";\"\";XLOOKUP($B$35;{CR}!$C$8:$C$31;{CR}!$D$8:$D$31))"),
    ("A37", "Fim da parcela atual"),
    ("B37", f"=IF($B$35=\"\";\"\";XLOOKUP($B$35;{CR}!$C$8:$C$31;{CR}!$E$8:$E$31))"),
    ("A38", "Faltas h/a na parcela atual"),
    ("B38", "=IF(OR($B$4=\"\";$B$35=\"\");\"\";SUMIFS(REGISTROS!$J$3:$J;REGISTROS!$D$3:$D;$B$4;REGISTROS!$B$3:$B;\">=\"&$B$36;REGISTROS!$B$3:$B;\"<=\"&$B$37;REGISTROS!$L$3:$L;\"Computa Falta\"))"),
]

CALC_BLOCKS = {
    # lista de alunos vinculada a turma + status (validação do campo ALUNO)
    "M1": "LISTA ALUNOS",
    "M2": f"=LET(t;{D('$B$5')};s;{D('$D$5')};x;FILTER(ALUNOS!$B$2:$C;ALUNOS!$B$2:$B<>\"\";((t=\"Todas as Turmas\")+(t=\"\")+(ALUNOS!$F$2:$F=t))>0;((s=\"Todos\")+(s=\"\")+(ALUNOS!$H$2:$H=s))>0);IFERROR(BYROW(SORT(x;2;TRUE);LAMBDA(r;INDEX(r;1;2)&\" — \"&INDEX(r;1;1)));\"(nenhum aluno)\"))",
    # disciplinas do aluno no período
    "N1": "LISTA DISCIPLINAS",
    "N2": f"=IF(OR($B$4=\"\";$B$5=\"\";$B$6=\"\");\"Todas\";IFERROR(VSTACK(\"Todas\";SORT(UNIQUE(FILTER({REG('H')};{MAT_TXT}=$B$4;{REG('H')}<>\"\";{REG('B')}>=$B$5;{REG('B')}<=$B$6))));\"Todas\"))",
    # registros do aluno no período (cache usado por todos os indicadores)
    "P1": "DATA", "Q1": "DISCIPLINA", "R1": "AULAS", "S1": "SITUAÇÃO", "T1": "IMPACTO", "U1": "Nº DOC", "V1": "STATUS JUSTIF.", "W1": "OBSERVAÇÕES",
    "P2": f"=IF(OR($B$4=\"\";$B$5=\"\";$B$6=\"\");\"\";IFERROR(SORT(FILTER(HSTACK({REG('B')};{REG('H')};{REG('J')};{REG('K')};{REG('L')};{REG('M')};{REG('N')};{REG('Q')});{MAT_TXT}=$B$4;{REG('B')}>=$B$5;{REG('B')}<=$B$6;(($B$7=\"Todas\")+({REG('H')}=$B$7))>0);1;TRUE);\"\"))",
    # série por parcela (gráfico de linha)
    "Y1": "Parcela", "Z1": "Aluno", "AA1": "Média da turma", "AB1": "Meta 75%",
    "Y2": f"=IF($B$8=\"\";\"\";ARRAYFORMULA(LET(lab;{BF}!$G$4:$AD$4;ini;{BF}!$G$2:$AD$2;f;INDEX({BF}!$G$5:$AD$204;$B$8;0);med;MAP(SEQUENCE(1;24);LAMBDA(i;IFERROR(AVERAGEIFS(INDEX({BF}!$G$5:$AD$204;0;i);{BF}!$D$5:$D$204;$B$10);\"\")));ok;ini<=$B$31;TRANSPOSE(FILTER(VSTACK(lab;f;med;IF(ok;$B$11;\"\"));ok)))))",
    # série mensal (colunas empilhadas)
    "AD1": "Mês", "AE1": "Presenças", "AF1": "Faltas", "AG1": "Abonos",
    "AD2": "=IF(COUNT($P$2:$P)=0;\"\";LET(d;FILTER($P$2:$P;$P$2:$P<>\"\");m;UNIQUE(ARRAYFORMULA(EOMONTH(d;-1)+1));HSTACK(ARRAYFORMULA(TEXT(m;\"mmm/yy\"));MAP(m;LAMBDA(x;COUNTIFS($P$2:$P;\">=\"&x;$P$2:$P;\"<=\"&EOMONTH(x;0);$T$2:$T;\"Computa Presença\")));MAP(m;LAMBDA(x;COUNTIFS($P$2:$P;\">=\"&x;$P$2:$P;\"<=\"&EOMONTH(x;0);$T$2:$T;\"Computa Falta\")));MAP(m;LAMBDA(x;COUNTIFS($P$2:$P;\">=\"&x;$P$2:$P;\"<=\"&EOMONTH(x;0);$T$2:$T;\"Justificada*\"))))))",
    # distribuição das situações (rosca)
    "AI1": "Situação", "AJ1": "Dias",
    "AI2": "=IF(COUNT($P$2:$P)=0;\"\";LET(s;FILTER($S$2:$S;$S$2:$S<>\"\";$T$2:$T<>\"Dia Não Letivo\");u;UNIQUE(s);SORT(HSTACK(u;MAP(u;LAMBDA(x;COUNTIF(s;x))));2;FALSE)))",
    # calendário: datas (AL2:AP7) e códigos (AL10:AP15)
    "AL1": "CALENDÁRIO — DATAS (SEG–SEX)",
    "AL2": "=IF($B$34=\"\";\"\";LET(m;$B$34;st;m-WEEKDAY(m;2)+1;MAKEARRAY(6;5;LAMBDA(w;d;LET(dt;st+(w-1)*7+(d-1);IF(MONTH(dt)=MONTH(m);dt;\"\"))))))",
    "AL9": "CALENDÁRIO — CÓDIGOS",
    "AL10": "=IF($B$34=\"\";\"\";MAP($AL$2:$AP$7;LAMBDA(dt;IF(dt=\"\";\"\";LET(s;IFERROR(XLOOKUP(dt;$P$2:$P;$S$2:$S);\"\");IF(s=\"\";\"—\";IFERROR(XLOOKUP(s;'PARÂMETROS'!$B$7:$B$15;'PARÂMETROS'!$A$7:$A$15);s)))))))",
    # aptidão nas 24 parcelas
    "AR1": "PARCELA", "AS1": "PERÍODO", "AT1": "FREQ. ALUNO", "AU1": "MÉDIA TURMA", "AV1": "APTIDÃO",
    "AR2": f"=IF($B$8=\"\";\"\";LET(i;SEQUENCE(24);HSTACK(TRANSPOSE({BF}!$G$4:$AD$4);MAP(i;LAMBDA(k;TEXT(INDEX({BF}!$G$2:$AD$2;1;k);\"dd/mm/yy\")&\" a \"&TEXT(INDEX({BF}!$G$3:$AD$3;1;k);\"dd/mm/yy\")));TRANSPOSE(INDEX({BF}!$G$5:$AD$204;$B$8;0));MAP(i;LAMBDA(k;IFERROR(AVERAGEIFS(INDEX({BF}!$G$5:$AD$204;0;k);{BF}!$D$5:$D$204;$B$10);\"\")));TRANSPOSE(INDEX({BF}!$AF$5:$BC$204;$B$8;0)))))",
}

# =====================================================================
# DASHBOARD DO ALUNO — textos e fórmulas visíveis
# =====================================================================
K = lambda a1: f"{CN}!${''.join(c for c in a1 if c.isalpha())}${''.join(c for c in a1 if c.isdigit())}"  # CALC_DASH!$B$16

TILES_1 = [  # (coluna inicial, rótulo, valor, sublinha)
    ("B", "FREQUÊNCIA NO PERÍODO", f"=IF({K('B16')}=\"\";\"—\";{K('B16')})",
     f"=IF({K('B16')}=\"\";\"Meta: \"&TEXT({K('B11')};\"0%\");\"Meta \"&TEXT({K('B11')};\"0%\")&\" • \"&TEXT(({K('B16')}-{K('B11')})*100;\"+0.0;-0.0\")&\" p.p.\")"),
    ("D", "PRESENÇAS", f"=IF({K('B4')}=\"\";\"—\";{K('B18')})", f"=\"de \"&{K('B17')}&\" dias lançados\""),
    ("F", "FALTAS NÃO JUSTIFICADAS", f"=IF({K('B4')}=\"\";\"—\";{K('B19')})", f"={K('B15')}&\" h/a descontadas\""),
    ("H", "ABONOS", f"=IF({K('B4')}=\"\";\"—\";{K('B20')})", "Faltas justificadas, atestados e dispensas"),
    ("J", "SITUAÇÃO DA META", f"=IF({K('B4')}=\"\";\"—\";{K('B22')})", f"=\"Em risco: até \"&TEXT({BF}!$BL$2*100;\"0\")&\" p.p. acima da meta\""),
    ("L", "MARGEM NA PARCELA ATUAL", f"=IF({K('B24')}=\"\";\"—\";{K('B24')})", f"=IF({K('B35')}=\"\";\"\";\"Faltas ainda possíveis em \"&{K('B35')}&\" (estim.)\")"),
]
TILES_2 = [
    ("B", "PARCELAS APTAS NO CURSO", f"=IF({K('B25')}=\"\";\"—\";{K('B25')}&\" de \"&{K('B26')})", "Parcelas já apuradas"),
    ("D", "VALOR APTO ACUMULADO", f"=IF({K('B27')}=\"\";\"—\";{K('B27')})", f"=\"R$ \"&TEXT({K('B13')};\"0\")&\" por parcela apta\""),
    ("F", "POSIÇÃO NA TURMA", f"=IF({K('B29')}=\"\";\"—\";{K('B29')}&\"º de \"&{K('B30')})", "Pela frequência no período"),
    ("H", "MÉDIA DA TURMA", f"=IF({K('B28')}=\"\";\"—\";{K('B28')})", f"=IF({K('B10')}=\"\";\"\";{K('B10')}&\" • mesmo período\")"),
    ("J", "BLOQUEIO / EVASÃO", f"=IF({K('B4')}=\"\";\"—\";{K('B21')})", "Dias como Deixou de Frequentar / Desistente"),
    ("L", "ÚLTIMO LANÇAMENTO", f"={K('B31')}", "Frequência lançada até esta data"),
]

AVISO = (f"=IF($F$5=\"\";\"Selecione a turma, o status e o aluno.\";IF(NOT({K('B3')});\"⚠ O aluno selecionado não pertence à turma / status filtrados. Escolha novamente na lista.\";"
         f"IF(OR({K('B5')}=\"\";{K('B6')}=\"\");\"⚠ Período inválido. Em intervalo personalizado, informe DE e ATÉ.\";"
         f"\"Período: \"&TEXT({K('B5')};\"dd/mm/yyyy\")&\" a \"&TEXT({K('B6')};\"dd/mm/yyyy\")&IF({K('B6')}>{K('B31')};\"  •  dados parciais: frequência lançada até \"&TEXT({K('B31')};\"dd/mm/yyyy\");\"\"))))")

DASH_CELLS = {
    "B1": "DASHBOARD INDIVIDUAL DE FREQUÊNCIA",
    "B2": "Curso Técnico em Enfermagem • ETSAL / UNCISAL • Turmas A e B — selecione turma, status e aluno; a lista de alunos acompanha os filtros.",
    "B4": "TURMA", "D4": "STATUS NO CURSO", "F4": "ALUNO", "J4": "PERÍODO", "L4": "DISCIPLINA / MÓDULO",
    "B5": "Turma A", "D5": "Matriculado", "J5": "Curso completo", "L5": "Todas",
    "B6": "DE", "D6": "ATÉ", "F6": AVISO,
    "B8": f"=IF({K('B4')}=\"\";\"Nenhum aluno selecionado\";{K('D32')})",
    "B9": "MATRÍCULA", "D9": "CÓDIGO", "F9": "TURMA • TURNO", "H9": "STATUS NO CURSO", "J9": "DATA DE INGRESSO", "L9": "E-MAIL",
    "B10": f"=IF({K('B4')}=\"\";\"—\";{K('B4')})",
    "D10": f"=IF({K('B4')}=\"\";\"—\";{K('B32')})",
    "F10": f"=IF({K('B4')}=\"\";\"—\";{K('G32')}&IF({K('B33')}=\"\";\"\";\" • \"&{K('B33')}))",
    "H10": f"=IF({K('B4')}=\"\";\"—\";{K('I32')})",
    "J10": f"=IF({K('B4')}=\"\";\"—\";{K('H32')})",
    "L10": f"=IF({K('B4')}=\"\";\"—\";{K('J32')})",
    "B12": "INDICADORES DO PERÍODO",
    "B21": "EVOLUÇÃO DA FREQUÊNCIA POR PARCELA", "H21": "PRESENÇAS, FALTAS E ABONOS POR MÊS",
    "B40": f"=\"CALENDÁRIO — \"&IF({K('B34')}=\"\";\"sem registros no período\";UPPER(TEXT({K('B34')};\"mmmm/yyyy\")))",
    "H40": "DISTRIBUIÇÃO DAS SITUAÇÕES NO PERÍODO",
    "B41": "SEG", "C41": "TER", "D41": "QUA", "E41": "QUI", "F41": "SEX", "G41": "LEGENDA",
    "B42": f"=IF({K('B34')}=\"\";\"\";MAP({CN}!$AL$2:$AP$7;{CN}!$AL$10:$AP$15;LAMBDA(dt;c;IF(dt=\"\";\"\";DAY(dt)&CHAR(10)&c))))",
    "B54": "APTIDÃO AO AUXÍLIO POR PARCELA", "H54": "OCORRÊNCIAS NO PERÍODO (FALTAS, ABONOS E BLOQUEIOS)",
    "B55": "PARCELA", "C55": "PERÍODO", "D55": "FREQ. ALUNO", "E55": "MÉDIA TURMA", "F55": "APTIDÃO",
    "B56": f"=ARRAYFORMULA(IF({K('B8')}=\"\";\"\";{CN}!$AR$2:$AV$25))",
    "H55": "DATA", "I55": "SITUAÇÃO", "J55": "DISCIPLINA", "K55": "Nº DOC", "L55": "STATUS JUSTIF.", "M55": "OBSERVAÇÕES",
    "H56": f"=IF(COUNT({CN}!$P$2:$P)=0;\"Selecione um aluno e um período com lançamentos.\";IFERROR(LET(c;FILTER({CN}!$P$2:$W;{CN}!$P$2:$P<>\"\";{CN}!$T$2:$T<>\"Computa Presença\";{CN}!$T$2:$T<>\"Dia Não Letivo\");SORT(CHOOSECOLS(c;1;4;2;6;7;8);1;FALSE));\"Nenhuma falta, abono ou ocorrência no período.\"))",
}
LEGEND = [("G42", "PRE  Presente"), ("G43", "FNJ / SUS  Falta"), ("G44", "FJU / ATE / DIS  Abono"),
          ("G45", "FER  Não letivo"), ("G46", "DEF / DES  Evasão"), ("G47", "—  Sem lançamento")]
for c, label, v, sub in TILES_1:
    DASH_CELLS[f"{c}13"], DASH_CELLS[f"{c}14"], DASH_CELLS[f"{c}15"] = label, v, sub
for c, label, v, sub in TILES_2:
    DASH_CELLS[f"{c}17"], DASH_CELLS[f"{c}18"], DASH_CELLS[f"{c}19"] = label, v, sub
DASH_CELLS.update(dict(LEGEND))


def grid(sid, cells):
    """Uma única updateCells cobrindo A1 até a última célula usada (células vazias ficam {})."""
    pos = {cell_ref(a1): v for a1, v in cells.items()}
    nr = max(r for r, _ in pos) + 1
    nc = max(c for _, c in pos) + 1
    rows = []
    for r in range(nr):
        vals = [{"userEnteredValue": val(pos[(r, c)])} if (r, c) in pos else {} for c in range(nc)]
        while vals and vals[-1] == {}:
            vals.pop()
        rows.append({"values": vals})
    return {"updateCells": {"start": {"sheetId": sid, "rowIndex": 0, "columnIndex": 0}, "rows": rows, "fields": "userEnteredValue"}}


def calc_cells():
    cells = {"A1": "CHAVE", "B1": "VALOR"}
    for i, (k, v) in enumerate(CALC_KEYS, start=2):
        cells[f"A{i}"], cells[f"B{i}"] = k, v
    cells.update(dict(CALC_EXTRA))
    cells.update(CALC_BLOCKS)
    return cells


def lote_estrutura():
    reqs = [
        {"addSheet": {"properties": {"sheetId": DASH, "title": "DASHBOARD DO ALUNO", "index": 0,
                                     "gridProperties": {"rowCount": 140, "columnCount": 14, "frozenRowCount": 6, "hideGridlines": True},
                                     "tabColorStyle": C(NAVY)}}},
        {"addSheet": {"properties": {"sheetId": CALC, "title": CN, "hidden": True,
                                     "gridProperties": {"rowCount": 1000, "columnCount": 52, "frozenRowCount": 1}}}},
    ]
    reqs += [grid(CALC, calc_cells()), grid(DASH, DASH_CELLS)]
    return reqs


# =====================================================================
# Formatação, filtros vinculados (validação), formatação condicional
# =====================================================================
def rc(rng, fmt, fields):
    return {"repeatCell": {"range": rng, "cell": {"userEnteredFormat": fmt}, "fields": ",".join("userEnteredFormat." + f for f in fields)}}


def txt(rng, fg=TEXT, size=10, bold=False, h=None, bg=None, wrap=None, italic=False):
    tf = {"fontFamily": FONT, "foregroundColorStyle": C(fg), "fontSize": size}
    if bold:
        tf["bold"] = True
    if italic:
        tf["italic"] = True
    fields = ["textFormat"]
    fmt = {"textFormat": tf}
    if h:
        fmt["horizontalAlignment"] = h; fields.append("horizontalAlignment")
    if bg:
        fmt["backgroundColorStyle"] = C(bg); fields.append("backgroundColorStyle")
    if wrap:
        fmt["wrapStrategy"] = wrap; fields.append("wrapStrategy")
    return rc(rng, fmt, fields)


def numfmt(rng, kind, pattern):
    return rc(rng, {"numberFormat": {"type": kind, "pattern": pattern}}, ["numberFormat"])


def border(rng, color, sides=("top", "bottom", "left", "right"), style="SOLID"):
    b = {"style": style, "colorStyle": C(color)}
    return {"updateBorders": {"range": rng, **{k: b for k in sides}}}


def merge(sid, a1):
    return {"mergeCells": {"range": G(sid, a1), "mergeType": "MERGE_ALL"}}


def width(sid, c0, c1, px):
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c0, "endIndex": c1}, "properties": {"pixelSize": px}, "fields": "pixelSize"}}


def height(sid, r0, r1, px):  # linhas 1-based inclusivas
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r0 - 1, "endIndex": r1}, "properties": {"pixelSize": px}, "fields": "pixelSize"}}


def dv_list(a1, items):
    return {"setDataValidation": {"range": G(DASH, a1), "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": i} for i in items]}, "strict": True, "showCustomUi": True}}}


def dv_range(a1, ref):
    return {"setDataValidation": {"range": G(DASH, a1), "rule": {"condition": {"type": "ONE_OF_RANGE", "values": [{"userEnteredValue": ref}]}, "strict": True, "showCustomUi": True}}}


def cf(a1, formula, fg=None, bg=None, bold=None, sid=DASH):
    fmt = {}
    if bg:
        fmt["backgroundColorStyle"] = C(bg)
    if fg or bold is not None:
        fmt["textFormat"] = {}
        if fg:
            fmt["textFormat"]["foregroundColorStyle"] = C(fg)
        if bold is not None:
            fmt["textFormat"]["bold"] = bold
    return {"addConditionalFormatRule": {"index": 0, "rule": {"ranges": [G(sid, a1)], "booleanRule": {
        "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]}, "format": fmt}}}}


PAIRS = ["B", "D", "F", "H", "J", "L"]
NEXT = {"B": "C", "D": "E", "F": "G", "H": "I", "J": "K", "L": "M"}


def lote_formato_partes():
    """Divide o lote de formatação em 3 chamadas menores (mesma ordem)."""
    reqs = lote_formato()
    n = len(reqs)
    return [reqs[: n // 3], reqs[n // 3: 2 * n // 3], reqs[2 * n // 3:]]


def lote_formato():
    R = lambda a1: G(DASH, a1)
    cells = dict(CALC_EXTRA)
    for i, (k, v) in enumerate(CALC_KEYS, start=2):
        if i in (23, 24):
            cells[f"A{i}"], cells[f"B{i}"] = k, v
    reqs = [put(CALC, a1, v) for a1, v in cells.items() if a1[1:] in ("23", "24", "35", "36", "37", "38")]
    reqs.append(put(CALC, "Y2", CALC_BLOCKS["Y2"]))
    reqs += [put(DASH, "L13", DASH_CELLS["L13"]), put(DASH, "L15", DASH_CELLS["L15"])]
    # formatos de número na CALC_DASH (alimentam os gráficos)
    reqs += [numfmt(G(CALC, "Z2:AB30"), "PERCENT", "0%"), numfmt(G(CALC, "AT2:AU30"), "PERCENT", "0.0%"),
             numfmt(G(CALC, "P2:P1000"), "DATE", "dd/mm/yyyy"), numfmt(G(CALC, "B5:B6"), "DATE", "dd/mm/yyyy"),
             numfmt(G(CALC, "B36:B37"), "DATE", "dd/mm/yyyy"), numfmt(G(CALC, "AL2:AP7"), "DATE", "dd/mm/yyyy")]
    # base da aba
    reqs += [width(DASH, 0, 1, 20), width(DASH, 1, 13, 108), width(DASH, 13, 14, 20),
             rc(R("A1:N140"), {"backgroundColorStyle": C(WHITE), "verticalAlignment": "MIDDLE",
                               "textFormat": {"fontFamily": FONT, "fontSize": 10, "foregroundColorStyle": C(TEXT)}},
                ["backgroundColorStyle", "verticalAlignment", "textFormat.fontFamily", "textFormat.fontSize", "textFormat.foregroundColorStyle"]),
             height(DASH, 1, 1, 44), height(DASH, 2, 2, 22), height(DASH, 3, 3, 10), height(DASH, 4, 4, 18), height(DASH, 5, 5, 34),
             height(DASH, 6, 6, 26), height(DASH, 7, 7, 12), height(DASH, 8, 8, 36), height(DASH, 9, 9, 18), height(DASH, 10, 10, 26),
             height(DASH, 11, 11, 14), height(DASH, 12, 12, 28), height(DASH, 13, 13, 22), height(DASH, 14, 14, 42), height(DASH, 15, 15, 22),
             height(DASH, 16, 16, 10), height(DASH, 17, 17, 22), height(DASH, 18, 18, 42), height(DASH, 19, 19, 22), height(DASH, 20, 20, 14),
             height(DASH, 21, 21, 28), height(DASH, 22, 38, 21), height(DASH, 39, 39, 14), height(DASH, 40, 40, 28), height(DASH, 41, 41, 20),
             height(DASH, 42, 47, 44), height(DASH, 48, 53, 21), height(DASH, 54, 54, 28), height(DASH, 55, 55, 26), height(DASH, 56, 140, 24)]
    # mesclagens
    for a1 in ["B1:M1", "B2:M2", "B4:C4", "D4:E4", "F4:I4", "J4:K4", "L4:M4", "B5:C5", "D5:E5", "F5:I5", "J5:K5", "L5:M5",
               "F6:M6", "B8:M8", "B12:M12", "B21:G21", "H21:M21", "B40:F40", "H40:M40", "B54:F54", "H54:M54"]:
        reqs.append(merge(DASH, a1))
    for r in (9, 10, 13, 14, 15, 17, 18, 19):
        reqs += [merge(DASH, f"{c}{r}:{NEXT[c]}{r}") for c in PAIRS]
    # cabeçalho
    reqs += [txt(R("B1:M1"), NAVY, 18, True), txt(R("B2:M2"), MUTED, 10),
             txt(R("B4:M4"), MUTED, 8, True),
             txt(R("B5:M5"), NAVY, 11, True, bg="#EEF2FF"),
             *[border(R(a1), "#C7D2FE") for a1 in ("B5:C5", "D5:E5", "F5:I5", "J5:K5", "L5:M5")],
             txt(R("B6"), MUTED, 8, True, "RIGHT"), txt(R("D6"), MUTED, 8, True, "RIGHT"),
             txt(R("C6"), NAVY, 10, True, "CENTER", "#EEF2FF"), txt(R("E6"), NAVY, 10, True, "CENTER", "#EEF2FF"),
             border(R("C6"), "#C7D2FE"), border(R("E6"), "#C7D2FE"),
             numfmt(R("C6"), "DATE", "dd/mm/yyyy"), numfmt(R("E6"), "DATE", "dd/mm/yyyy"),
             txt(R("F6:M6"), MUTED, 9, italic=True)]
    # cartão do aluno
    reqs += [txt(R("B8:M8"), INK, 16, True), border(R("B8:M8"), LINE, ("bottom",)),
             txt(R("B9:M9"), MUTED, 8, True), txt(R("B10:M10"), INK, 11, True),
             numfmt(R("J10"), "DATE", "dd/mm/yyyy")]
    # títulos de seção
    for a1 in ("B12:M12", "B21:G21", "H21:M21", "B40:F40", "H40:M40", "B54:F54", "H54:M54"):
        reqs += [txt(R(a1), NAVY, 10, True), border(R(a1), "#CBD5E1", ("bottom",))]
    # cartões de indicadores
    for r0 in (13, 17):
        reqs += [txt(R(f"B{r0}:M{r0}"), MUTED, 8, True, bg=SURF), txt(R(f"B{r0+1}:M{r0+1}"), INK, 20, True, bg=SURF),
                 txt(R(f"B{r0+2}:M{r0+2}"), MUTED, 8, bg=SURF, wrap="CLIP"),
                 border(R(f"B{r0}:M{r0+2}"), WHITE, ("left", "right", "innerVertical"), "SOLID_THICK")]
    reqs += [numfmt(R("B14"), "PERCENT", "0.0%"), numfmt(R("H18"), "PERCENT", "0.0%"),
             numfmt(R("D18"), "CURRENCY", "\"R$\" #,##0.00"), numfmt(R("L18"), "DATE", "dd/mm/yyyy")]
    # calendário
    reqs += [txt(R("B41:G41"), MUTED, 8, True, "CENTER"),
             txt(R("B42:F47"), INK, 10, True, "CENTER", WHITE, "WRAP"),
             border(R("B42:F47"), WHITE, ("top", "bottom", "left", "right", "innerHorizontal", "innerVertical"), "SOLID_THICK"),
             txt(R("G42:G47"), TEXT, 8, True, "LEFT", wrap="WRAP")]
    for a1, bgc, fgc in (("G42", GREEN_BG, GREEN), ("G43", RED_BG, RED), ("G44", BLUE_BG, NAVY), ("G45", GRAY_BG, MUTED),
                         ("G46", PURPLE_BG, PURPLE), ("G47", SURF, MUTED)):
        reqs.append(txt(R(a1), fgc, 8, True, "LEFT", bgc, "WRAP"))
    reqs.append(border(R("G42:G47"), WHITE, ("top", "bottom", "innerHorizontal", "left", "right"), "SOLID_THICK"))
    # tabelas
    for a1 in ("B55:F55", "H55:M55"):
        reqs += [txt(R(a1), NAVY, 8, True, "CENTER", HEAD), border(R(a1), NAVY, ("bottom",), "SOLID_MEDIUM")]
    reqs += [txt(R("B56:F79"), TEXT, 9), txt(R("D56:F79"), TEXT, 9, h="CENTER"),
             numfmt(R("D56:E79"), "PERCENT", "0.0%"),
             border(R("B56:F79"), LINE, ("bottom", "innerHorizontal")),
             txt(R("H56:M140"), TEXT, 9, wrap="WRAP"), numfmt(R("H56:H140"), "DATE", "dd/mm/yyyy"),
             txt(R("H56:H140"), TEXT, 9, True, "CENTER"),
             border(R("H56:M140"), LINE, ("bottom", "innerHorizontal"))]
    # filtros vinculados
    reqs += [dv_list("B5", ["Todas as Turmas", "Turma A", "Turma B"]),
             dv_list("D5", ["Todos", "Matriculado", "Deixou de Frequentar", "Desistente"]),
             dv_range("F5", f"={CN}!$M$2:$M$300"),
             dv_range("J5", f"={BF}!$BS$5:$BS$40"),
             dv_range("L5", f"={CN}!$N$2:$N$60"),
             {"setDataValidation": {"range": R("C6"), "rule": {"condition": {"type": "DATE_IS_VALID"}, "strict": True}}},
             {"setDataValidation": {"range": R("E6"), "rule": {"condition": {"type": "DATE_IS_VALID"}, "strict": True}}}]
    # formatação condicional (fórmulas de outra aba via INDIRECT)
    meta = "INDIRECT(\"CALC_DASH!B11\")"
    reqs += [cf("F5:I5", "=AND($F$5<>\"\";NOT(INDIRECT(\"CALC_DASH!B3\")))", RED, RED_BG),
             cf("F6:M6", "=LEFT($F$6;1)=\"⚠\"", RED, bold=True),
             cf("B14:C14", f"=AND(ISNUMBER($B$14);$B$14<{meta})", RED),
             cf("B14:C14", f"=AND(ISNUMBER($B$14);$B$14>={meta})", GREEN),
             cf("J14:K14", "=$J$14=\"Atingida\"", GREEN, GREEN_BG), cf("J14:K14", "=$J$14=\"Em risco\"", AMBER, AMBER_BG),
             cf("J14:K14", "=$J$14=\"Abaixo da meta\"", RED, RED_BG),
             cf("F14:G14", "=AND(ISNUMBER($F$14);$F$14>0)", RED),
             cf("B42:F47", "=REGEXMATCH(B42;\"PRE$\")", GREEN, GREEN_BG),
             cf("B42:F47", "=REGEXMATCH(B42;\"(FNJ|SUS)$\")", RED, RED_BG),
             cf("B42:F47", "=REGEXMATCH(B42;\"(FJU|ATE|DIS)$\")", NAVY, BLUE_BG),
             cf("B42:F47", "=REGEXMATCH(B42;\"FER$\")", MUTED, GRAY_BG),
             cf("B42:F47", "=REGEXMATCH(B42;\"(DEF|DES)$\")", PURPLE, PURPLE_BG),
             cf("B42:F47", "=REGEXMATCH(B42;\"—$\")", MUTED, SURF),
             cf("F56:F79", "=F56=\"Apto\"", GREEN, GREEN_BG, True), cf("F56:F79", "=F56=\"Não Apto\"", RED, RED_BG, True),
             cf("F56:F79", "=F56=\"Aguardando\"", MUTED),
             cf("D56:D79", f"=AND(ISNUMBER(D56);D56<{meta})", RED, bold=True),
             cf("I56:I140", "=OR(I56=\"Falta Não Justificada\";I56=\"Suspensão Disciplinar\")", RED, bold=True),
             cf("I56:I140", "=OR(I56=\"Deixou de Frequentar\";I56=\"Desistente\")", PURPLE, bold=True),
             cf("I56:I140", "=REGEXMATCH(I56;\"Justificada|Atestado|Dispensa\")", NAVY, bold=True)]
    # proteção (só aviso): tudo menos os filtros
    reqs += [{"addProtectedRange": {"protectedRange": {"range": {"sheetId": DASH}, "description": "Dashboard: edite apenas os filtros (linhas 5 e 6)",
                                                        "warningOnly": True, "unprotectedRanges": [R("B5:M5"), R("C6"), R("E6")]}}},
             {"addProtectedRange": {"protectedRange": {"range": {"sheetId": CALC}, "description": "Cálculos do dashboard — não editar", "warningOnly": True}}}]
    return reqs


def chart(anchor_row, anchor_col, w, h, spec):
    return {"addChart": {"chart": {"spec": {"fontName": FONT, **spec}, "position": {"overlayPosition": {
        "anchorCell": {"sheetId": DASH, "rowIndex": anchor_row, "columnIndex": anchor_col}, "offsetXPixels": 4, "offsetYPixels": 6,
        "widthPixels": w, "heightPixels": h}}}}}


def src(a1):
    return {"sourceRange": {"sources": [G(CALC, a1)]}}


def lote_graficos():
    linha = chart(21, 1, 640, 352, {"basicChart": {
        "chartType": "LINE", "legendPosition": "BOTTOM_LEGEND", "headerCount": 1,
        "axis": [{"position": "LEFT_AXIS", "viewWindowOptions": {"viewWindowMode": "EXPLICIT", "viewWindowMin": 0, "viewWindowMax": 1}}],
        "domains": [{"domain": src("Y1:Y25")}],
        "series": [{"series": src("Z1:Z25"), "targetAxis": "LEFT_AXIS", "colorStyle": C(NAVY), "lineStyle": {"width": 3},
                    "pointStyle": {"shape": "CIRCLE", "size": 6}},
                   {"series": src("AA1:AA25"), "targetAxis": "LEFT_AXIS", "colorStyle": C("#94A3B8"), "lineStyle": {"width": 2}},
                   {"series": src("AB1:AB25"), "targetAxis": "LEFT_AXIS", "colorStyle": C("#DC2626"), "lineStyle": {"width": 2, "type": "MEDIUM_DASHED"}}]}})
    colunas = chart(21, 7, 640, 352, {"basicChart": {
        "chartType": "COLUMN", "legendPosition": "BOTTOM_LEGEND", "headerCount": 1, "stackedType": "STACKED",
        "axis": [{"position": "LEFT_AXIS"}],
        "domains": [{"domain": src("AD1:AD25")}],
        "series": [{"series": src("AE1:AE25"), "targetAxis": "LEFT_AXIS", "colorStyle": C("#16A34A")},
                   {"series": src("AF1:AF25"), "targetAxis": "LEFT_AXIS", "colorStyle": C("#DC2626")},
                   {"series": src("AG1:AG25"), "targetAxis": "LEFT_AXIS", "colorStyle": C("#F59E0B")}]}})
    rosca = chart(40, 7, 640, 380, {"pieChart": {"legendPosition": "RIGHT_LEGEND", "pieHole": 0.55,
                                                 "domain": src("AI2:AI15"), "series": src("AJ2:AJ15")}})
    return [linha, colunas, rosca]


if __name__ == "__main__":
    lote = sys.argv[1] if len(sys.argv) > 1 else "estrutura"
    print(json.dumps({"estrutura": lote_estrutura, "formato": lote_formato, "graficos": lote_graficos,
                      "formato1": lambda: lote_formato_partes()[0], "formato2": lambda: lote_formato_partes()[1],
                      "formato3": lambda: lote_formato_partes()[2]}[lote](), ensure_ascii=False, separators=(",", ":")))

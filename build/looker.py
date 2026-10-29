"""Gera o lote (Sheets API batchUpdate) das abas de dados do Looker Studio.

Uso:  python3 build/looker.py > build/lote_looker.json

LS_REGISTROS  uma linha por lançamento de REGISTROS (indicadores, calendário, ocorrências)
LS_PARCELAS   uma linha por aluno x parcela já iniciada (frequência oficial e aptidão da BASE FREQUÊNCIA)

As colunas ALUNO, MATRÍCULA, TURMA, STATUS ATUAL, Nº PARCELA e PARCELA têm o mesmo nome
nas duas abas: no Looker Studio um controle filtra gráficos das duas fontes.
CPF e e-mail não entram nas abas.
"""
import json

from layout import C, BF, CR, G

LSR, LSP = 910020, 910021
PAR = "'PARÂMETROS'"
REG = lambda c: f"REGISTROS!${c}$3:${c}"

R_HEAD = ["DATA", "Nº PARCELA", "PARCELA", "MATRÍCULA", "ALUNO", "TURMA", "STATUS ATUAL", "TURNO",
          "DISCIPLINA", "SITUAÇÃO", "CÓDIGO", "IMPACTO", "AULAS", "HA LETIVA", "HA FALTA",
          "PRESENÇA", "FALTA", "ABONO", "BLOQUEIO", "Nº DOC", "STATUS JUSTIFICATIVA", "OBSERVAÇÕES"]

# lançamentos válidos (data e matrícula preenchidas), enriquecidos com cadastro e parcela
R_FORMULA = (
    "=ARRAYFORMULA(LET("
    f"b;FILTER(HSTACK({REG('B')};TO_TEXT({REG('D')});{REG('I')};{REG('H')};{REG('K')};{REG('L')};{REG('J')};{REG('M')};{REG('N')};{REG('Q')});"
    f"{REG('B')}<>\"\";{REG('D')}<>\"\");"
    "d;CHOOSECOLS(b;1);m;CHOOSECOLS(b;2);sit;CHOOSECOLS(b;5);imp;CHOOSECOLS(b;6);aul;N(CHOOSECOLS(b;7));"
    "ma;TO_TEXT(ALUNOS!$B$2:$B);"
    f"np;XLOOKUP(d;{CR}!$D$8:$D$31;SEQUENCE(24);\"\";-1);"
    f"pc;XLOOKUP(d;{CR}!$D$8:$D$31;{CR}!$C$8:$C$31;\"\";-1);"
    "nome;XLOOKUP(m;ma;ALUNOS!$C$2:$C;\"\");"
    "HSTACK(d;np;pc;m;nome&\" — \"&m;XLOOKUP(m;ma;ALUNOS!$F$2:$F;\"\");XLOOKUP(m;ma;ALUNOS!$H$2:$H;\"\");"
    "CHOOSECOLS(b;3);CHOOSECOLS(b;4);sit;"
    f"XLOOKUP(sit;{PAR}!$B$7:$B$15;{PAR}!$A$7:$A$15;\"\");imp;aul;"
    "IF(imp=\"Dia Não Letivo\";0;aul);IF(imp=\"Computa Falta\";aul;0);"
    "--(imp=\"Computa Presença\");--(imp=\"Computa Falta\");--(LEFT(imp;11)=\"Justificada\");"
    "--((imp=\"Bloqueio de Benefício\")+(imp=\"Cancelamento\")>0);"
    "CHOOSECOLS(b;8);CHOOSECOLS(b;9);CHOOSECOLS(b;10))))"
)

P_HEAD = ["MATRÍCULA", "ALUNO", "TURMA", "STATUS ATUAL", "Nº PARCELA", "PARCELA", "INÍCIO", "FIM",
          "FREQUÊNCIA", "MÉDIA DA TURMA", "META", "APTIDÃO", "APTO", "VALOR APTO", "POSIÇÃO NA TURMA",
          "PARCELA EM CURSO", "ÚLTIMO LANÇAMENTO"]

# aluno x parcela (só parcelas iniciadas até o último lançamento)
F = f"{BF}!$G$5:$AD$204"
P_FORMULA = (
    "=ARRAYFORMULA(LET("
    f"lin;FILTER(SEQUENCE(200);{BF}!$A$5:$A$204<>\"\");"
    f"ult;{BF}!$B$2;np;COUNTIF({BF}!$G$2:$AD$2;\"<=\"&ult);"
    "s;SEQUENCE(ROWS(lin)*np);"
    "r;MAP(s;LAMBDA(x;INDEX(lin;INT((x-1)/np)+1)));k;MAP(s;LAMBDA(x;MOD(x-1;np)+1));"
    f"m;MAP(r;LAMBDA(x;TO_TEXT(INDEX({BF}!$A$5:$A$204;x))));"
    "ma;TO_TEXT(ALUNOS!$B$2:$B);"
    f"tb;MAP(r;LAMBDA(x;INDEX({BF}!$D$5:$D$204;x)));"
    f"fim;MAP(k;LAMBDA(y;INDEX({BF}!$G$3:$AD$3;1;y)));"
    f"fr;MAP(r;k;LAMBDA(x;y;LET(v;INDEX({F};x;y);IF(ISNUMBER(v);v;\"\"))));"
    f"ap;MAP(r;k;LAMBDA(x;y;INDEX({BF}!$AF$5:$BC$204;x;y)));"
    f"meta;{PAR}!$B$2;"
    "HSTACK(m;XLOOKUP(m;ma;ALUNOS!$C$2:$C;\"\")&\" — \"&m;XLOOKUP(m;ma;ALUNOS!$F$2:$F;\"\");XLOOKUP(m;ma;ALUNOS!$H$2:$H;\"\");"
    f"k;MAP(k;LAMBDA(y;INDEX({BF}!$G$4:$AD$4;1;y)));MAP(k;LAMBDA(y;INDEX({BF}!$G$2:$AD$2;1;y)));fim;fr;"
    f"MAP(tb;k;LAMBDA(t;y;IFERROR(AVERAGEIFS(INDEX({F};0;y);{BF}!$D$5:$D$204;t);\"\")));"
    "IF(LEN(m);meta;\"\");ap;--(ap=\"Apto\");IF(ap=\"Apto\";"
    f"{PAR}!$B$4;0);"
    f"MAP(fr;tb;k;LAMBDA(f;t;y;IF(ISNUMBER(f);COUNTIFS(INDEX({F};0;y);\">\"&f;{BF}!$D$5:$D$204;t)+1;\"\")));"
    "IF(fim>=ult;\"Sim\";\"Não\");IF(LEN(m);ult;\"\"))))"
)


def aba(sid, title, head, formula, cols):
    reqs = [
        {"addSheet": {"properties": {"sheetId": sid, "title": title, "tabColorStyle": C("#94A3B8"),
                                     "gridProperties": {"rowCount": 6000 if sid == LSR else 2000, "columnCount": len(head), "frozenRowCount": 1}}}},
        {"updateCells": {"start": {"sheetId": sid, "rowIndex": 0, "columnIndex": 0},
                         "rows": [{"values": [{"userEnteredValue": {"stringValue": h}} for h in head]},
                                  {"values": [{"userEnteredValue": {"formulaValue": formula}}]}],
                         "fields": "userEnteredValue"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontFamily": "Inter"}, "backgroundColorStyle": C("#F1F5F9")}},
                        "fields": "userEnteredFormat.textFormat,userEnteredFormat.backgroundColorStyle"}},
    ]
    for letters, kind, pattern in cols:  # formatos que o Looker Studio usa para detectar o tipo
        a, b = letters.split(":")
        reqs.append({"repeatCell": {"range": {**G(sid, f"{a}2:{b}2"), "endRowIndex": None},
                                    "cell": {"userEnteredFormat": {"numberFormat": {"type": kind, "pattern": pattern}}},
                                    "fields": "userEnteredFormat.numberFormat"}})
        del reqs[-1]["repeatCell"]["range"]["endRowIndex"]
    return reqs


def lote():
    return (aba(LSR, "LS_REGISTROS", R_HEAD, R_FORMULA, [("A:A", "DATE", "yyyy-mm-dd")])
            + aba(LSP, "LS_PARCELAS", P_HEAD, P_FORMULA,
                  [("G:H", "DATE", "yyyy-mm-dd"), ("I:K", "PERCENT", "0.0%"),
                   ("N:N", "CURRENCY", "\"R$\" #,##0.00"), ("Q:Q", "DATE", "yyyy-mm-dd")]))


if __name__ == "__main__":
    print(json.dumps(lote(), ensure_ascii=False, separators=(",", ":")))

from app.macros.vbs_parser import parse_vbs

SNIPPET = """
Option Explicit
Dim SapGuiAuto, application, connection, session

session.findById("wnd[0]/tbar[0]/okcd").Text = "/nML81N"
session.findById("wnd[0]").sendVKey 0
session.findById("wnd[0]/shellcont/shell/shellcont[1]/shell[1]").topNode = "          1"
session.findById("wnd[0]/tbar[1]/btn[17]").Press
session.findById("wnd[1]/usr/ctxtRM11R-LBLNI").Text = NumHES
session.findById("wnd[1]/usr/ctxtRM11R-LBLNI").SetFocus
session.findById("wnd[1]/usr/ctxtRM11R-LBLNI").caretPosition = 10
session.findById("wnd[1]/tbar[0]/btn[0]").Press
session.findById("wnd[0]").sendVKey 5
session.findById("wnd[0]").sendVKey 7
session.findById("wnd[0]/usr/ctxtNAST-LDEST").Text = "LOCL"
session.findById("wnd[0]/usr/cmbNAST-TDOCOVER").key = "D"
session.ActiveWindow.sendVKey 13
session.findById("wnd[0]").maximize
session.StartTransaction "SP01"
"""


def test_parse_vbs_steps():
    steps = parse_vbs(SNIPPET)
    actions = [step.action for step in steps]
    assert actions == [
        "transaction",
        "send_vkey",
        "set_tree_node",
        "press",
        "set_text",
        "focus",
        "press",
        "send_vkey",
        "send_vkey",
        "set_text",
        "set_combo",
        "send_vkey_active",
        "maximize",
        "transaction",
    ]


def test_document_id_is_marked():
    steps = parse_vbs(SNIPPET)
    field = next(s for s in steps if s.action == "set_text" and s.path.endswith("ctxtRM11R-LBLNI"))
    assert field.value == "{ID}"


def test_literal_values_kept():
    steps = parse_vbs(SNIPPET)
    ld = next(s for s in steps if s.action == "set_text" and s.path.endswith("ctxtNAST-LDEST"))
    assert ld.value == "LOCL"


def test_transaction_values():
    steps = parse_vbs(SNIPPET)
    assert steps[0].value == "ML81N"
    assert steps[-1].value == "SP01"


def test_numeric_literal_marked_as_id():
    steps = parse_vbs('session.findById("wnd[1]/usr/ctxtRM11R-LBLNI").Text = "1042683137"')
    assert steps[0].action == "set_text"
    assert steps[0].value == "{ID}"
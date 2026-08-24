import re
from typing import Dict, List, Optional

from .macro_model import MacroStep

_FIND = re.compile(r'findById\(\s*"([^"]+)"\s*\)')
_ACTIVE_VKEY = re.compile(r"ActiveWindow\.sendVKey\s+(-?\d+)", re.IGNORECASE)
_TX = re.compile(r"StartTransaction\s+[\"']([^\"']+)[\"']", re.IGNORECASE)
_TEXT = re.compile(r'\.Text\s*=\s*"([^"]*)"', re.IGNORECASE)
_TEXT_VAR = re.compile(r"\.Text\s*=\s*([A-Za-z_]\w*)", re.IGNORECASE)
_KEY = re.compile(r'\.key\s*=\s*"([^"]*)"', re.IGNORECASE)
_SELECTED = re.compile(r'\.Selected\s*=\s*(True|False)', re.IGNORECASE)
_TOPNODE = re.compile(r'\.topNode\s*=\s*"([^"]*)"', re.IGNORECASE)
_VKEY = re.compile(r"\.sendVKey\s+(-?\d+)", re.IGNORECASE)
_CARET = re.compile(r"\.caretPosition", re.IGNORECASE)
_ID_VALUE = re.compile(r"^\d{8,}$")

_EMPTY_ROW_SUB = re.compile(
    r"Sub\s+(\w+)\s*\(\)\s*(.*?)^End\s+Sub", re.IGNORECASE | re.DOTALL | re.MULTILINE
)
_EMPTY_ROW_FUNC = re.compile(
    r"Function\s+(\w+)\s*\(.*?\)\s*(.*?)^End\s+Function", re.IGNORECASE | re.DOTALL | re.MULTILINE
)
_FOR_LOOP = re.compile(r"For\s+(\w+)\s*=\s*0\s*To\s+(\w+)", re.IGNORECASE)
_IF_EMPTY = re.compile(r'If\s+Trim\((\w+)\)\s*=\s*""\s*Then', re.IGNORECASE)
_EXIT_FOR = re.compile(r"Exit\s+For", re.IGNORECASE)
_ERROR_RAISE = re.compile(r"Err\.Raise", re.IGNORECASE)
_FIND_BY_ID_ROW = re.compile(
    r'findById\(\s*"([^"]+)"\s*\)', re.IGNORECASE
)
_TEXT_ASSIGN = re.compile(r'\.Text\s*=\s*"([^"]*)"', re.IGNORECASE)
_KEY_ASSIGN = re.compile(r'\.key\s*=\s*"([^"]*)"', re.IGNORECASE)
_SETFOCUS = re.compile(r"\.SetFocus", re.IGNORECASE)

_CELL_TEXT_FUNC = re.compile(
    r'resultado\s*=\s*session\.findById\(\s*"([^"]+)"\s*\)\.Text', re.IGNORECASE
)
_ROW_PARAM = re.compile(r'\(\s*fila\s*\)', re.IGNORECASE)


def _mark_document_id(step: MacroStep) -> MacroStep:
    if step.action == "set_text" and _ID_VALUE.match(step.value or ""):
        step.value = "{ID}"
    return step


def _parse_empty_row_subroutine(sub_name: str, sub_body: str) -> Optional[MacroStep]:
    """Detecta el patron AgregarMensajeNEU:
    - Loop For fila = 0 To maxFilas
    - Llama a funcion que lee .Text de una celda con parametro fila
    - If Trim(celdaTexto) = "" Then -> fila encontrada
    - Luego escribe valor en esa fila (set_text) y/o combo
    """
    cell_func_match = _CELL_TEXT_FUNC.search(sub_body)
    if not cell_func_match:
        return None

    cell_path_template = cell_func_match.group(1)
    base_cell_path = re.sub(r'\s*["\']\s*&\s*\w+\s*&\s*["\']', '{row}', cell_path_template)

    max_rows = 20
    for_loop = _FOR_LOOP.search(sub_body)
    if for_loop:
        try:
            max_rows = int(for_loop.group(2))
        except ValueError:
            pass

    write_text_match = _TEXT_ASSIGN.search(sub_body)
    write_value = ""
    if write_text_match:
        write_value = write_text_match.group(1)

    combo_key_match = _KEY_ASSIGN.search(sub_body)
    combo_value = ""
    if combo_key_match:
        combo_value = combo_key_match.group(1)

    combo_path = ""
    key_lines = [line for line in sub_body.splitlines() if _KEY_ASSIGN.search(line)]
    if key_lines:
        find_match = _FIND.search(key_lines[0])
        if find_match:
            combo_path = find_match.group(1).replace('" & filaEncontrada & "', '{row}')

    if not base_cell_path:
        return None

    return MacroStep(
        action="find_empty_row",
        path=base_cell_path,
        table_path="",
        column_path=base_cell_path,
        write_value=write_value or "NEU",
        combo_path=combo_path,
        combo_value=combo_value or "1",
        max_rows=max_rows,
        value="",
    )


def _extract_subroutines(text: str) -> List[Dict]:
    subs = []
    for match in _EMPTY_ROW_SUB.finditer(text):
        subs.append({"type": "sub", "name": match.group(1), "body": match.group(2)})
    for match in _EMPTY_ROW_FUNC.finditer(text):
        subs.append({"type": "function", "name": match.group(1), "body": match.group(2)})
    return subs


def _mark_document_id(step: MacroStep) -> MacroStep:
    if step.action == "set_text" and _ID_VALUE.match(step.value or ""):
        step.value = "{ID}"
    return step


def parse_vbs(text: str) -> List[MacroStep]:
    steps = []

    subs = _extract_subroutines(text)
    empty_row_steps = []
    for sub in subs:
        if sub["type"] == "sub":
            step = _parse_empty_row_subroutine(sub["name"], sub["body"])
            if step:
                empty_row_steps.append(step)

    lines = text.splitlines()
    steps = []
    in_sub = False
    sub_depth = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("'"):
            continue

        if re.match(r"^\s*(Sub|Function)\s+\w+", line, re.IGNORECASE):
            in_sub = True
            sub_depth += 1
            continue
        if re.match(r"^\s*End\s+(Sub|Function)", line, re.IGNORECASE):
            sub_depth -= 1
            if sub_depth == 0:
                in_sub = False
            continue

        if in_sub:
            continue

        tx = _TX.search(line)
        if tx:
            steps.append(MacroStep(action="transaction", value=tx.group(1)))
            continue

        active = _ACTIVE_VKEY.search(line)
        if active:
            steps.append(MacroStep(action="send_vkey_active", key=int(active.group(1))))
            continue

        match = _FIND.search(line)
        if not match:
            continue
        path = match.group(1)

        if _CARET.search(line):
            continue
        if _TEXT.search(line):
            value = _TEXT.search(line).group(1)
            if path.endswith("okcd") and value.lower().startswith("/n"):
                steps.append(MacroStep(action="transaction", value=value[2:]))
            else:
                steps.append(
                    _mark_document_id(MacroStep(action="set_text", path=path, value=value))
                )
            continue
        if _TEXT_VAR.search(line):
            steps.append(
                MacroStep(action="set_text", path=path, value="{ID}")
            )
            continue
        key = _KEY.search(line)
        if key:
            steps.append(MacroStep(action="set_combo", path=path, value=key.group(1)))
            continue
        selected = _SELECTED.search(line)
        if selected:
            steps.append(MacroStep(action="set_checked", path=path, value=selected.group(1)))
            continue
        topnode = _TOPNODE.search(line)
        if topnode:
            steps.append(MacroStep(action="set_tree_node", path=path, value=topnode.group(1)))
            continue
        vkey = _VKEY.search(line)
        if vkey:
            steps.append(MacroStep(action="send_vkey", path=path, key=int(vkey.group(1))))
            continue
        if ".Press" in line:
            steps.append(MacroStep(action="press", path=path))
            continue
        if ".SetFocus" in line:
            steps.append(MacroStep(action="focus", path=path))
            continue
        if ".maximize" in line:
            steps.append(MacroStep(action="maximize", path=path))
            continue

    steps.extend(empty_row_steps)

    return steps

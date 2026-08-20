import re

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


def _mark_document_id(step):
    if step.action == "set_text" and _ID_VALUE.match(step.value or ""):
        step.value = "{ID}"
    return step


def parse_vbs(text):
    steps = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("'"):
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
    return steps
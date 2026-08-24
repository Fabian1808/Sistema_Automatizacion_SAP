HES_TRANSACTION = "ML81N"
SP01_TRANSACTION = "SP01"

TREE_ROOT = "wnd[0]/shellcont/shell/shellcont[1]/shell[1]"
TREE_ROOT_NODE = "          1"
BTN_OTRAS_ENTRADAS = "wnd[0]/tbar[1]/btn[17]"
POPUP_HES_FIELD = "wnd[1]/usr/ctxtRM11R-LBLNI"
POPUP_OK = "wnd[1]/tbar[0]/btn[0]"

MSG_TABLE_KSCHL = "wnd[0]/usr/tblSAPDV70ATC_NAST3/ctxtDNAST-KSCHL[1,{row}]"
MSG_TABLE_NACHA = "wnd[0]/usr/tblSAPDV70ATC_NAST3/cmbNAST-NACHA[3,{row}]"
KSCHL_VALUE = "NEU"
NACHA_VALUE = "1"

BTN_TBAR_3 = "wnd[0]/tbar[0]/btn[3]"
BTN_TBAR_11 = "wnd[0]/tbar[0]/btn[11]"
BTN_GRABAR = "wnd[0]/tbar[0]/btn[15]"

CMB_VSZTP = "wnd[0]/usr/cmbNAST-VSZTP"
VSZTP_VALUE = "4"
CTXT_LDEST = "wnd[0]/usr/ctxtNAST-LDEST"
LDEST_VALUE = "LOCL"
CMB_TDOCOVER = "wnd[0]/usr/cmbNAST-TDOCOVER"
TDOCOVER_VALUE = "D"

SP01_REFRESH = "wnd[0]/tbar[1]/btn[8]"
SP01_CHK = "wnd[0]/usr/chk[1,3]"
SP01_PRINT = "wnd[0]/tbar[1]/btn[13]"

VKEY_ENTER = 0
VKEY_F5 = 5
VKEY_F7 = 7
VKEY_SHIFT_F1 = 13

from ...services.native_dialog import (  # noqa: E402
    DIALOG_TIMEOUT,
    LONG_WAIT,
    PDF_WAIT_TIMEOUT,
    SAVE_DIALOG_TITLES,
)

ERROR_KEYWORDS = [
    "no existe",
    "no encontrad",
    "bloquead",
    "no autorizad",
    "no permitid",
    "error",
]
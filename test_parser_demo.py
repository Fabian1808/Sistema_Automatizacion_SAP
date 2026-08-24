from sap_document_automation.macros.vbs_parser import parse_vbs

raw = open('ImprimirReporte.vbs', 'rb').read()
text = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', errors='replace')
steps = parse_vbs(text)
print('Total steps:', len(steps))
for i, s in enumerate(steps):
    val = s.value if s.value else (str(s.key) if s.key else '')
    print(f'{i+1:2}. {s.action:18} {s.path or "-":55} {val}')
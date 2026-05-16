import zipfile
import re

file_path = r'database\Materie Prime.xlsm'

def extract_strings(binary_data):
    # Find sequences of printable characters
    return re.findall(b'[a-zA-Z0-9_/]{4,}', binary_data)

try:
    with zipfile.ZipFile(file_path, 'r') as z:
        vba_project = 'xl/vbaProject.bin'
        if vba_project in z.namelist():
            with z.open(vba_project) as f:
                content = f.read()
                strings = extract_strings(content)
                # Filter for interesting keywords
                keywords = [b'Sub', b'Function', b'Dim', b'Sheets', b'Range', b'Value', b'MsgBox', b'Click']
                found = []
                for s in strings:
                    s_str = s.decode('utf-8', errors='ignore')
                    # Look for things that look like procedure names after Sub
                    # or names of sheets
                    found.append(s_str)
                
                # Let's print unique strings that might be macro names
                # Often macro names are capitalized or camelCase
                macro_hints = [s for s in found if any(k in s for k in ['Scarica', 'Stampa', 'Pulisci', 'Aggiorna', 'Crea', 'Lotto', 'FDG'])]
                print("Potential Macro names/Keywords found:")
                for m in sorted(list(set(macro_hints))):
                    if len(m) > 3:
                        print(f"- {m}")
        else:
            print("No macros found.")
except Exception as e:
    print(f"Error: {e}")

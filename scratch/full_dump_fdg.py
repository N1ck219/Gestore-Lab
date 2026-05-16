import pandas as pd
import os

file_path = r'database\Materie Prime.xlsm'
sheet_name = 'Picking FDG'

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', header=None)
    items = []
    # Loop through rows where materials usually are
    for i in range(10, 40):
        if i >= len(df): break
        row = df.iloc[i]
        # Material name is usually in col 6 (index 6)
        # Code is in col 2 (index 2)
        # Quantity is in col 21 (index 21) or col 45 (index 45)?
        # Let's check where the quantity "20" is for Flaconi
        name = str(row[6])
        code = str(row[2])
        qnt = row[21]
        
        if code.isdigit() and name != 'nan':
            items.append({'codice': code, 'nome': name, 'qnt': qnt})
    
    for item in items:
        print(item)

except Exception as e:
    print(f"Error: {e}")

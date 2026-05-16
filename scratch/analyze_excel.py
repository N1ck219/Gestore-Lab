import pandas as pd
import os

file_path = r'database\Materie Prime.xlsm'
sheet_name = 'Picking FDG'

try:
    # Read without headers first to see the whole sheet
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', header=None)
    
    # Let's print rows 0 to 30 and columns 0 to 15
    print("--- Picking FDG (Top Left Section) ---")
    print(df.iloc[0:30, 0:15].to_string(header=False, index=False))
    
    print("\n--- Picking FDG (Right Section) ---")
    # I saw some interesting data on the right in previous logs
    print(df.iloc[0:30, 40:55].to_string(header=False, index=False))

except Exception as e:
    print(f"Error: {e}")

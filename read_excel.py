import pandas as pd

try:
    file_path = "INVENTARIO.xlsx"
    excel_data = pd.ExcelFile(file_path)
    print("Sheet names:", excel_data.sheet_names)
    
    for sheet_name in excel_data.sheet_names:
        print(f"\n--- Sheet: {sheet_name} ---")
        df = pd.read_excel(excel_data, sheet_name=sheet_name)
        print(df.head(10))
        print("\nColumns:", df.columns.tolist())
except Exception as e:
    print("Error reading Excel file with pandas:", e)

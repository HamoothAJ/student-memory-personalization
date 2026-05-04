import pandas as pd
import os

file_path = os.path.join('data', 'raw', 'skill_builder_data.csv')
encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']

for enc in encodings:
    try:
        pd.read_csv(file_path, encoding=enc, nrows=5)
        print('ok', enc)
    except Exception as e:
        print('fail', enc, type(e).__name__, str(e))

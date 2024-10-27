import pandas as pd
import pathlib
import numpy as np



DB_PATH = pathlib.Path(__file__).parent / "section_data"

def pfi_sections():
    df = pd.read_csv(DB_PATH / 'eu_pf_sections.csv')
    scaled_columns = {
        "A": 2,
        "Iy": 4,
        "Wel_y": 3,
        "Wpl_y": 3,
        "iy": 1,
        "Avz": 2,
        "Iz": 4,
        "Wel_z": 3,
        "Wpl_z": 3,
        "iz": 1,
        "Ss": 1,
        "It": 4,
        "Iw": 3 + 6,
    }
    for column_name, power in scaled_columns.items():
        df[column_name] = df[column_name] * 10**power
    return df
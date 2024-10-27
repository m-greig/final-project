import pandas as pd
import pathlib
import numpy as np
from sectionproperties.analysis.section import Section
from sectionproperties.pre.pre import Material
from sectionproperties.pre.library import steel_sections as steel



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


def aisc_w_sections(si_units: bool = True):
    if not si_units:
        df = pd.read_csv(DB_PATH / 'aisc_w_sections_us.csv')
        return df
    else:
        df = pd.read_csv(DB_PATH / 'aisc_w_sections_si.csv')
        scaled_columns = {
            "Ix": 6,
            "Zx": 3,
            "Sx": 3,
            "Iy": 6,
            "Zy": 3,
            "Sy": 3,
            "Cw": 9,
            "J": 3,
        }
        for column_name, power in scaled_columns.items():
            df[column_name] = df[column_name] * 10**power
        return df


def section_filter(sections_df: pd.DataFrame, operator: str, **kwargs) -> pd.DataFrame:
    """
    Returns a new DataFrame representing 'sections_df' but filtered with 'operator'
    according to the given 'kwargs'
    sections_df: A DataFrame with records of structural sections
    operator: str, either {"ge", "le"}, greater-than-or-equal-to and less-than-or-equal-to
    'kwargs': The kwargs provided should correspond to column names in 'sections_df'
        (which should all be valid Python identifiers)
        e.g. if there is a column in 'sections_df' called Ix then the DataFrame
        could be filtered by calling the function as such:
            section_filter(sections_df, 'ge', Ix=400e6)
    """
    sub_df = sections_df.copy()
    for key, value in kwargs.items():
        if operator.lower() == "le":
            sub_df = sub_df.loc[sub_df[key] <= value]
        elif operator.lower() == "ge":
            sub_df = sub_df.loc[sub_df[key] >= value]
        if sub_df.empty:
            print(f"No records match all of the parameters: {kwargs}")
    return sub_df


def section_approx_equal(sections_df: pd.DataFrame, tol=0.1, **kwargs) -> pd.DataFrame:
    """
    Returns a new DataFrame representing 'sections_df' but filtered with 'operator'
    according to the given 'kwargs'
    sections_df: A DataFrame with records of structural sections
    'kwargs': The kwargs provided should correspond to column names in 'sections_df'
        (which should all be valid Python identifiers)
        e.g. if there is a column in 'sections_df' called Ix then the DataFrame
        could be filtered by calling the function as such:
            section_approx_equal(sections_df, Ix=400e6)
    """
    sub_df = sections_df.copy()
    for key, value in kwargs.items():
        sub_df = sub_df.loc[sub_df[key] <= value * (1 + tol)]
        sub_df = sub_df.loc[sub_df[key] >= value * (1 - tol)]
        print(sub_df[key].unique())
    return sub_df


def sort_by_weight(sections_df: pd.DataFrame, ascending:bool = True) -> pd.DataFrame:
    """
    Returns 'sections_df' sorted by weight
    """
    return sections_df.sort_values("W", ascending=ascending)

def calculate_section_stresses(
    sections_df: pd.DataFrame,
    fy: float,
    N: float = 0,
    Mx: float = 0,
    My: float = 0,
    Vx: float = 0,
    Vy: float = 0,
    Mz: float = 0
) -> pd.DataFrame:
    """
    Returns a copy of 'sections_df' with nine additional columns added:
        - Steel yield strength 
        - N
        - Mx
        - My
        - Vx
        - Vy
        - Mz
        - sig_vm Max (Maximum von Mises stress)
        - DCR stress
        
    Calculated off of the section data in each row and the provided
    force actions.
    """
    acc = []
    for df_idx, row in sections_df.iterrows():
        print(f"Calculating section: {row['Section']}")
        section = create_section(row, mesh_size=100)
        max_vm_stress = max_vonmises_stress(section, N, Mx, My, Vx, Vy, Mz)
        row['fy'] = fy
        row['sig_vm Max'] = max_vm_stress
        row['DCR stress'] = row['sig_vm Max'] / row['fy']
        acc.append(row)
    return pd.DataFrame(acc)


def create_section(
    steel_section: pd.Series, 
    mesh_size: float = 100,
) -> float: 
    """
    Returns a section from section_record
    """
    d = steel_section.d
    b = steel_section.bf
    t_f = steel_section.tf
    t_w = steel_section.tw
    k = steel_section.kdes
    r = k - t_f
    steel_350 = Material("Steel 350 MPa", 200e3, 0.3, 350, 1, color='lightgrey')
    geom = steel.i_section(d=d, b=b, t_f=t_f, t_w=t_w, r=r, n_r = 12, material=steel_350)
    geom.create_mesh(mesh_size)
    section = Section(geom)
    return section


def max_vonmises_stress(
    section: Section,
    N: float = 0,
    Mx: float = 0,
    My: float = 0,
    Vx: float = 0,
    Vy: float = 0,
    Mz: float = 0,
) -> float:
    """
    Returns the maximum von Mises stress that occurs within 'section' when subjected to the combined
    actions of 'N', 'Mx', 'My', 'Mz', 'Vx', 'Vy'.
    """
    section.calculate_geometric_properties()
    section.calculate_warping_properties()
    stress_result = section.calculate_stress(N, Vx, Vy, Mx, My, Mzz=Mz)
    stress_dict = stress_result.get_stress()[0]
    vm = stress_dict['sig_vm']
    return np.max(np.abs(vm))
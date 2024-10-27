import streamlit as st
import load_factors, beams, sections_db, plots
import PyNite
from PyNite import FEModel3D
import matplotlib as plt
import pandas as pd
from load_factors import nbcc_2020_combos, nbcc_2015_combos, nbcc_2010_combos

st.set_page_config(layout='wide')

col1, col2 = st.columns(2)

with col1:
    st.header('Inputs')
    st.text('Geometry')
    length = st.slider('Beam length (m)', 1, 20)
    left_support = st.selectbox('Left hand support', ['Pin', 'Fix', 'None'])
    right_support = st.selectbox('Right hand support', ['Pin', 'Fix', 'None'])

    
    st.text("""Loading
All loads are in kN or kN/m for point and UDL. Locations are absolute rather than relative.""")

    udl_loads = pd.DataFrame(
        {
            'Case': ['Dead', 'Live', 'Wind', 'Snow'],
            'Magnitude': [-2, -4, -1, -0.5],
            'Start Point': [0, 0, 0, 0],
            'End Point': [1, 1, 1, 1]
        }
    )

    point_loads = pd.DataFrame(
        {
            'Case': ['Dead', 'Live', 'Wind', 'Snow'],
            'Magnitude': [-5, -10, -2, -1],
            'Location': [0.5, 0.5, 0.5, 0.5]
        }
    )

    edited_point_loads = st.data_editor(point_loads,
                                        column_config={
                                            "Case": st.column_config.SelectboxColumn(options=['Dead', 'Live', 'Snow', 'Wind']),
                                            "Location": st.column_config.NumberColumn(min_value=0, max_value=20)
                                            },
                                            num_rows='dynamic')
    edited_udl_loads = st.data_editor(udl_loads,
                                      column_config={
                                          "Case": st.column_config.SelectboxColumn(options=['Dead', 'Live', 'Snow', 'Wind']),
                                          'Start Point': st.column_config.NumberColumn(min_value=0, max_value=20),
                                          'End Point': st.column_config.NumberColumn(min_value=0, max_value=20)
                                      },
                                      num_rows='dynamic')
    
    st.text('Load combinations to check')
    load_combos = st.selectbox('Combination Set', ['nbcc_2020', 'nbcc_2015', 'nbcc_2010'])
    
    st.text('Allowable deflection limits')
    deflection_limit = st.slider('Deflection limit (span/x)', 1, 1000)

    

# Create dictionary to contain supports

supports = {0: left_support, length: right_support}
updated_supports = {}

for key,value in supports.items():
    if value == 'None' or None:
        pass
    else:
        updated_supports[key] = value[0]


# Create dictionary to contain loads
loads_dict = []

for _, row in edited_point_loads.iterrows():
    if row['Case'] == 'Dead':
        case = 'D'
    elif row['Case'] == 'Live':
        case = 'L'
    elif row['Case'] == 'Wind':
        case = 'W'
    elif row['Case'] == 'Snow':
        case = 'S'
    row_dict = {
        'Type': 'Point',
        'Direction': 'FZ',
        'Magnitude': row['Magnitude'],
        'Location': row['Location'],
        'Case': case
    }
    loads_dict.append(row_dict)

for _, row in edited_udl_loads.iterrows():
    if row['Case'] == 'Dead':
        case = 'D'
    elif row['Case'] == 'Live':
        case = 'L'
    elif row['Case'] == 'Wind':
        case = 'W'
    elif row['Case'] == 'Snow':
        case = 'S'
    row_dict = {
        'Type': 'Dist',
        'Direction': 'FZ',
        'Start Magnitude': row['Magnitude'],
        'End Magnitude': row['Magnitude'],
        'Start Location': row['Start Point'],
        'End Location': row['End Point'],
        'Case': case
    }
    loads_dict.append(row_dict)



beam_data = {
    'Name': 'beam',
    'L': length,
    'Nodes': beams.get_node_locations([0, length], length),
    'Supports': updated_supports,
    'Loads': loads_dict,
    'E': 210*1000*1000,
    'nu': 0.3,
    'rho': 7850,
    'Iy': 1,
    'Iz': 1,
    'J': 1,
    'A': 1
}

beam_model = beams.build_beam(beam_data)

if load_combos is not None:
    if load_combos.lower() == "nbcc_2020":
        load_combos = nbcc_2020_combos()
    elif load_combos.lower() == "nbcc_2015":
        load_combos = nbcc_2015_combos()
    elif load_combos.lower() == "nbcc_2010":
        load_combos = nbcc_2010_combos()
    else:
        raise ValueError(f"Add combos must be one of 'nbcc_2020', 'nbcc_2015', or 'nbcc_2010', not {load_combos}")
    for combo_name, combo_factors in load_combos.items():
        beam_model.add_load_combo(combo_name, combo_factors)


beam_model.add_load_combo("SLS", {"D": 1.0, "L": 1.0, "W": 1.0, "S": 1.0})


beam_model.analyze()
left_support_reaction  = beam_model.Nodes['N0'].RxnFY["LC1"]
right_support_reaction = beam_model.Nodes['N1'].RxnFY['LC1']

max_fz = []
max_my = []
max_def = []

for combo_name, combo_factors in load_combos.items():
    max_fz.append(beam_model.Members['beam'].max_shear('Fz', combo_name))
    max_fz.append(beam_model.Members['beam'].min_shear('Fz', combo_name))
    max_my.append(beam_model.Members['beam'].max_moment('My', combo_name))
    max_my.append(beam_model.Members['beam'].min_moment('My', combo_name))

max_def.append(beam_model.Members['beam'].max_deflection('dz', "SLS"))
max_def.append(beam_model.Members['beam'].min_deflection('dz', "SLS"))

abs_max_fz = max(max_fz, key=abs)
abs_max_my = max(max_my, key=abs)
abs_max_def = max(max_def, key=abs)


# Checking strength requirements
wpl_req = abs((abs_max_my * 1000 * 1000)/355) # mm3
av_req = abs((abs_max_fz * 1000)/355) # mm2

# Checking deflection requirements
multiplier = (1*1000*1000*1000*1000)*abs(abs_max_def*1000)
d_limit = (length*1000)/deflection_limit


# Creating plots
fig_envelope_shear = plots.plot_enveloped_results(beam_model, 'shear', 'Fz', 'kN', 'LC1')
fig_envelope_moment = plots.plot_enveloped_results(beam_model, 'moment', 'My', 'kNm', 'LC1')



sections = sections_db.pfi_sections()
sections['calc_def'] = multiplier/sections['Iy']

filtered_sections = sections[
    (sections['Wpl_y'] > wpl_req) & 
    (sections['Avz'] > av_req) & 
    (sections['Section name'].str.contains('UC|UB ')) &
    (sections['calc_def'] < d_limit)]

result = filtered_sections.loc[filtered_sections['kg/m'].idxmin()]

print(result['Section name'])

with col2:
    st.header('Output')
    st.write(f'Max shear: {round(abs_max_fz, 2)} kN')
    st.write(f'Max moment: {round(abs_max_my, 2)} kNm')
    st.write(f'Recommended section: {result["Section name"]}')
    st.pyplot(fig_envelope_shear)
    st.pyplot(fig_envelope_moment)
    


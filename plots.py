from matplotlib.figure import Figure
from typing import Optional
from PyNite import FEModel3D
from beams import extract_arrays_all_combos
from load_factors import envelope_min, envelope_max

def plot_enveloped_results(beam_model: FEModel3D, result_type: str, direction: Optional[str] = None, units: Optional[str] = None, load_combo: Optional[str] = None, figsize=(8,3), dpi=200, n_points=1000) -> Figure:
    """
    Returns a matplotlib figure of the analysis results in 'beam_model' according to the 'result_type' and 'direction'
    result_type: str, one of {"shear", "moment", "torque", "axial", "deflection"}
    direction: str, one of {"Fy", "Fx", "Fz"} (applicable to shear), {"Mx", "My", "Mz"} (applicable to moment), or 
        {"dx", "dy", "dz"} (applicable to deflection)
    units: if provided, will be included in figure title, default None
    load_combo: if not None, then the provided load combo will be plotted within the envelope, if present in the model.

    """
    fig = Figure(figsize=figsize, dpi=dpi)
    ax = fig.gca()
    result_arrays = extract_arrays_all_combos(beam_model, result_type=result_type.lower(), direction=direction, n_points=1000)
    x_array = list(result_arrays.values())[0][0] # X-array same across all results; get the first one

    # Plot beam line
    ax.plot(x_array, [0] * len(x_array), color='k')

    # Plot envelope
    max_result_env = envelope_max(result_arrays)
    min_result_env = envelope_min(result_arrays)
    ax.fill_between(x_array, y1=max_result_env[1], y2=min_result_env[1], fc='#E41D93', alpha=0.2)

    if load_combo is not None:
        ax.plot(x_array, result_arrays[load_combo][1], color='#E41D93')
        if units is not None:
            ax.set_title(f'Max/min {result_type} envelope w/ load combo {load_combo} ({units})')
        else:
            ax.set_title(f'Max/min {result_type} envelope w/ load combo {load_combo}')
    else:
        ax.set_title(f'Max/min {result_type} envelope')

    # Add some "padding" around the top and bottom of the plot
    ax.margins(x=0.1, y=0.1)

    # Setup the variables required for labelling
    if result_type == "shear":
        action_symbol = "VEd"
    elif result_type == "moment": 
        action_symbol = "MEd"
    elif result_type == "axial":
        action_symbol = "NEd"
    elif result_type == "torque":
        action_symbol = "TEd"
    elif result_type == "deflection":
        action_symbol = "$\Delta$"

    if max(x_array) < 1000:
        loc_precision = 1
    else:
        loc_precision = -1
    
    max_value = max(max_result_env[1])
    min_value = min(min_result_env[1])
    delta = max(abs(max_value), abs(min_value))
    results_precision = 0
    if delta < 100:
        results_precision = 2
    
    max_idx = max_result_env[1].index(max_value)
    max_value_loc = max_result_env[0][max_idx]
    ax.annotate(xy=[max_value_loc, max_value], text=f"{action_symbol}, max @ {round(max_value_loc, loc_precision)} = {round(max_value, results_precision)}")
    

    min_idx = min_result_env[1].index(min_value)
    min_value_loc = min_result_env[0][min_idx]
    ax.annotate(xy=[min_value_loc, min_value], text=f"{action_symbol}, min @ {round(min_value_loc, loc_precision)} = {round(min_value, results_precision)}")

    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    return fig
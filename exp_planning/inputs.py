from itertools import product, chain
from .utils import timeit
import pandas as pd
import numpy as np


@timeit
def create_inputs(CapsuleModel, data):
    """Create inputs for the model here.

    Arguments:
        inputs (Dict): Optional inputs, used as a dictionary of elements\
        for all the sets and parameters of the model. Every element should\
        have a key of the value of a dictionary mapping the set of indexes\
        as tuples to the desired value.
    """
    state_expr = data.state_expr
    scenarios_time = data.scenarios_time
    bat_prof = data.bat_prof
    storage = data.storage
    lines = data.lines

    inputs = {}

    # Sets defined
    inputs['R'] = [(x, y) for x in state_expr.keys() for y in state_expr[x].keys()]
    inputs['J'] = np.unique([x for y in state_expr.keys() for x in state_expr[y].keys()])
    inputs['CJ'] = [(c, j) for c in state_expr.keys() for j in state_expr[c].keys()]
    inputs['CJE'] = [(c, j, e) for c in state_expr.keys() for j in state_expr[c].keys()
                     for e in state_expr[c][j]['islands'].keys()]
    inputs['CJEH'] = [(c, j, e, h) for c in state_expr.keys()
                      for j in state_expr[c].keys() for e in state_expr[c][j]['islands'].keys()
                      for h in state_expr[c][j]['islands'][e]['storage']]
    inputs['E'] = np.unique([x for z in state_expr.keys() for y in state_expr[z].keys()
                             for x in state_expr[z][y]['islands'].keys()])
    inputs['Jc'] = dict((x, list(state_expr[x].keys())) for x in state_expr.keys())
    inputs['Ecj'] = dict(((x, y), list(state_expr[x][y]['islands'].keys()))
                         for x in state_expr.keys() for y in state_expr[x].keys())
    inputs['Hcje'] = dict(((x, y, z), list(state_expr[x][y]['islands'][z]['storage']))
                          for x in state_expr.keys() for y in state_expr[x].keys()
                          for z in state_expr[x][y]['islands'].keys())
    inputs['Dcje'] = dict(((x, y, z), list(state_expr[x][y]['islands'][z]['buses_load']))
                          for x in state_expr.keys() for y in state_expr[x].keys()
                          for z in state_expr[x][y]['islands'].keys())
    inputs['RLONcj'] = dict(((x, y), list(state_expr[x][y]['rel_on']))
                            for x in state_expr.keys() for y in state_expr[x].keys())
    inputs['RLOFFcj'] = dict(((x, y), list(state_expr[x][y]['rel_off']))
                             for x in state_expr.keys() for y in state_expr[x].keys())

    # PF sets
    x = lines.loc[lines.loc[lines.base_topology == 1].index.to_numpy()].copy()
    x['l_number'] = x.index.to_numpy()
    x_from = x.groupby('from')['l_number'].apply(list)
    x_to = x.groupby('to')['l_number'].apply(list)
    inputs['From'] = dict(zip(data.bus_tb.index, [[] for i in data.bus_tb.index]))
    inputs['To'] = dict(zip(data.bus_tb.index, [[] for i in data.bus_tb.index]))
    inputs['From'].update(dict(zip(x_from.index, x_from.values)))
    inputs['To'].update(dict(zip(x_to.index, x_to.values)))

    non_subs_bus = data.bus_tb.index.difference(data.substations.index)
    inputs['H_n'] = dict(zip(non_subs_bus, [[] for i in non_subs_bus]))
    H = storage.loc[storage.candidate == 1].index.to_numpy()
    inputs['H_n'].update(dict(zip(H, [[i] for i in (H)])))

    # Params
    inputs['f_load'] = dict(zip(
        list(zip(scenarios_time.t, scenarios_time.d, scenarios_time.scenario)),
        scenarios_time.load_factor.to_numpy()))

    inputs['f_bat'] = data.bat_prof.set_index(['H', 'T', 'D']).f_bat.to_dict()
    inputs['c_tr'] = (data.substations_cost.set_index(['substation', 'T', 'D']).c_tr_kwh * 1000
                      / (data.parameters['sbase_mva'] * 1E6)).to_dict()

    CapsuleModel.inputs = inputs


def read_csv(file, index):
    """Read csv using pandas, obtaining index and values.

    Arguments:
        index (str): Index to be used from csv file.
    Return:
        vals (dict): Dictionary of values, index as list and other values as\
        dict indexed by index column.
    """
    df = pd.read_csv(file)
    vals = {index: df[index].tolist()}
    df = df.set_index(index)
    for i in df.columns:
        vals.update({i: df[i].to_dict()})
    return vals


def array_to_dict(np_array, index=None):
    """Convert a numpy array to dictionary, with optional custom indexes.

    Arguments:
        np_array (np.array): Numpy array values.
        index (list): Optional list consisting in indexes to use for dictionary.
    Return:
        vals (dict): Dictionary of values.
    """
    if index:
        for n, i in enumerate(np_array.shape):
            assert len(index[n]) == i
        tags = product(*index)
    else:
        tags = product(*[range(i) for i in np_array.shape])
    return dict(zip(tags, sum(np_array.tolist(), [])))

from types import SimpleNamespace
import logging
import pandas as pd
import networkx as nx
from itertools import product
import numpy as np
from network import Network

logger = logging.getLogger("MAIN")


class Namespace(SimpleNamespace):
    def __repr__(self):
        return "Namespace consisting of attributes lines, bus_tb, storage, substations, " \
               "grid_states, scenarios, bat_prof, scenarios_time, line_loss, substation_loss, " \
               "days, demand_prof, substations_cost and state_expr"


def read_data_alternative(folder):

    parameters = pd.read_csv(folder + '/generalParameters.csv')
    parameters = parameters.T.to_dict()[0]

    net_inputs = {
        'branches': pd.read_csv(folder + '/branches.csv', index_col=0),
        'substations': pd.read_csv(folder + '/substations.csv', index_col=0),
        'loads': pd.read_csv(folder + '/loads.csv', index_col=0),
        'branch_candidates': pd.read_csv(folder + '/branch_candidates.csv', index_col=0),
        'storage_candidates': pd.read_csv(folder + '/storage_candidates.csv')
    }
    mv_network = Network(**net_inputs)

    hourly_profiles = {
        'profiles': pd.read_csv(folder + '/hourly_profiles.csv'),
        'day_weights': pd.read_csv(folder + '/days.csv', index_col=0)
    }

    mv_network.add_hourly_profiles(hourly_profiles)

    routine_failures = {
        'overhead_lines': (0.2, 2),
        'underground_lines': (0.1, 1),
        'substations': (0.05, 1)
    }
    mv_network.add_routine_failures(routine_failures)

    extreme_events = [
        {'branches': [1, 2, 3], 'substations': [1], 'frequency': 0.02, 'duration': 50},
        {'branches': [43, 26, 37], 'substations': [], 'frequency': 0.01, 'duration': 60}
    ]
    mv_network.add_extreme_events(extreme_events)

    mv_network.add_event_list(pd.read_csv(folder + '/list_of_events.csv', index_col=0))

    net_data = mv_network.get_data()
    data = Namespace()
    for d in net_data.keys():
        setattr(data, d, net_data[d])

    data.parameters = parameters
    data.state_expr = states_evaluation(data)
    return data


def data_from_network(net, parameters):
    net_data = net.get_data()
    data = Namespace()
    for d in net_data.keys():
        setattr(data, d, net_data[d])

    parameters = parameters.T.to_dict()[0]
    data.parameters = parameters
    data.state_expr = states_evaluation(data)

    return data


def create_graph(active_lines, nodes_tb):
    """Create graph and obtain isolated nodes."""
    network = nx.Graph()
    network.add_nodes_from(nodes_tb.index.values)
    network.add_edges_from(list(zip(active_lines['from'].values, active_lines['to'].values)))
    islands = sorted(nx.connected_components(network))
    return network, islands


def states_evaluation(data, write_eq=False):
    """Heuristic to obtain states in terms of load. Use write_eq to True
    to write equations to a file."""
    grid_states = data.grid_states
    line_tb = data.lines
    bus_tb = data.bus_tb
    if write_eq:
        text_file = open("states_model.txt", "w")
        equation_file = open("equations_model.txt", "w")

    state_expr = {}

    candidate_lines = line_tb.loc[line_tb.candidate == 1].copy()
    states = grid_states.keys()

    for state in states:
        print('Evaluating state: ', state)
        state_lines = line_tb.loc[grid_states[state] * line_tb.existing == 1].copy()
        state_network, state_clusters = create_graph(state_lines, bus_tb)

        primary_connection = np.array([bus_tb.loc[list(cluster)].g_tr_max_kw.sum() for cluster in state_clusters])
        isolated_clusters = np.where(primary_connection == 0)[0]
        connected_buses = set().union(*np.delete(state_clusters, isolated_clusters))

        # getting the relevant line candidates
        # that connect isolated clusters to connected nodes

        relevant_candidates_idx = []
        for ic_idx in isolated_clusters:
            connecting_lines_fr = candidate_lines.loc[
                candidate_lines['from'].isin(state_clusters[ic_idx]) &
                candidate_lines['to'].isin(connected_buses)]

            connecting_lines_to = candidate_lines.loc[
                candidate_lines['from'].isin(connected_buses) &
                candidate_lines['to'].isin(state_clusters[ic_idx])]

            relevant_candidates_idx = np.concatenate([relevant_candidates_idx,
                                                      connecting_lines_fr.index,
                                                      connecting_lines_to.index])

        relevant_candidates = candidate_lines.loc[relevant_candidates_idx]

        combination_matrix = list(product([0, 1], repeat=len(relevant_candidates)))

        # writing expression for no-investments
        if write_eq:
            text_file.write("\n grid state: %s\n" % state)
            text_file.write("info: relevant line investments %s\n" % relevant_candidates_idx)
        expr = load_curtailment_expr(state_clusters, bus_tb)
        if expr and write_eq:
            text_file.write("---> no_investment\n")
            write_expr(expr, text_file)
            write_equations (expr, equation_file, relevant_candidates_idx, combination_matrix[0], state)
        state_expr.update({state: {0: {'rel_on': [], 'rel_off': relevant_candidates_idx, 'islands': expr}}})

        # writing expression for investment cases
        for idx_row, row in enumerate(combination_matrix[1:]):
            inv = row*relevant_candidates_idx
            inv = inv[inv != 0]
            cnd = relevant_candidates.loc[inv]
            state_inv_net = state_network.copy()
            state_inv_net.add_edges_from(list(cnd[['from', 'to']].itertuples(index=False, name=None)))
            expr = load_curtailment_expr(sorted(nx.connected_components(state_inv_net)), bus_tb)

            if expr:
                if write_eq:
                    text_file.write(f'---> investment in lines {str(inv)} \n')
                    write_expr(expr, text_file)
                    write_equations(expr, equation_file, relevant_candidates_idx, row, state)
                state_expr[state].update({idx_row+1: {'rel_on': inv, 'rel_off': np.setxor1d(
                    relevant_candidates_idx, inv), 'islands': expr}})

    if write_eq:
        text_file.close()
        equation_file.close()
    return state_expr


def load_curtailment_expr(clusters, buses_tb, reduced=True):
    curt_expr = {}
    island_no = 0
    for cluster_idx, cluster in enumerate(clusters):
        cluster_buses = buses_tb.loc[list(cluster)].copy()
        cluster_total = cluster_buses.sum()
        substation_max = cluster_total.g_tr_max_kw

        if reduced and cluster_total.peakDemand_kw <= substation_max:
            pass
        else:
            curt_expr.update({island_no:
                {'storage': cluster_buses.loc[cluster_buses.candidate == 1].index.values,
                 'substation': substation_max,
                 'buses_load': cluster_buses.index.values}}
            )
            island_no += 1
    # If there is no island and everything is connected
    if curt_expr == {}:
        curt_expr.update({island_no:
            {'storage': [],
             'substation': 0,
             'buses_load': []}}
        )
    return curt_expr


def write_expr(expr, file):
    file.write(f'load_curt =')
    expr_keys = list(expr.keys())
    first_row = expr[expr_keys[0]]
    file.write(f'sum_load({str(first_row["buses_load"])}) -  '
        f'sum_storage_soc({str(first_row["storage"])}) - {str(first_row["substation"])}')

    for k in expr_keys[1:]:
        row = expr[k]
        file.write(f'\n sum_load({str(row["buses_load"])}) -  '
                   f'sum_storage_soc({str(row["storage"])}) - {str(row["substation"])}')
    file.write(f'\n')


def write_equations(expr, file, inv, matrix, state):
    file.write(f'load_curt {state} =')
    expr_keys = list(expr.keys())
    first_row = expr[expr_keys[0]]
    file.write(f'sum_load({str(first_row["buses_load"])}) -  '
               f'sum_storage_soc({str(first_row["storage"])}) - {str(first_row["substation"])}')

    for k in expr_keys[1:]:
        row = expr[k]
        file.write(f' + sum_load({str(row["buses_load"])}) -  '
                   f'sum_storage_soc({str(row["storage"])}) - {str(row["substation"])}')

    if matrix:
        file.write(f'   if   ')
        for i in enumerate(inv):
            file.write(f'  X_{int(i[1])}=({matrix[i[0]]})')

    file.write(f'\n')

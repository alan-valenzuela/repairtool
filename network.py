import pandas as pd
from itertools import product
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


class Network:

    def __init__(self, branches, substations, loads, **kwargs):

        self.branches = branches

        # base topology are the branches that do not have switches + normally_closed switches
        self.branches['base_topology'] = branches.switch \
                                         * branches.switch_nc + (1 - branches.switch)
        self.substations = substations
        self.loads = loads

        self.all_branches = branches

        # time expansion
        self.hourly_profiles = {}
        self.weight_days = {}

        # candidates
        self.candidate_storage = pd.DataFrame()
        self.candidate_branches = pd.DataFrame()
        if 'branch_candidates' in kwargs:
            self.update_branch_candidates(kwargs['branch_candidates'])

        if 'storage_candidates' in kwargs:
            self.update_storage_candidates(kwargs['storage_candidates'])

        # bus coordinates
        self.bus_coordinates=pd.DataFrame()
        # reliability and resilience variables
        self.failure_events, self.extreme_failures, self.event_list = {}, {}, {}

    def add_hourly_profiles(self, hp):

        prof = hp['profiles']
        profiles = {}
        for t in prof['type'].unique():
            profiles.update({f'{t}': prof.loc[prof.type == f'{t}'].
                            reset_index(drop=True).drop('type', axis=1)})

        if 'day_weights' in hp.keys():
            days = hp['day_weights']
        else:
            n_days = prof['day'].unique()
            days = pd.DataFrame(n_days, columns=['days']).set_index('days')
            days['weight'] = 365.0/len(n_days)

        self.hourly_profiles = profiles
        self.weight_days = days

    def add_routine_failures(self, rf, rewrite=True):

        if rewrite:
            self.failure_events = {}
        br = self.branches
        lines = pd.DataFrame()

        if 'underground_lines' in rf.keys():
            ug = br.loc[br.OH == 0].reset_index()[['branch_index']]
            ug[['frequency', 'duration']] = rf['underground_lines']
            lines = pd.concat([lines, ug])

        if 'overhead_lines' in rf.keys():
            oh = br.loc[br.OH == 1].reset_index()[['branch_index']]
            oh[['frequency', 'duration']] = rf['overhead_lines']
            lines = pd.concat([lines, oh])

        lines = lines.rename(columns={'branch_index': 'branches'})
        lines['state'] = 'LN_R_' + lines['branches'].astype(str)
        lines['branches'] = lines['branches'].apply(lambda x: [x])
        lines['routine'] = 1

        self.failure_events.update(lines.set_index('state').T.to_dict())

        if 'substations' in rf.keys():
            sbs = self.substations['bus'].reset_index()
            sbs['substation_index'] = 'S_R_' + sbs['substation_index'].astype(str)
            sbs[['frequency', 'duration']] = rf['substations']
            sbs['branches'] = sbs['bus'].apply(lambda bus: br.loc[
                (br.from_bus == bus) | (br.to_bus == bus)].index.to_list())
            sbs['routine'] = 1
            self.failure_events.update(
                sbs.drop('bus', axis=1).set_index('substation_index').T.to_dict())

    def add_event_list(self, event_list, rewrite=True):
        if rewrite:
            self.event_list = {}

        for k in ['branches', 'substations']:
            event_list[k] = event_list[k].fillna(-1).apply(
                lambda x: [] if x == -1 else [int(float(s)) for s in str(x).split(',')])
        event_list['routine'] = 1
        event_list['event'] = event_list.index.to_series().apply(lambda x: 'EVT_' + str(x))

        events =event_list.set_index('event').T.to_dict()

        br = self.branches
        for n, n_ev in enumerate(events.keys()):
            ev = events[n_ev]
            # converting substations to branches
            sbs = self.substations.loc[ev['substations']]
            lines = sbs['bus'].apply(lambda bus: br.loc[
                (br.from_bus == bus) | (br.to_bus == bus)].index.to_list()).to_list()
            branches = [l for sl in lines for l in sl] + ev['branches']

            # updating event and adding to the list
            ev['branches'] = list(set(branches))
            ev.pop('substations')

            self.event_list.update({n_ev: ev})

    def add_extreme_events(self, extreme_events, rewrite=True):

        if rewrite:
            self.extreme_failures = {}

        br = self.branches
        for n, ev in enumerate(extreme_events):
            # converting substations to branches
            sbs = self.substations.loc[ev['substations']]
            lines = sbs['bus'].apply(lambda bus: br.loc[
                (br.from_bus == bus) | (br.to_bus == bus)].index.to_list()).to_list()
            branches = [l for sl in lines for l in sl] + ev['branches']

            # updating event and adding to the list
            ev['branches'] = list(set(branches))
            ev.pop('substations')
            ev.update({'routine': 0})
            self.extreme_failures.update({f'HILP_{n}': ev})

    def get_data(self):

        # update failures list and get states and scenarios
        if len(self.event_list) > 0:
            self.failure_events.update(self.event_list)
        if len(self.extreme_failures) > 0:
            self.failure_events.update(self.extreme_failures)
        grid_states, scenarios = self._state_scenarios()

        br = self.branches

        # prepare bus table
        buses = pd.DataFrame(pd.concat([br.from_bus, br.to_bus]).unique(), columns=['bus'])
        buses[['v_min', 'v_max']] = [0.95, 1.05]
        sc = self.candidate_storage
        sc['candidate'] = 1
        for df in [self.loads, self.substations, sc]:
            buses = pd.merge(buses, df, how='outer').fillna(0)
        bus_tb = buses.set_index('bus').sort_index()

        # expand profiles
        def expand_profile(p, label):
            p = p.set_index('day').T.reset_index().rename(columns={'index': 'T'})
            p['T'] = p['T'].apply(lambda s: int(s[1:]))
            p = p.set_index('T')
            p_ext = pd.DataFrame()
            for d in p.keys():
                df = pd.DataFrame(p[d].rename(label))
                df['D'] = d
                p_ext = pd.concat([p_ext, df])
            return p_ext.reset_index()
        # expand storage
        bat_p = expand_profile(self.hourly_profiles['battery_soc'], 'f_bat')
        bat_prof = pd.DataFrame()
        for h in self.candidate_storage.bus.unique():
            bat_p['H'] = h
            bat_prof = pd.concat([bat_prof, bat_p])
        # expand substation_costs
        sub_c = expand_profile(self.hourly_profiles['costs_dol_kWh'], 'c_tr_kwh')
        sub_cost = pd.DataFrame()
        for s in self.substations.bus.unique():
            sub_c['substation'] = s
            sub_cost = pd.concat([sub_cost, sub_c])
        # expand demand profile
        demand_prof = self.hourly_profiles['demand_profile']
        dp = expand_profile(self.hourly_profiles['demand_profile'], 'load_factor')

        # scenarios time
        scenarios_time = pd.merge(
            pd.DataFrame(product(demand_prof.day.to_numpy(), list(range(24)),
                                 scenarios['state']),
                         columns=['d', 't', 'state']), scenarios.reset_index(), on='state')

        scenarios_time = scenarios_time.merge(dp.rename(columns={'T': 't', 'D': 'd'}))

        data = {'substations': self.substations.set_index('bus'),
                'lines': self.all_branches.rename(columns={'from_bus': 'from', 'to_bus': 'to',
                                                    'max_ka': 'f_max_ka'}).copy(),
                'grid_states': grid_states,
                'scenarios': scenarios,
                'bus_tb': bus_tb,
                'demand_prof': demand_prof.drop('day', axis=1),
                'bat_prof': bat_prof,
                'substations_cost': sub_cost.reset_index()[['substation', 'T', 'D', 'c_tr_kwh']],
                'days': self.weight_days,
                'scenarios_time': scenarios_time,
                'storage': self.candidate_storage.set_index('bus')
                }

        return data

    def _state_scenarios(self):
        """
        Transforms the grid failures into the grid_states
        scenarios of the REPAIR format
        """
        br = self.all_branches
        grid_states = pd.DataFrame()
        grid_states['state_0'] = br['base_topology']

        # unique states:
        fe = pd.DataFrame(self.failure_events).T

        fe['state'] = fe['branches'].apply(lambda x: tuple(x))
        f_st = pd.DataFrame(fe['state'].unique(), columns=['lines_out']).reset_index()
        f_st['index'] = 'state_' + (f_st['index']+1).astype('str')
        map_states = f_st.set_index('lines_out')['index'].to_dict()
        # for some reason the next does not work with .map
        fe['state'] = [map_states[x] for x in fe['state']]

        def top(ln_out):
            """gets a list of lines out and returns the base topology vector"""
            top_state = br['base_topology'].copy()
            top_state.loc[ln_out] = 0
            return top_state

        grid_states[f_st['index']] = f_st.lines_out.apply(top).T

        fe['probability'] = fe.frequency / 8760.0

        cols = ['state', 'probability', 'duration', 'routine']
        scenarios = pd.DataFrame([['state_0', 1 - fe['probability'].sum(), 1, 1]], columns=cols)
        scenarios = pd.concat([scenarios, fe[cols]])
        scenarios.index.names = ['scenario']

        return grid_states, scenarios

    def _update_branch_candidates(self):
        candidate_branches = self.candidate_branches.rename(
            columns={'max_ka': 'f_cand_max'})
        candidate_branches[['candidate', 'switch']] = 1
        self.candidate_branches = candidate_branches

        all_branches = pd.concat([self.branches, candidate_branches]).fillna(0)
        all_branches = all_branches.reset_index(drop=True)
        self.all_branches = all_branches

    def visualize(self):
        branches = self.branches.copy()
        substations = self.substations[['bus']].copy()
        substations['is_substation'] = 1
        loads = self.loads
        loads['is_load'] = 1
        if self.candidate_storage.shape[0] == 0:  # in case there are not storage candidates
            storage_cd = pd.DataFrame(columns=['bus'])
        else:
            storage_cd = self.candidate_storage.copy()
        storage_cd['is_st_cd'] = 1
        if 'capacity' not in storage_cd.keys():  # contemplating storage investments
            storage_cd['capacity'] = 0

        buses = pd.DataFrame(pd.concat([branches['from_bus'], branches['to_bus']]
                                       ).unique(), columns=['bus'])
        buses = buses.merge(loads, how='outer'
                            ).merge(substations, how='outer'
                                    ).merge(storage_cd, how='outer').fillna(0).set_index('bus').sort_index()

        def node_color(n):
            if n.is_st_cd == 1:
                if n.capacity > 0:
                    return 'red'
                else:
                    return 'orange'
            elif n.is_substation == 1:
                return '#0E51F7'
            elif n.is_load == 1:
                return '#eeefff'
            else:
                return '#eeefff'# we can change this color to distinguish load and non-load nodes

        buses['color_map'] = buses.apply(node_color, axis=1)

        # create graph and add nodes
        G = nx.Graph()
        G.add_nodes_from(list(buses.index))
 

        # add edges
        edges = branches[['from_bus', 'to_bus']].to_records(index=False)
        G.add_edges_from(edges, color='#eeefff')
        if self.candidate_branches.shape[0] > 0:  # add candidate edges
            br = self.all_branches
            cd_edges = br.loc[br.candidate == 1]
            if 'invest' in cd_edges.keys():
                cd_invest = cd_edges.loc[cd_edges.invest == 1][['from_bus', 'to_bus']].to_records(index=False)
                G.add_edges_from(cd_invest, color='red')
                cd_edges = cd_edges.loc[cd_edges.invest == 0]
            G.add_edges_from(cd_edges[['from_bus', 'to_bus']].to_records(index=False), color='#FDD8A4')
        edge_colors = [G[u][v]['color'] for u, v in G.edges]

        # p plot
        plt.show(block=False)
        plt.ion()

        # defining the postition to plot
        if self.bus_coordinates.shape[0] > 0:
            pos = dict(zip(self.bus_coordinates.bus, zip(self.bus_coordinates.x, self.bus_coordinates.y)))
        else:
            pos = nx.spring_layout(G, seed=100)
        nx.draw(G,
                node_color=buses['color_map'].to_list(),
                edge_color=edge_colors,
                pos=pos,
                node_size=8)

        # drawing legend
        lg_lbl = {
            'branches': Line2D([], [], color='#eeefff', marker='_'),
            'nodes': Line2D([], [], color="white", marker='o', markerfacecolor='#eeefff'),
            'substations': Line2D([], [], color="white", marker='o', markerfacecolor="#0E51F7")
        }
        if self.candidate_storage.shape[0] > 0:
            lg_lbl.update({'storage candidates': Line2D([], [], color="white",
                                                        marker='o', markerfacecolor="orange")})
        if self.candidate_branches.shape[0] > 0:
            lg_lbl.update({'line candidates': Line2D([], [], color='#FDD8A4', marker='_')})

        if 'capacity' in self.candidate_storage.keys():
            lg_lbl.update({'storage investments': Line2D([], [], color="white",
                                                         marker='o', markerfacecolor="red")})
        if 'invest' in self.all_branches.keys():
            lg_lbl.update({'line investments': Line2D([], [], color='red', marker='_')})

        lbl_keys = tuple(lg_lbl.keys())
        plt.legend(tuple(lg_lbl[l] for l in lbl_keys), lbl_keys, loc="lower left", ncol=4)

        return plt

    def update_storage_candidates(self, storage_candidates):
        storage_candidates['existing'] = 0
        self.candidate_storage = storage_candidates

    def update_branch_candidates(self, branch_candidates):
        if 'existing' not in self.branches.keys():
            self.branches['existing'] = 1
        self.candidate_branches = branch_candidates
        self._update_branch_candidates()

    def add_bus_coordinates(self, coordinates):
        self.bus_coordinates = coordinates

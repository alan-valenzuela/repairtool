from .utils import Set, timeit


@timeit
def create_sets(CapsuleModel, data):
    """Define pyomo sets here."""
    m = CapsuleModel.model
    lines = data.lines
    storage = data.storage
    scenarios = data.scenarios
    state_expr = data.state_expr
    days = data.days
    bus_tb = data.bus_tb
#    substation_loss = data.substation_loss
#    line_loss = data.line_loss

    inputs = CapsuleModel.inputs

    m.L = Set(initialize=lines.index.to_numpy())
    m.L_c = Set(initialize=lines.loc[lines.candidate == 1].index.to_numpy())
    m.L_e = Set(initialize=lines.loc[lines.existing == 1].index.to_numpy())
    m.L_bt = Set(initialize=lines.loc[lines.base_topology == 1].index.to_numpy())
    m.H = Set(initialize=storage.index.to_numpy())
    m.H_c = Set(initialize=storage.loc[storage.candidate == 1].index.to_numpy())
    m.H_e = Set(initialize=storage.loc[storage.existing == 1].index.to_numpy())
    m.C = Set(initialize=list(state_expr.keys()))
    m.S = Set(initialize=scenarios.index.to_numpy())
    m.S_routine = Set(initialize=scenarios.loc[scenarios.routine == 1].index.to_numpy())
    m.S_hilp = Set(initialize=scenarios.loc[scenarios.routine != 1].index.to_numpy())
    m.S_dur = Set(m.S, initialize=scenarios.duration.map(lambda x: range(int(x))).to_dict())

    m.D = Set(initialize=days.index.to_numpy())
    m.T = Set(initialize=list(range(24)))
    m.N = Set(initialize=bus_tb.index.to_numpy())
    m.N_SS = Set(initialize=bus_tb.loc[bus_tb.g_tr_max_kw > 0].index.to_numpy())  # substation busses
    m.R = Set(initialize=inputs['R'])

    m.J = Set(initialize=inputs['J'])
    m.E = Set(initialize=inputs['E'])

    m.CJ = Set(initialize=inputs['CJ'])
    m.CJE = Set(initialize=inputs['CJE'])
    m.CJEH = Set(initialize=inputs['CJEH'])

    # Index sets for summation only
    m.Jc = Set(m.C, initialize=inputs['Jc'])
    m.Ecj = Set(m.C, m.J, initialize=inputs['Ecj'])
    m.Hcje = Set(m.C, m.J, m.E, initialize=inputs['Hcje'])
    m.Dcje = Set(m.C, m.J, m.E, initialize=inputs['Dcje'])
    m.RLONcj = Set(m.C, m.J, initialize=inputs['RLONcj'])
    m.RLOFFcj = Set(m.C, m.J, initialize=inputs['RLOFFcj'])

#    m.nJ_ss = Set(initialize=substation_loss.index.to_numpy())
#    m.nJ_l = Set(initialize=line_loss.index.to_numpy())
    m.N_load = m.N - m.N_SS
    m.H_n = Set(m.N_load, initialize=inputs['H_n'])
    m.From = Set(m.N, initialize=inputs['From'])
    m.To = Set(m.N, initialize=inputs['To'])

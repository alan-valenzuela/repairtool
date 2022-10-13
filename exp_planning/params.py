from .utils import Param, timeit
from itertools import product
from pyomo.environ import Any


@timeit
def create_params(CapsuleModel, data):
    """Define pyomo parameters here."""
    m = CapsuleModel.model
    inputs = CapsuleModel.inputs
    lines = data.lines
    storage = data.storage
    scenarios = data.scenarios
    bus_tb = data.bus_tb
    days = data.days
#    substation_loss = data.substation_loss
#   line_loss = data.line_loss
    demand_prof = data.demand_prof

    m.sc_state = Param(m.S, initialize=dict(zip(scenarios.index, scenarios.state)), within=Any)
    m.s_prob = Param(m.S, initialize=scenarios['probability'].to_dict())
    m.f_load = Param(m.T, m.D, m.S, initialize=inputs['f_load'])
    m.f_bat = Param(m.H, m.T, m.D, initialize=inputs['f_bat'])

    m.d_peak = Param(m.N, initialize=dict(zip(bus_tb.index.to_numpy(),
                                              bus_tb.peakDemand_kw * 1E3 / (data.parameters['sbase_mva'] * 1E6))))

    disc_rate = data.parameters['discount_rate']
    cand_lines = lines.loc[m.L_c]
    c_fix_l = cand_lines.c_fix_usd * disc_rate / (1-(cand_lines.lifetime*0+1 + disc_rate).pow(-cand_lines.lifetime))
    m.c_fix_l = Param(m.L_c, initialize=c_fix_l.to_dict())
    m.alpha_reg = Param(m.L, initialize=lines['alpha'].to_dict())

    cand_stor = storage.loc[m.H]
    c_SD_fix = cand_stor.c_SD_fix_usd * disc_rate / (1-(cand_stor.lifetime*0+1 + disc_rate).pow(-cand_stor.lifetime))
    # Cost are in $USD/KWh, translate it to $USD/pu
    c_SD_var = cand_stor.c_SD_var_usd_kwh * (data.parameters['sbase_mva'] * 1E6) / 1E3 / cand_stor.s_charge
    c_SD_var = c_SD_var * disc_rate / (1-(cand_stor.lifetime*0+1 + disc_rate).pow(-cand_stor.lifetime))
    m.c_sd_fix = Param(m.H, initialize=c_SD_fix.to_dict())
    m.c_sd_var = Param(m.H, initialize=c_SD_var.to_dict())

    m.s = Param(m.H, initialize=storage.loc[m.H].s_charge.to_dict())
    m.eff = Param(m.H, initialize=storage.loc[m.H].eff.to_dict())
    # m.sd_max = Param(m.H, initialize=(storage.loc[m.H].sd_max_kw / (data.parameters['sbase_mva'] * 1E6) * 1E3).to_dict())
    m.sd_max = Param(m.H, initialize=(storage.loc[m.H].sd_max).to_dict())

    m.p_in_max = Param(m.H, initialize=(storage.loc[m.H].p_in_max_kw * 1E3 / (data.parameters['sbase_mva'] * 1E6)).to_dict())
    m.p_out_max = Param(m.H, initialize=(storage.loc[m.H].p_out_max_kw * 1E3 / (data.parameters['sbase_mva'] * 1E6)).to_dict())

    m.w = Param(m.D, initialize=days['weight'].to_dict())

    m.c_imb = data.parameters['c_imb_usd_kwh'] / 1E3 * data.parameters['sbase_mva'] * 1E6
    m.M = data.parameters['bigM']
    m.lbd = data.parameters['lambda']
    m.alpha_cvar = data.parameters['alpha_cvar']
    m.pf = data.parameters['pf']

    m.g_tr_max = Param(m.N_SS, initialize=dict(zip(m.N_SS, (bus_tb.loc[list(m.N_SS)].g_tr_max_kw
                                                            * 1E3 / (data.parameters['sbase_mva'] * 1E6)))))
    """
    m.beta_tr_max = Param(m.N_SS, m.nJ_ss,
                          initialize=dict(zip(list(product(m.N_SS, m.nJ_ss )),
                                              list(substation_loss.loc[m.nJ_ss].betaGen_max)*len(m.N_SS))))

    m.beta_l_max = Param(m.L_bt, m.nJ_l,
                         initialize=dict(zip(list(product(m.L_bt, m.nJ_l)),
                                             list(line_loss.loc[m.nJ_l].betaLine_max)*len(m.L_bt))))
    """

    m.v_max = Param(m.N, initialize=dict(zip(m.N, bus_tb.loc[m.N].v_max)))
    m.v_min = Param(m.N, initialize=dict(zip(m.N, bus_tb.loc[m.N].v_min)))
    zbase = (data.parameters['vbase_kv'] * 1E3) ** 2 / (data.parameters['sbase_mva'] * 1E6)
    m.z = Param(m.L_bt, initialize=dict(zip(m.L_bt, lines.loc[m.L_bt].Z_ohm_km / zbase)))
    m.length = Param(m.L_bt, initialize=dict(zip(m.L_bt, lines.loc[m.L_bt].r_len_km)))
    ibase = (data.parameters['sbase_mva'] * 1E6) / (data.parameters['vbase_kv'] * 1E3)
    m.f_max = Param(m.L_bt, initialize=dict(zip(m.L_bt, (lines.loc[m.L_bt].f_max_ka * 1000 / ibase))))
    m.fr = Param(m.L_bt, initialize=lines.loc[m.L_bt]['from'].to_dict())
    m.to = Param(m.L_bt, initialize=lines.loc[m.L_bt]['to'].to_dict())
    m.y_l = Param(m.L_bt, m.T, m.D, initialize=1)

    demand_prof.columns = list(range(24))
    m.demand = Param(m.T, m.D, initialize=demand_prof.transpose().stack().to_dict())

from pyomo.environ import Objective
from .utils import timeit


@timeit
def create_objective(CapsuleModel):
    """Create objective function adding expressions."""
    m = CapsuleModel.model

    m.line_costs = line_costs(m)
    m.bat_costs = bat_costs(m)
    m.imb_costs = imb_costs(m)
    m.load_shedding_island_costs = load_shedding_island_costs(m)
    m.cvar_costs = cvar_costs(m)

    m.obj = Objective(rule=lambda m: m.line_costs + m.bat_costs +
                      m.load_shedding_island_costs + m.imb_costs + m.cvar_costs)


def line_costs(m):
    return sum(m.c_fix_l[l] * m.x_fix_l[l] for l in m.L_c)


def bat_costs(m):
    return sum(m.c_sd_fix[h] * m.x_sd[h] +
               m.c_sd_var[h] * m.x_sd_var[h] * m.p_in_max[h] for h in m.H)


def imb_costs(m):
    return sum(m.w[d] * m.pf * m.c_imb *
               sum(m.delta_minus[n, t, d] + m.delta_plus[n, t, d]
                   for n in m.N_load for t in m.T)
               for d in m.D)


def load_shedding_island_costs(m):
    return (1-m.lbd) * m.pf * m.c_imb * sum(
        m.w[d] * sum(m.s_prob[s] * m.l_tds[t, d, s] for t in m.T for s in m.S)
        for d in m.D)


def cvar_costs(m):
    return m.lbd * m.pf * m.c_imb * sum(m.w[d] * sum(
        m.zeta[t, d] + sum(m.s_prob[s]/(1-m.alpha_cvar) * m.phi_cvar[t,d,s] for s in m.S)
                              for t in m.T)
        for d in m.D)


# Not being used currently
def supply_costs(m):
    return sum(m.w[d] *
               sum(m.pf *
                   sum(m.c_tr[n, t, d] * m.g_tr[n, t, d] for n in m.N_SS)
                   for t in m.T)
               for d in m.D)

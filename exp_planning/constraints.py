from pyomo.environ import Constraint
from .utils import timeit


@timeit
def create_constraints(CapsuleModel):
    """Add constraints to model. Define rules for constraints in this files"""
    m = CapsuleModel.model
    cvar_constraints(m)
    inv_constraints(m)
    op_constraints(m)
    storage_inv_constraints(m)
    storage_constraints(m)


def cvar_constraints(m):
    m.c2 = Constraint(m.T, m.D, m.S, rule=c2)
    m.c4 = Constraint(m.T, m.D, m.S_routine, rule=c4)
    m.c5 = Constraint(m.T, m.D, m.S_hilp, rule=c5)
    # Might enforce this with no load shedding
    # m.c7 = Constraint(m.T, m.D, rule=c7)


def inv_constraints(m):
    m.c8 = Constraint(m.C, rule=c8)
    m.c9a = Constraint(m.CJ, rule=c9a)
    m.c9b = Constraint(m.CJ, rule=c9b)
    # m.c9c = Constraint(m.CJ, rule=c9c)
    m.c10a = Constraint(m.CJEH, rule=c10a)
    m.c10b = Constraint(m.CJEH, rule=c10b)
    m.c11a = Constraint(m.CJEH, rule=c11a)
    m.c11b = Constraint(m.CJEH, rule=c11b)
    m.c12a = Constraint(m.CJE, rule=c12a)
    m.c12b = Constraint(m.CJE, rule=c12b)


def op_constraints(m):
    m.c14 = Constraint(m.N_SS, m.T, m.D, rule=c14)
    # Old losses constraints
    # m.c15 = Constraint(m.N_SS, m.T, m.D, rule=c15)
    # m.c16 = Constraint(m.N_SS, m.nJ_ss, m.T, m.D, rule=c16)
    # m.c17 = Constraint(m.L_bt, m.T, m.D, rule=c17)
    # m.c18 = Constraint(m.L_bt, m.T, m.D, rule=c18)
    # m.c19 = Constraint(m.L_bt, m.nJ_l, m.T, m.D, rule=c19)
    m.c15a = Constraint(m.N, m.T, m.D, rule=c15a)
    m.c15b = Constraint(m.N, m.T, m.D, rule=c15b)
    m.c16a = Constraint(m.L_bt, m.T, m.D, rule=c16a)
    m.c16b = Constraint(m.L_bt, m.T, m.D, rule=c16b)
    m.c18 = Constraint(m.N_SS, m.T, m.D, rule=c18)
    # Enforcing max limit on V
    if m.FIX_V_SLACK:
        m.c18b = Constraint(m.T, m.D, m.N_SS, m.N_SS, rule=c18b)
    m.c19 = Constraint(m.N_load, m.T, m.D, rule=c19)
    m.c20a = Constraint(m.L_bt, m.T, m.D, rule=c20a)
    m.c20b = Constraint(m.L_bt, m.T, m.D, rule=c20b)


def storage_constraints(m):
    m.c21 = Constraint(m.H, m.D, rule=c21)
    m.c22_23 = Constraint(m.H, m.T, m.D, rule=c22_23)
    m.c24 = Constraint(m.H_e, rule=c24)
    m.c26 = Constraint(m.H, m.T, m.D, rule=c26)
    m.c27 = Constraint(m.H_e, m.T, m.D, rule=c27)
    m.c28 = Constraint(m.H_e, m.T, m.D, rule=c28)


def storage_inv_constraints(m):
    m.c25 = Constraint(m.H_c, rule=c25)
    m.c29 = Constraint(m.H_c, m.T, m.D, rule=c29)
    m.c30 = Constraint(m.H_c, m.T, m.D, rule=c30)
    m.c31 = Constraint(m.H_c, rule=c31)


def c2(m, t, d, s):
    return m.phi_cvar[t, d, s] + m.zeta[t, d] >= m.l_tds[t, d, s]


def c4(m, t, d, s):
    c = m.sc_state[s]
    # fl = m.f_load[t, d, s]
    return m.l_tds[t, d, s] >= sum(
        sum(m.l_cje[c, j, e] * m.f_load[t+tau, d, s]
            for tau in m.S_dur[s] if t + tau <= max(m.T))
        - sum(m.soc_aux[c, j, e, h] * m.f_bat[h, t, d]
              for h in m.Hcje[c, j, e])
        for j in m.Jc[c] for e in m.Ecj[c, j])


def c5(m, t, d, s):
    c = m.sc_state[s]
    # fl = m.f_load[t, d, s]
    return m.l_tds[t, d, s] >= sum(
        sum(m.l_cje[c, j, e] * m.f_load[t+tau, d, s]
            for tau in m.S_dur[s] if t + tau <= max(m.T))
        - sum(m.soc_aux[c, j, e, h]
              for h in m.Hcje[c, j, e])
        for j in m.Jc[c] for e in m.Ecj[c, j])


def c7(m, t, d):
    return m.l_tds[t, d, 0] == 0


def c8(m, c):
    return sum(m.x_ind[c, j] for j in m.Jc[c]) == 1


def c9a(m, c, j):
    return - m.M * sum((1 - m.x_fix_l[l]) for l in m.RLONcj[c, j]) \
           - m.M * sum((m.x_fix_l[l]) for l in m.RLOFFcj[c, j]) <= m.x_ind[c, j] - 1


def c9b(m, c, j):
    return m.M * sum((1 - m.x_fix_l[l]) for l in m.RLONcj[c, j]) \
           + m.M * sum((m.x_fix_l[l]) for l in m.RLOFFcj[c, j]) >= m.x_ind[c, j] - 1


def c9c(m, c, j):
    return sum((1 - m.x_fix_l[l]) for l in m.RLONcj[c, j]) \
           + sum((m.x_fix_l[l]) for l in m.RLOFFcj[c, j]) <= m.M * (1 - m.x_ind[c, j])


def c10a(m, c, j, e, h):
    return -m.M * (1 - m.x_ind[c, j]) <= m.soc_ref[h] - m.soc_aux[c, j, e, h]


def c10b(m, c, j, e, h):
    return m.soc_ref[h] - m.soc_aux[c, j, e, h] <= m.M * (1 - m.x_ind[c, j])


def c11a(m, c, j, e, h):
    return -m.M * m.x_ind[c, j] <= m.soc_aux[c, j, e, h]


def c11b(m, c, j, e, h):
    return m.soc_aux[c, j, e, h] <= m.M * m.x_ind[c, j]


def c12a(m, c, j, e):
    return -m.M * (1 - m.x_ind[c, j]) <= sum(m.d_peak[i] for i in m.Dcje[c, j, e]) - m.l_cje[c, j, e]


def c12b(m, c, j, e):
    return sum(m.d_peak[i] for i in m.Dcje[c, j, e]) - m.l_cje[c, j, e] <= m.M * (1 - m.x_ind[c, j])


def c14(m, n, t, d):
    return m.g_tr[n, t, d] <= m.g_tr_max[n]

#
# def c15(m, n, t, d):
#     return m.g_tr[n, t, d] == sum(m.beta_tr[n, j, t, d] for j in m.nJ_ss)


# def c16(m, n, j, t, d):
#     return m.beta_tr[n, j, t, d] <= m.beta_tr_max[n, j]
#
#
# def c17(m, l, t, d):
#     return sum(m.beta_l[l, j, t, d] for j in m.nJ_l) >= m.f_l[l, t, d]
#
#
# def c18(m, l, t, d):
#     return sum(m.beta_l[l, j, t, d] for j in m.nJ_l) >= - m.f_l[l, t, d]
#
#
# def c19(m, l, j, t, d):
#     return m.beta_l[l, j, t, d] <= m.beta_l_max[l, j]
#

def c15a(m, n, t, d):
    return m.v[n, t, d] >= m.v_min[n]


def c15b(m, n, t, d):
    return m.v[n, t, d] <= m.v_max[n]


def c16a(m, l, t, d):
    return - m.y_l[l, t, d] * m.f_max[l] <= m.f_l[l, t, d]


def c16b(m, l, t, d):
    return m.f_l[l, t, d] <= m.y_l[l, t, d] * m.f_max[l]


def c18(m, n, t, d):
    return sum(m.f_l[l, t, d] for l in m.To[n]) \
           - sum(m.f_l[l, t, d] for l in m.From[n]) + m.g_tr[n, t, d] == 0


def c18b(m, t, d, n1, n2):
    if n1 < n2:
        return m.v[n1, t, d] == m.v[n2, t, d]
    else:
        return Constraint.Skip


def c19(m, n, t, d):
    return sum(m.f_l[l, t, d] for l in m.To[n]) \
           - sum(m.f_l[l, t, d] for l in m.From[n]) \
           == sum(m.p_in[h, t, d] - m.p_out[h, t, d] for h in m.H_n[n]) \
           - m.delta_minus[n, t, d] + m.delta_plus[n, t, d] + m.demand[t,d] * m.d_peak[n]


def c20a(m, l, t, d):
    return -m.M * (1 - m.y_l[l, t, d]) <= m.z[l] * m.length[l] * m.f_l[l, t, d] - (m.alpha_reg[l] * m.v[m.fr[l], t, d] - m.v[m.to[l], t, d])


def c20b(m, l, t, d):
    return m.z[l] * m.length[l] * m.f_l[l, t, d] - (m.alpha_reg[l] * m.v[m.fr[l], t, d] - m.v[m.to[l], t, d]) <= (1 - m.y_l[l, t, d]) * m.M


def c21(m, h, d):
    return m.soc_t0[h, d] == m.soc[h, len(m.T)-1, d]


def c22_23(m, h, t, d):
    if t == 0:
        return m.soc[h, t, d] == m.soc_t0[h, d] + m.eff[h]*m.p_in[h, t, d] - m.p_out[h, t, d]
    else:
        return m.soc[h, t, d] == m.soc[h, t-1, d] + m.eff[h]*m.p_in[h, t, d] - m.p_out[h, t, d]


def c24(m, h):
    return m.soc_ref[h] <= m.s[h] * m.p_in_max[h]


def c25(m, h):
    return m.soc_ref[h] <= m.s[h] * m.x_sd_var[h] * m.p_in_max[h]


def c26(m, h, t, d):
    return m.soc[h, t, d] == m.soc_ref[h] * m.f_bat[h, t, d]


def c27(m, h, t, d):
    return m.p_in[h, t, d] <= m.p_in_max[h]


def c28(m, h, t, d):
    return m.p_out[h, t, d] <= m.p_out_max[h]


def c29(m, h, t, d):
    return m.p_in[h, t, d] <= m.x_sd_var[h] * m.p_in_max[h]


def c30(m, h, t, d):
    return m.p_out[h, t, d] <= m.x_sd_var[h] * m.p_out_max[h]


def c31(m, h):
    return m.x_sd_var[h] <= m.x_sd[h] * m.sd_max[h]

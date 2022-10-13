from .utils import Var, timeit
from pyomo.environ import NonNegativeReals, Binary


@timeit
def create_vars(CapsuleModel, data):
    """Define pyomo variables here."""
    m = CapsuleModel.model

    # Real number of - x_b
    m.phi_cvar = Var(m.T, m.D, m.S, domain=NonNegativeReals)
    m.zeta = Var(m.T, m.D)
    m.l_tds = Var(m.T, m.D, m.S,  domain=NonNegativeReals)

    m.l_cje = Var(m.CJE, domain=NonNegativeReals)
    m.soc_aux = Var(m.CJEH, domain=NonNegativeReals)
    m.soc_ref = Var(m.H, domain=NonNegativeReals)

    # investment variables
    m.x_ind = Var(m.CJ, domain=Binary)
    m.x_fix_l = Var(m.L_c, domain=Binary)
    m.x_sd = Var(m.H, domain=Binary)
    m.x_sd_var = Var(m.H, domain=NonNegativeReals)

    m.g_tr = Var(m.N_SS, m.T, m.D, domain=NonNegativeReals)
    # m.beta_tr = Var(m.N_SS, m.nJ_ss, m.T, m.D, domain=NonNegativeReals)

    # m.g_l = Var(m.L, m.T, m.D, domain=NonNegativeReals)
    # m.beta_l = Var(m.L, m.nJ_l, m.T, m.D, domain=NonNegativeReals)

    m.f_l = Var(m.L_e, m.T, m.D)
    # m.y_l = Var(m.L_e, m.T, m.D, domain=Binary)
    m.v = Var(m.N, m.T, m.D)

    m.p_in = Var(m.H, m.T, m.D, domain=NonNegativeReals)
    m.p_out = Var(m.H, m.T, m.D, domain=NonNegativeReals)
    m.soc = Var(m.H, m.T, m.D, domain=NonNegativeReals)
    m.soc_t0 = Var(m.H, m.D, domain=NonNegativeReals)

    m.delta_plus = Var(m.N_load, m.T, m.D, domain=NonNegativeReals)
    m.delta_minus = Var(m.N_load, m.T, m.D, domain=NonNegativeReals)

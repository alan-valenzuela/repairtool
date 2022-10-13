import traceback
import logging
import custom_logger
import pandas as pd

from exp_planning import CapsuleModel as ExpansionPlanning
from data import read_data_alternative

# Initialize logger
logger = logging.getLogger("MAIN")
custom_logger.init_logger(filename="run_investment.log")


def main():
    logger.info("Program initialized")
    input_folder = "example_case"

    data = read_data_alternative(input_folder)

    logger.info(f"Data folder {input_folder} read, building optimization model")
    run_investment(data, folder="solutions")


def run_investment(data, **kwargs):
    opt = ExpansionPlanning()
    opt.model.FIX_V_SLACK = False
    opt.build_model(data)

    logger.info("Solving Optimization model")
    res = opt.solve('cplex', tee=True)

    m = opt.model

    def load_shedding_island_costs(m):
        return m.pf * m.c_imb * sum(
            m.w[d] * sum(m.s_prob[s] * m.l_tds[t, d, s].value for t in m.T for s in m.S)
            for d in m.D)

    def cvar_costs(m):
        return m.pf * m.c_imb * sum(m.w[d] * sum(
                m.zeta[t, d].value + sum(
                    m.s_prob[s] / (1-m.alpha_cvar) * m.phi_cvar[t,d,s].value
                    for s in m.S)
                for t in m.T)
            for d in m.D)

    obj = opt.get_objective_solution()
    obj['cvar_costs'] = cvar_costs(m)
    obj['load_shedding_island_costs'] = load_shedding_island_costs(m)

    logger.info("Printing objective costs:")
    for i, j in obj.items():
        logger.info(f"{i}: {j}")

    results = opt.get_solutions(data)
    data.lines_inv = results['line_inv']
    if not data.storage.empty:
        data.storage_inv = results['storage_inv']

    if 'folder' in kwargs:
        folder = kwargs['folder']
        pd.DataFrame(obj, index=[0]).to_csv(folder + '/obj_inv.csv', index=False)
        logger.info(f"Writing solutions to {folder}")
        for i, j in results.items():
            j.to_csv(folder + '/' + i + '.csv', index=False)

    return{'obj': obj, 'storage_inv': results['storage_inv'], 'line_inv': results['line_inv']}


if __name__ == '__main__':
    # Run main, otherwise write error to log
    try:
        main()
    except Exception:
        logger.critical('\n\n'+traceback.format_exc()+'\n')

from pyomo.environ import ConcreteModel, Set, Constraint, Param, Var, Objective, SolverFactory
from pyomo.version import version as pyomo_ver
from .inputs import create_inputs
from .sets import create_sets
from .params import create_params
from .vars import create_vars
from .constraints import create_constraints
from .objective import create_objective
import sys
import pandas as pd

import logging
logger = logging.getLogger("MAIN")


class CapsuleModel:
    """Class template model for Pyomo optimization problem.

    The idea behind this class is to have a simple and well documented
    optimization problem, that serves as a starting point for developing a more
    complex optimization problem. This includes the possibility of adding a
    mathematical formulation as our code's documentation, to have a readable
    and coherent code.

    This class contains attributes that are automatically generated, so in order
    to be used, you should go to the respective python files and make the
    correspondant replacement.

    Arguments:
        base (CapsuleModel): Optional CapsuleModel to use attributes from.
        model (pyomo.environ.ConcreteModel): Optional Pyomo ConcreteModel to\
        add optimization attributes.
        debug (bool): True for printing all logger, False otherwise (default).
        time (bool): True for printing execution time in logger, False\
        otherwise (default).

    """

    def __init__(self, base=None, model=None, debug=False, time=False):
        """Initialize class."""

        self.log = logger
        # if debug is False:
        #     logger.remove()
        #     logger.add(sys.stderr, level="WARNING")

        self.time = time

        if base is None:
            self.inputs = {}
            self.sets = []
            self.parameters = []
            self.vars = []
            self.constraints = []
            self.objective = None
        else:
            self.inputs = base.inputs
            self.sets = base.sets
            self.parameters = base.parameters
            self.vars = base.vars
            self.constraints = base.constraints
            self.objective = base.objective

        if model is None:
            if base is None:
                self.model = ConcreteModel()
            else:
                self.model = base.model
        else:
            self.model = model

        self.model.FIX_V_SLACK = False


    def __str__(self):
        """String representation of class."""
        attrs = ['inputs', 'sets', 'parameters', 'vars', 'constraints',
                 'objective', 'model']
        attrs = [i for i in attrs if (getattr(self, i) != []) and
                 (getattr(self, i) is not None)]
        if attrs != []:
            str_repr = ('CapsuleModel consisting in the following attributes:\n\t' +
                        '\n\t'.join(attrs))
        else:
            str_repr = 'Empty CapsuleModel'
        return str_repr

    # @logger.catch
    def build_model(self, data):
        """Build a model completely.

        The model is built using the following order:
            1. self.add_inputs(inputs)
            2. self.add_sets()
            3. self.add_params()
            4. self.add_vars()
            5. self.add_constraints()
            6. self.add_objective()

        Arguments:
            inputs (Dict): Optional inputs, used as a dictionary of elements\
            for all the sets and parameters of the model. Every element should\
            have a key of the value of a dictionary mapping the set of indexes\
            as tuples to the desired value.
        """
        self.add_inputs(data)
        self.add_sets(data)
        self.add_params(data)
        self.add_vars(data)
        self.add_constraints()
        self.add_objective()

    def add_inputs(self, inputs):
        """Add inputs to model.

        Arguments:
            inputs (Dict): Optional inputs, used as a dictionary of elements\
            for all the sets and parameters of the model. Every element should\
            have a key of the value of a dictionary mapping the set of indexes\
            as tuples to the desired value.
        """
        self.log.info('Adding inputs.')
        create_inputs(self, inputs)
        self.log.info('Inputs added successfully.')

    def add_sets(self, data):
        """Add sets to model."""
        self.log.info('Adding sets.')
        create_sets(self, data)
        self.sets = [i.name for i in self.model.component_objects(Set)]
        self.log.info('Sets added successfully.')

    def add_params(self, data):
        """Add parameters to model."""
        self.log.info('Adding params.')
        create_params(self, data)
        self.params = [i.name for i in self.model.component_objects(Param)]
        self.log.info('Params added successfully.')

    def add_vars(self, data):
        """Add variables to model."""
        self.log.info('Adding variables.')
        create_vars(self, data)
        self.vars = [i.name for i in self.model.component_objects(Var)]
        self.log.info('Variables added successfully.')

    def add_constraints(self):
        """Add constraints to model."""
        self.log.info('Adding constraints.')
        create_constraints(self)
        self.constraints = [i.name for i in self.model.component_objects(Constraint)]
        self.log.info('Constraints added successfully.')

    def add_objective(self):
        """Add objective function to model."""
        self.log.info('Adding objective function.')
        non_obj_vars = dir(self.model)
        create_objective(self)
        self.objective = [i.name for i in self.model.component_objects(Objective)]
        self.obj_expr = [i for i in dir(self.model) if i not in non_obj_vars + self.objective]
        self.log.info('Objective function added successfully.')

    def update_param(self, param, values):
        """Update a parameter using a dictionary of values.

        Arguments:
            param (str): Name of parameter to update.
            values (dict): Values to replace.
        """
        if param in self.params:
            getattr(self.model, param)._initialize_from(values)
        else:
            self.log.info("Parameter not found.")

    def update_constraint(self, constraint):
        """Update a constraint.

        Arguments:
            constraint (str): Name of constraint."""
        if constraint in self.constraints:
            getattr(self.model, constraint).clear()
            getattr(self.model, constraint).reconstruct()
        else:
            self.log.info("Constraint not found.")

    def update_objective(self):
        """Update objective function."""
        self.model.obj._init_sense = 1
        self.model.obj.reconstruct()

    def update_set(self, sets, values):
        """Update a set using a dictionary of values.

        Arguments:
            sets (str): Name of set to update.
            values (dict): Values to replace.
        """
        if sets in self.sets:
            aux_set = list(getattr(self.model, sets).value)
            for i in aux_set:
                getattr(self.model, sets).remove(i)
            for i in values:
                getattr(self.model, sets).add(i)
        else:
            self.log.info("Set not found.")

    def fix_var(self, var, pos, value):
        """Fix the value of a variable.

        Arguments:
            var (str): Name of variable to fix.
            pos (tuple): Index of variable to fix.
            value (float/int): Value to replace.
        """
        if var in self.vars:
            getattr(self.model, var)[pos].value = value
            getattr(self.model, var)[pos].fixed = True
        else:
            self.log.info("Variable not found.")

    def set_var(self, var, pos, value):
        """Set the value of a variable.

        Arguments:
            var (str): Name of variable to fix.
            pos (tuple): Index of variable to fix.
            value (float/int): Value to replace.
        """
        if var in self.vars:
            getattr(self.model, var)[pos].value = value
        else:
            self.log.info("Variable not found.")

    def deact_constraint(self, constraint, pos):
        """Desactivate constraint.

        Arguments:
            constraint (str): Name of constraint.
            pos (tuple): Index of constraint to deactivate.
        """
        if constraint in self.constraints:
            getattr(self.model, constraint)[pos].deactivate()
        else:
            self.log.info("Constraint not found.")

    def unfix_var(self, var, pos):
        """Unfix the value of a variable.

        Arguments:
            var (str): Name of variable to fix.
            pos (tuple): Index of variable to fix.
        """
        if var in self.vars:
            getattr(self.model, var)[pos].fixed = False
        else:
            self.log.info("Variable not found.")

    def act_constraint(self, constraint, pos):
        """Activate constraint.

        Arguments:
            constraint (str): Name of constraint.
            pos (tuple): Index of constraint to deactivate.
        """
        if constraint in self.constraints:
            getattr(self.model, constraint)[pos].activate()
        else:
            self.log.info("Constraint not found.")

    def get_var_solution(self, vars=[]):
        """Get dictionary of DataFrames of variables results.

        Arguments:
            vars (list): List of variables to print. If none is given, all\
            variables are returned.
        Returns:
            df (dictionary): Dictionary of DataFrames consisting of variables,\
            grouped by same index.
        """
        if vars == []:
            vars = self.vars
        sets = {}
        for n, var in enumerate(vars):
            found = False
            for key in sets:
                try:
                    if list(getattr(self.model, key).keys()) == list(getattr(self.model, var).keys()):
                        sets[key].update([var])
                        found = True
                        break
                except Exception:
                    found = False
            if found is False:
                sets[var] = set([var])

        df = {}
        for key in sets:
            df[key] = pd.DataFrame.from_dict(getattr(self.model, key).keys())
            for var in sets[key]:
                df[key][var] = pd.Series([i.value for i in getattr(self.model, var).values()])

        return df

    def get_objective_solution(self, expr=[]):
        """Get dictionary consisting of objective function values.

        Arguments:
            expr (list): List of expressions, defined in objective.py, that\
            will be obtained. If none is given, all expressions are returned.
        Returns:
            results (dict): Dictionary consisting of all values for asked\
            expressions and objective function.
        """
        if expr == []:
            expr = self.obj_expr + self.objective
        elif self.objective[0] not in expr:
            expr = expr + self.objective

        results = {}
        for attr in expr:
            val = getattr(self.model, attr)
            if type(val) not in (int, float):
                results[attr] = getattr(self.model, attr)()
            else:
                results[attr] = val

        return results


    def solve(self, solver, tee=True):
        opt = SolverFactory(solver)
        results = opt.solve(self.model, tee=tee)
        return results

    def get_solutions(self, data):
        """Get all results as a dictionary of DataFrames."""
        results = self.get_var_solution()
        CJE = {0: 'state', 1: 'rel_inv', 2: 'island'}
        CJEH = {0: 'state', 1: 'rel_inv', 2: 'island', 3: 'H'}
        # Give index and names to solutions DataFrames
        results['cvar'] = results.pop('phi_cvar').rename(columns={0: 'T', 1: 'D', 2: 'S'})
        results['value_at_risk'] = results.pop('zeta').rename(columns={0: 'T', 1: 'D'})
        results['load_shedding_island'] = results.pop('l_cje').rename(columns=CJE)
        if len(self.model.H) != 0:
            results['storage_states'] = results.pop('soc_aux').rename(columns=CJEH)
            results['storage_inv'] = results.pop('soc_ref').rename(columns={0: 'H'})
            results['storage_inv']['x_sd_var_kw'] = results['storage_inv']['x_sd_var'] * data.storage['p_in_max_kw'].to_numpy()
            results['storage_inv']['x_sd_var_kwh'] = results['storage_inv']['x_sd_var_kw'] * data.storage['s_charge'].to_numpy()
        results['state_investment'] = results.pop('x_ind').rename(columns=CJE)
        # Add relevant investment from heuristic to results
        results['state_investment']['rel_on'] = [
            data.state_expr[i][j]['rel_on'] for i, j in
            zip(results['state_investment'].state, results['state_investment'].rel_inv)]
        results['state_investment']['rel_off'] = [
            data.state_expr[i][j]['rel_off'] for i, j in
            zip(results['state_investment'].state, results['state_investment'].rel_inv)]
        results['line_inv'] = results.pop('x_fix_l').rename(columns={0: 'L_c'})
        results['substation'] = results.pop('g_tr').rename(columns={0: 'N', 1: 'T', 2: 'D'})
        results['line_flow'] = results.pop('f_l').rename(columns={0: 'L_e', 1: 'T', 2: 'D'})
        results['voltage'] = results.pop('v').rename(columns={0: 'N', 1: 'T', 2: 'D'})
        if len(self.model.H) != 0:
            results['storage_op'] = results.pop('p_in').rename(columns={0: 'H', 1: 'T', 2: 'D'})
            results['storage_t0'] = results.pop('soc_t0').rename(columns={0: 'H', 1: 'D'})
        results['imbalance'] = results.pop('delta_plus').rename(columns={0: 'N', 1: 'T', 2: 'D'})
        return results

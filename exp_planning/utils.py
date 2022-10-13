"""
Module for other advanced functions non related to the pyomo model.

This includes functions such as building documentation, decorators, etc.
"""
from pyomo.environ import Var as add_var
from pyomo.environ import Param as add_params
from pyomo.environ import Set as add_set
from functools import wraps
import time


def Var(*args, **kwargs):
    """Pyomo add variable."""
    if 'doc' in kwargs:
        del kwargs['doc']
    if 'sym' in kwargs:
        del kwargs['sym']
    return add_var(*args, **kwargs)


def Param(*args, **kwargs):
    """Pyomo add parameter."""
    if 'sym' in kwargs:
        del kwargs['sym']
    return add_params(*args, **kwargs)


def Set(*args, **kwargs):
    """Pyomo add set."""
    if 'sym' in kwargs:
        del kwargs['sym']
    return add_set(*args, **kwargs)


def timeit(method):
    """Get timing by decorator."""
    @wraps(method)
    def timed(*args, **kwargs):
        ts = time.time()
        result = method(*args, **kwargs)
        te = time.time()
        if hasattr(args[0], 'log'):
            if args[0].time == True:
                args[0].log.info(f'{method.__name__} took {te-ts} s.')
        return result
    return timed

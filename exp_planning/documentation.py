"""
Module for building documentation automatically.
"""
from . import constraints, objective, sets, params, vars
import os
import shutil
import fileinput
import sys
import platform
import inspect


class Documentation():
    def __init__(self, name='capsule'):
        self.name = name
        self.read_set()
        self.read_var()
        self.read_param()

    def build_doc_html(self):
        """Create html documentation. Run in main folder."""
        module_name = self.name
        os.chdir('docs')
        # Modify to index
        shutil.copyfile('source/template_index.txt', 'source/index.rst')
        with fileinput.FileInput('source/index.rst', inplace=True) as file:
            for line in file:
                print(line.replace(
                    'capsule', module_name).replace(
                        'Capsule', str.capitalize(module_name)), end='')
        # Create tables
        set_t = make_table([["Code", "Symbol", "Description"]] +
                           [[i, self.sets_tex[i], self.sets_description[i]]
                            for i in self.sets])
        par_t = make_table([["Code", "Symbol", "Description"]] +
                           [[i, self.params_tex[i], self.params_description[i]]
                            for i in self.params])
        var_t = make_table([["Code", "Symbol", "Description"]] +
                           [[i, self.vars_tex[i], self.vars_description[i]]
                            for i in self.vars])
        add_to_file('source/index.rst', 'Sets\n',
                    '\n' + set_t + '\n')
        add_to_file('source/index.rst', 'Parameters\n',
                    '\n' + par_t + '\n')
        add_to_file('source/index.rst', 'Variables\n',
                    '\n' + var_t + '\n')
        os.system('make html')
        os.chdir('..')

    def build_doc_latex(self):
        """Create latex documentation. Run in main folder."""
        module_name = self.name
        os.chdir('docs')
        shutil.copyfile('source/template_index.txt', 'source/index.rst')
        with fileinput.FileInput('source/index.rst', inplace=True) as file:
            for line in file:
                print(line.replace(
                    'capsule', module_name).replace(
                        'Capsule', str.capitalize(module_name)), end='')
        # Create tables
        set_t = make_table([["Code", "Symbol", "Description"]] +
                           [[i, self.sets_tex[i], self.sets_description[i]]
                            for i in self.sets])
        par_t = make_table([["Code", "Symbol", "Description"]] +
                           [[i, self.params_tex[i], self.params_description[i]]
                            for i in self.params])
        var_t = make_table([["Code", "Symbol", "Description"]] +
                           [[i, self.vars_tex[i], self.vars_description[i]]
                            for i in self.vars])
        add_to_file('source/index.rst', 'Sets\n',
                    '\n' + set_t + '\n')
        add_to_file('source/index.rst', 'Parameters\n',
                    '\n' + par_t + '\n')
        add_to_file('source/index.rst', 'Variables\n',
                    '\n' + var_t + '\n')
        os.system('make latex')
        if platform.system() == 'Windows':
            os.chdir('build/latex')
            os.system('pdflatex capsule.tex')
            os.chdir('../..')
        else:
            os.system('make latexpdf')
        os.chdir('..')

    def read_set(self):
        """Read sets comments to obtain description and symbols."""
        code = inspect.getsource(sets.create_sets).split('m = CapsuleModel.model')[1]
        split = code.split('Set(')
        values = self.get_description(split)
        self.sets = values[0]
        self.sets_description = values[1]
        self.sets_tex = values[2]

    def read_var(self):
        """Read variables comments to obtain description and symbols."""
        code = inspect.getsource(vars.create_vars).split('m = CapsuleModel.model')[1]
        split = code.split('Var(')
        values = self.get_description(split)
        self.vars = values[0]
        self.vars_description = values[1]
        self.vars_tex = values[2]

    def read_param(self):
        """Read params comments to obtain description and symbols."""
        code = inspect.getsource(params.create_params).split('m = CapsuleModel.model')[1]
        split = code.split('Param(')
        values = self.get_description(split)
        self.params = values[0]
        self.params_description = values[1]
        self.params_tex = values[2]

    def get_description(self, split):
        """Read string splitted to read the description on last found comment."""
        value = [i.split('\n')[-1] for i in split[:-1]]
        value = [i.replace('m.', '').replace(' ', '').replace('=', '')
                 for i in value]
        # Last comment
        last_comments = [i.split('#')[1] for i in split if '#' in i]
        elements = [i.split('\n')[1].replace('m.', '').replace(' ', '').replace('=', '')
                    for i in last_comments]
        info = [i.split('\n')[0].strip() for i in last_comments]
        description = {}
        keys = {}
        for n, i in enumerate(info):
            if '-' in i:
                keys[elements[n]] = ':math:`' + i.split('-')[-1].strip() + '`'
                description[elements[n]] = i.split('-')[0].strip()
            else:
                keys[elements[n]] = ':math:`' + elements[n].strip() + '`'
                description[elements[n]] = i.strip()
        for set in value:
            if not (set in description.keys()):
                description[set] = ''
                keys[set] = ':math:`' + str(set).strip() + '`'
        return value, description, keys

    def get_latex_nomenclature(self):
        """Get exported nomenclature to latex."""
        latex_text = ''
        description = {}
        description['sets'] = self.sets_description
        description['params'] = self.params_description
        description['vars'] = self.vars_description
        tex = {}
        tex['sets'] = self.sets_tex
        tex['params'] = self.params_tex
        tex['vars'] = self.vars_tex
        dict_type = {'sets': 'I', 'params': 'P', 'vars': 'V'}
        for i in description.keys():
            latex_text += '\n% ' + i + '\n'
            for j, k in description[i].items():
                k = k.replace(':math:`', '$').replace('`', '$')
                tex_val = tex[i][j].replace(':math:`', '$').replace('`', '$')
                latex_text += ('\\nomenclature[' + dict_type[i] +
                               ']{' + tex_val + '}' + '(' + k + ')\n')
        return latex_text

    def get_latex_constraints(self):
        """Get exported constraints to latex by reading documentation."""
        constraints_list = [i for i in inspect.getmembers(constraints,
                                                          inspect.isfunction)
                            if i[0] not in ['create_constraints', 'timeit']]
        latex_text = ''
        for i, j in constraints_list:
            doc = j.__doc__.replace(':math:`', '$$').replace('`', '$$')
            latex_text += ('\n' + i + ': ' + doc + '\n')
        return latex_text

    def get_latex_objective(self):
        """Get exported objective expressions to latex by reading
        documentation."""
        objective_list = [i for i in inspect.getmembers(objective,
                                                        inspect.isfunction)
                          if i[0] not in ['create_objective', 'timeit']]
        latex_text = ''
        for i, j in objective_list:
            doc = j.__doc__.replace(':math:`', '$$').replace('`', '$$')
            latex_text += ('\n' + i + ': ' + doc + '\n')
        return latex_text


def make_table(grid):
    max_cols = [max(out) for out in map(list, zip(*[[len(item) for item in row]
                                                    for row in grid]))]
    rst = table_div(max_cols, 1)

    for i, row in enumerate(grid):
        header_flag = False
        if i == 0 or i == len(grid)-1:
            header_flag = True
        rst += normalize_row(row, max_cols)
        rst += table_div(max_cols, header_flag)
    return rst


def table_div(max_cols, header_flag=1):
    out = ""
    if header_flag == 1:
        style = "="
    else:
        style = "-"

    for max_col in max_cols:
        out += max_col * style + " "

    out += "\n"
    return out


def normalize_row(row, max_cols):
    r = ""
    for i, max_col in enumerate(max_cols):
        r += row[i] + (max_col - len(row[i]) + 1) * " "

    return r + "\n"


def add_to_file(filename, line_input, line_to_add, after=1):
    """Add line to file after a number of lines when finding a line.

    Arguments:
        filename (str): File to replace.
        line_input (str): Line as a str to find.
        line_to_add (str): Line to add to file.
        after (int): Number of line after founded line to add.
    """
    n = -1
    for i, line in enumerate(fileinput.input(filename, inplace=1)):
        sys.stdout.write(line)
        if line == line_input:
            n = i + after
        if i == n:
            sys.stdout.write(line_to_add)

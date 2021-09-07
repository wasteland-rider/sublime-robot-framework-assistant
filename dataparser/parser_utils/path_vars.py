from os import path

from robot.running.builder import RobotParser
from robot.variables.variables import Variables

class PathVariables(Variables):
    """
    Storage for variables which keep paths to imported resources
    """
    def __init__(self, path_file=None):
        super().__init__()
        self.path_file = path_file
        self.base_path = self._get_base_path()

    def _get_base_path(self):
        if self.path_file:
            return path.dirname(self.path_file)

    def substitute_path(self):
        store = self.as_dict()
        for key, value in store.items():
            if not path.isabs(value):
                tmp_path = '/'.join((self.base_path, value))
                self.store.add(key, path.abspath(tmp_path))
            else:
            # Need this to dispatch alredy resolved variables, like ${CURDIR}
                self.store.add(key, path.abspath(value))

# Need this workarournd function to deal with ${/} robot variable
def sanitize_slash_var(variables):
    slash_var = '${/}'
    for variable in variables:
        variable_str = variable.value[0]
        if slash_var in variable_str:
            sanitized_str = variable_str.replace(slash_var, '/')
            variable.value = (sanitized_str, )

# TODO: Add check if path_file is exist and don't crash the whole process if there is no variables in it.
def init_path_variables(path_file):
    if not path_file:
        return None
    parsed_variables = RobotParser().parse_resource_file(path_file).variables
    sanitize_slash_var(parsed_variables)
    path_variables = PathVariables(path_file=path_file)
    path_variables.set_from_variable_table(parsed_variables)
    path_variables.substitute_path()
    return path_variables
        
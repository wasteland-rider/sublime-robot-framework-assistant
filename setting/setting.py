import subprocess
from os import path
import sublime
from sublime import error_message


class PathResolver(object):
    """Provides default paths for plugin"""
    curr_dir = path.dirname(path.realpath(__file__))
    package_dir = path.realpath(path.join(curr_dir, '..'))
    database_folder = path.join(package_dir, 'database')
    index_folder = 'index'
    scanner_folder = 'scanner'
    log_file_name = 'scan_index.log'

    @property
    def default_db_dir(self):
        return path.join(self.package_dir, self.database_folder)

    @property
    def default_scanner_dir(self):
        return path.join(self.default_db_dir, self.scanner_folder)

    @property
    def default_index_dir(self):
        return path.join(self.default_db_dir, self.index_folder)

    @property
    def default_log_file(self):
        return path.join(self.default_db_dir, self.log_file_name)

    @property
    def datapraser_folder(self):
        return path.join(self.package_dir, 'dataparser')

    @property
    def scanner_runner(self):
        return path.join(self.datapraser_folder, 'run_scanner.py')

    @property
    def index_runner(self):
        return path.join(self.datapraser_folder, 'run_index.py')

    @property
    def log_file(self):
        return path.join(self.default_db_dir, self.log_file_name)


class SettingObject(object):
    __instance = None

    table_dir = 'table_dir'
    index_dir = 'index_dir'
    scanner_runner = 'scanner_runner'
    index_runner = 'index_runner'
    log_file = 'log_file'
    python_binary = 'path_to_python'
    workspace = 'robot_framework_workspace'
    extension = 'robot_framework_extension'
    builtin_variables = 'robot_framework_builtin_variables'
    module_search_path = 'robot_framework_module_search_path'
    arg_format = 'robot_framework_keyword_argument_format'
    lib_in_xml = 'robot_framework_libraries_in_xml'
    project_setting = 'robot_framework_assistant'
    db_dir = 'robot_framework_database_path'
    log_commands = 'robot_framework_log_commands'
    automatic_table_creation = 'robot_framework_automatic_database_table'
    automatic_index_creation = 'robot_framework_automatic_indexing'
    automatic_database_update = 'robot_framework_automatic_database_update'
    kw_prefixes = 'robot_framework_keyword_prefixes'
    path_file = 'paths_variables_file'
    PY3 = None

    def __new__(cls, val):
        if SettingObject.__instance is None:
            SettingObject.__instance = object.__new__(cls)
        SettingObject.__instance.val = val
        return SettingObject.__instance


def get_scanner_dir():
    project_setting = parse_project(SettingObject.db_dir)
    if not project_setting:
        return PathResolver().default_scanner_dir
    else:
        return path.join(project_setting, PathResolver().scanner_folder)


def get_index_dir():
    project_setting = parse_project(SettingObject.db_dir)
    if not project_setting:
        return PathResolver().default_index_dir
    else:
        return path.join(project_setting, PathResolver.index_folder)


def get_log_file():
    project_setting = parse_project(SettingObject.db_dir)
    if not project_setting:
        return PathResolver().log_file
    else:
        return path.join(project_setting, PathResolver().log_file_name)


def get_view_path():
    project_setting = parse_project(SettingObject.db_dir)
    if not project_setting:
        return PathResolver().default_view_folder
    else:
        return path.join(project_setting, PathResolver().view_folder)


def get_python_binary():
    error_message = 'RobotFrameworkAssistant\n' + \
        '***********************************\n' + \
        'The plugin is fully supported on python 3\n'
    python_binary = get_sublime_setting(SettingObject.python_binary)
    if SettingObject.PY3 is None:
        result = subprocess.check_output(
            [python_binary, "-c", "import sys;print(sys.version_info.major)"])
        version = int(result.decode('utf-8').strip())
        if version < 3:
            error_message(error_msg)
            SettingObject.PY3 = False
        else:
            SettingObject.PY3 = True
    elif not SettingObject.PY3:
        error_message(error_msg)
    return python_binary


def get_setting(setting):
    if setting.lower() == SettingObject.table_dir:
        return get_scanner_dir()
    elif setting.lower() == SettingObject.index_dir:
        return get_index_dir()
    elif setting.lower() == SettingObject.scanner_runner:
        return PathResolver().scanner_runner
    elif setting.lower() == SettingObject.index_runner:
        return PathResolver().index_runner
    elif setting.lower() == SettingObject.log_file:
        return get_log_file()
    elif setting.lower() == SettingObject.python_binary:
        return get_python_binary()
    elif setting.lower() == SettingObject.path_file:
        return get_path_file(setting)
    else:
        return get_sublime_setting(setting)


def parse_project(setting):
    rf_project_setting = None
    window = sublime.active_window()
    project_data = window.project_data()
    if project_data and SettingObject.project_setting in project_data:
        rf_project_data = project_data[SettingObject.project_setting]
        if setting in rf_project_data:
            rf_project_setting = rf_project_data[setting]
    return rf_project_setting

def get_path_file(setting):
    workspace = get_sublime_setting(SettingObject.workspace)
    project_setting = parse_project(setting)
    if not project_setting:
        plugin_settings = sublime.load_settings('Robot.sublime-settings')
        if plugin_settings.get(setting):
            return path.join(workspace, plugin_settings.get(setting))
        else:
            return None
    else:
        return path.join(workspace, project_setting)


def get_sublime_setting(setting):
    project_setting = parse_project(setting)
    if not project_setting:
        plugin_settings = sublime.load_settings('Robot.sublime-settings')
        return plugin_settings.get(setting)
    else:
        return project_setting

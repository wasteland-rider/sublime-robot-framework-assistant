from robot import parsing
from robot.variables.filesetter import VariableFileSetter
from robot.variables.store import VariableStore
from robot.variables.variables import Variables
from robot.libdocpkg.robotbuilder import LibraryDocBuilder
from robot.utils.importer import Importer
from robot.libraries import STDLIBS
from robot.output import LOGGER as ROBOT_LOGGER
from robot.errors import DataError
from os import path
import xml.etree.ElementTree as ET
from tempfile import mkdtemp
import logging
import inspect
from parser_utils.util import normalise_path
from db_json_settings import DBJsonSetting

logging.basicConfig(
    format='%(levelname)s:%(asctime)s: %(message)s',
    level=logging.DEBUG)


def strip_and_lower(text):
    return text.lower().replace(' ', '_')


class DataParser():
    """ This class is used to parse different tables in test data.

    Class will return the the test data as in json format. Can parse
    Python libraries, library xml documentation generated by the libdoc
    resource and test suite files.
    """

    def __init__(self):
        self.file_path = None
        self.rf_variables = Variables()
        self.rf_var_storage = VariableStore(self.rf_variables)
        self.libdoc = LibraryDocBuilder()

    def parse_resource(self, file_path):
        self.file_path = file_path
        if path.exists(file_path):
            if '__init__.' in file_path:
                folder = path.dirname(file_path)
                model = parsing.TestDataDirectory(source=folder).populate()
            else:
                model = parsing.ResourceFile(file_path).populate()
            data =  self._parse_robot_data(file_path, model)
            data[DBJsonSetting.table_type] = DBJsonSetting.resource_file
            return data
        else:
            logging.error('File %s could not be found', file_path)
            raise ValueError(
                'File does not exist: {0}'.format(file_path))

    def parse_suite(self, file_path):
        self.file_path = file_path
        if path.exists(file_path):
            model = parsing.TestCaseFile(source=file_path).populate()
            data = self._parse_robot_data(file_path, model)
            data[DBJsonSetting.table_type] = DBJsonSetting.suite
            return data
        else:
            logging.error('File %s could not be found', file_path)
            raise ValueError(
                'File does not exist: {0}'.format(file_path))

    def parse_variable_file(self, file_path, args=None):
        if not args:
            args = []
        data = {}
        data[DBJsonSetting.file_name] = path.basename(file_path)
        data[DBJsonSetting.file_path] = normalise_path(file_path)
        self.file_path = file_path
        setter = VariableFileSetter(self.rf_var_storage)
        var_list = []
        try:
            variables = setter.set(file_path, args)
        except DataError:
            variables = []
        for variable in variables:
            var_list.append(variable[0])
        data[DBJsonSetting.variables] = sorted(var_list)
        data[DBJsonSetting.table_type] = DBJsonSetting.variable_file
        return data

    def parse_library(self, library, args=None):
        """Parses RF library to dictionary

        Uses internally libdoc modules to parse the library.
        Possible arguments to the library are provided in the
        args parameter.
        """
        data = {}
        if not args:
            data[DBJsonSetting.arguments] = []
        else:
            arg_list = []
            for arg in args:
                arg_list.append(arg)
            data[DBJsonSetting.arguments] = arg_list
        if path.isfile(library):
            data[DBJsonSetting.file_path] = normalise_path(library)
            if library.endswith('.xml'):
                library_module, keywords = self._parse_xml_doc(library)
                data[DBJsonSetting.keywords] = keywords
                data[DBJsonSetting.library_module] = library_module
            elif library.endswith('.py'):
                data[DBJsonSetting.file_name] = path.basename(library)
                data[DBJsonSetting.library_module] = path.splitext(
                    data[DBJsonSetting.file_name])[0]
                data[DBJsonSetting.keywords] = self._parse_python_lib(
                    library, data[DBJsonSetting.arguments])
            else:
                raise ValueError('Unknown library')
        else:
            data[DBJsonSetting.library_module] = library
            data[DBJsonSetting.keywords] = self._parse_python_lib(
                library, data[DBJsonSetting.arguments])
        if data[DBJsonSetting.keywords] is None:
            raise ValueError('Library did not contain keywords')
        else:
            data[DBJsonSetting.table_type] = DBJsonSetting.library
            return data

    def register_console_logger(self):
        ROBOT_LOGGER.register_console_logger()

    def unregister_console_logger(self):
        ROBOT_LOGGER.unregister_console_logger()

    def close_logger(self):
        ROBOT_LOGGER.close()

    def _parse_python_lib(self, library, args):
        lib_with_args = self._lib_arg_formatter(library, args)
        kws = {}
        try:
            lib = self.libdoc.build(lib_with_args)
        except DataError:
            raise ValueError(
                'Library does not exist: {0}'.format(library))
        if library in STDLIBS:
            import_name = 'robot.libraries.' + library
        else:
            import_name = library
        importer = Importer('test library')
        lib_args = self._argument_strip(lib, args)
        libcode = importer.import_class_or_module(
            import_name, instantiate_with_args=lib_args,
            return_source=False)
        kw_with_deco = self._get_keywords_with_robot_name(libcode)
        for keyword in lib.keywords:
            kw = {}
            kw[DBJsonSetting.keyword_name] = keyword.name
            kw[DBJsonSetting.tags] = list(keyword.tags._tags)
            kw[DBJsonSetting.keyword_arguments] = keyword.args
            kw[DBJsonSetting.documentation] = keyword.doc
            if keyword.name in kw_with_deco:
                function_name = kw_with_deco[keyword.name]
            else:
                function_name = keyword.name
            kw[DBJsonSetting.keyword_file] = self._get_library_kw_source(
                libcode, function_name)
            kws[strip_and_lower(keyword.name)] = kw
        return kws

    def _argument_strip(self, lib, given_args):
        formated_args = []
        if not given_args:
            return formated_args
        try:
            default_args = lib.inits[0].args
        except IndexError:
            default_args = []
        for default_arg in default_args:
            if '=' in default_arg:
                default_parts = default_arg.split('=', 1)
                formated_args.append(default_parts[1])
            else:
                formated_args.append(default_arg)
        return formated_args

    def _get_keywords_with_robot_name(self, lib_instance):
        """Returns keywords which uses Robot keyword decorator with robot_name

        The keyword name can be changed with Robot Framework keyword decorator
        and by using the robot_name attribute. Return dictionary which key is
        the value of the robot_name attribute and the original function name.
        """
        kw_deco = {}
        lib_class = type(lib_instance)
        for name in dir(lib_instance):
            owner = lib_class if hasattr(lib_class, name) else lib_instance
            method_attrib = getattr(owner, name)
            if hasattr(method_attrib, 'robot_name') and method_attrib.robot_name:
                kw_deco[method_attrib.robot_name] = name
        return kw_deco

    def _get_library_kw_source(self, libcode, keyword):
        kw_func = keyword.lower().replace(' ', '_')
        func = None
        func_file = None
        if hasattr(libcode, kw_func):
            func = getattr(libcode, kw_func)
        else:
            func_file, func = None, None
        if func:
            return func.__code__.co_filename
        return func_file

    def get_class_that_defined_method(self, meth):
        try:
            class_mro = inspect.getmro(meth.__self__.__class__)
        except AttributeError:
            return None
        for cls in class_mro:
            if meth.__name__ in cls.__dict__:
                return cls
        return None

    def get_function_file(self, kw_class):
        file_ = inspect.getsourcefile(kw_class)
        if file_ and path.exists(file_):
            return normalise_path(file_)
        else:
            return None

    def _lib_arg_formatter(self, library, args):
        args = self._argument_path_formatter(library, args)
        if not args:
            return library
        else:
            for item in args:
                library = '{lib}::{item}'.format(lib=library, item=item)
            return library

    def _argument_path_formatter(self, library, args):
        """Replace robot folder with real path

        If ${/}, ${OUTPUT_DIR} or ${EXECDIR} is found from args then
        a temporary directory is created and that one is used instead."""
        arguments = []
        for arg in args:
            if '${/}' in arg or '${OUTPUT_DIR}' in arg or '${EXECDIR}' in arg:
                f = mkdtemp()
                logging.info(
                    'Possible robot path encountered in library arguments')
                logging.debug('In library %s', library)
                logging.debug('Instead of %s using: %s', arg, f)
                arguments.append(f)
            else:
                arguments.append(arg)
        return arguments

    def _parse_xml_doc(self, library):
        root = ET.parse(library).getroot()
        if ('type', DBJsonSetting.library) in list(root.items()):
            return root.attrib['name'], self._parse_xml_lib(root)
        else:
            raise ValueError('XML file is not library: {0}'.format(
                root.attrib['name'])
            )

    def _parse_xml_lib(self, root):
        kws = {}
        for element in root.findall('kw'):
            kw = {}
            kw[DBJsonSetting.keyword_file] = None
            kw[DBJsonSetting.keyword_name] = element.attrib['name']
            kw[DBJsonSetting.documentation] = element.find('doc').text
            tags = []
            [tags.append(tag.text) for tag in element.findall('.//tags/tag')]
            kw[DBJsonSetting.tags] = tags
            arg = []
            [arg.append(tag.text) for tag in element.findall('.//arguments/arg')]
            kw[DBJsonSetting.keyword_arguments] = arg
            kws[strip_and_lower(kw[DBJsonSetting.keyword_name])] = kw
        return kws

    def _parse_robot_data(self, file_path, model):
        data = {}
        data[DBJsonSetting.file_name] = path.basename(file_path)
        data[DBJsonSetting.file_path] = normalise_path(file_path)
        data[DBJsonSetting.keywords] = self._get_keywords(model)
        data[DBJsonSetting.variables] = self._get_global_variables(model)
        lib, res, v_files = self._get_imports(
            model,
            path.dirname(normalise_path(file_path)),
            file_path
        )
        data[DBJsonSetting.resources] = res
        data[DBJsonSetting.libraries] = lib
        data[DBJsonSetting.variable_files] = v_files
        return data

    def _get_keywords(self, model):
        kw_data = {}
        for kw in model.keywords:
            tmp = {}
            tmp[DBJsonSetting.keyword_arguments] = kw.args.value
            tmp[DBJsonSetting.documentation] = kw.doc.value
            tmp[DBJsonSetting.tags] = kw.tags.value
            tmp[DBJsonSetting.keyword_name] = kw.name
            kw_data[strip_and_lower(kw.name)] = tmp
        return kw_data

    def _get_imports(self, model, file_dir, file_path):
        lib = []
        res = []
        var_files = []
        for setting in model.setting_table.imports:
            if setting.type == 'Library':
                lib.append(self._format_library(setting, file_dir))
            elif setting.type == 'Resource':
                res.append(self._format_resource(setting, file_path))
            elif setting.type == 'Variables':
                var_files.append(self._format_variable_file(setting))
        return lib, res, var_files

    def _format_library(self, setting, file_dir):
        data = {}
        lib_name = setting.name
        if lib_name.endswith('.py') and not path.isfile(lib_name):
            lib_path = path.abspath(path.join(file_dir, lib_name))
            lib_name = path.basename(lib_path)
        elif lib_name.endswith('.py') and path.isfile(lib_name):
            lib_path = normalise_path(lib_name)
            lib_name = path.basename(lib_name)
        else:
            lib_path = None
        data[DBJsonSetting.library_name] = lib_name
        data[DBJsonSetting.library_alias] = setting.alias
        data[DBJsonSetting.library_arguments] = setting.args
        data[DBJsonSetting.library_path] = lib_path
        return data

    def _format_resource(self, setting, file_path):
        if path.isabs(setting.name):
            return setting.name
        else:
            c_dir = path.dirname(self.file_path)
            resource_path = normalise_path(path.join(c_dir, setting.name))
            if not path.isfile(resource_path):
                print(('Import failure on file: {0},'.format(file_path),
                       'could not locate: {0}'.format(setting.name)))
            return resource_path

    def _format_variable_file(self, setting):
        data = {}
        v_path = normalise_path(path.join(
            path.dirname(self.file_path), setting.name))
        args = {}
        args['variable_file_arguments'] = setting.args
        data[v_path] = args
        return data

    def _get_global_variables(self, model):
        var_data = []
        for var in model.variable_table.variables:
            if var:
                var_data.append(var.name)
        return var_data

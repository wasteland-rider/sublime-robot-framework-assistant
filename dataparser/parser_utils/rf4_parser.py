from robot.api.parsing import get_resource_model, ModelVisitor, Token
from robot.api.parsing import get_resource_tokens
from robot.parsing.model.statements import KeywordName
import ast
from collections import namedtuple
from dataclasses import dataclass, field

# FILENAME = '/Users/wastelandeer/python/rf-playground/Utils/Resources/WebPages/meServicePagePlaywright.robot'
FILENAME = '/Users/wastelandeer/python/sublime-robot-framework-assistant/test_rf_file.robot'

class SampleVisitor(ModelVisitor):
    def __init__(self):
        # pass
        self.keywords = list()
        # self.Keyword = namedtuple('Keyword', 'name args doc tags')
        self.keyword_attrs = {}
        self.variables = list()

        self.libraries_import = []
        self.resources_import = []
        self.variables_import = []
        # sel
    # def visit_KeywordSection(self, node):
    #     # for token in tokens:
    #     #     if isinstance(token, Token.KEYWORD_HEADER):
    #     #         print(token[1])
    #     # self.keywords = None
    #     print(node.header.get_value(Token.KEYWORD_HEADER))
    #     self.generic_visit(node)
    #     # self.keywords.append(self.keyword_attrs)
    #     # print(self.keyword_attrs)
    def visit_Keyword(self, node):
        # self.keywords = list()
        # self.keyword_attrs = {}
        # self.keyword_attrs = dict()
        # print(node.name)
        self.keyword_attrs['name'] = node.name
        self.generic_visit(node)
        # breakpoint()
        self.keywords.append(Keyword(**self.keyword_attrs))
        # print(self.keyword_attrs)
        self.keyword_attrs = {}

    def visit_Arguments(self, node):
        # print(*node.get_values(Token.ARGUMENT))
        self.keyword_attrs['args'] = list(node.get_values(Token.ARGUMENT))
    def visit_Tags(self, node):
        # print(*node.get_values(Token.ARGUMENT))
        self.keyword_attrs['tags'] = list(node.get_values(Token.ARGUMENT))
    def visit_Documentation(self, node):
        self.keyword_attrs['doc'] = node.value
    
    def visit_VariableSection(self, node):
        self.generic_visit(node)
    
    def visit_Variable(self, node):
        self.variables.append(node.get_value(Token.VARIABLE))

    def visit_LibraryImport(self, node):
        self.libraries_import.append(Library(node.name, node.args, node.alias))
    def visit_ResourceImport(self, node):
        self.resources_import.append(node.name)
    def visit_VariablesImport(self, node):
        self.variables_import.append(Variable(node.name, node.args))
        # print(node.name)
        # print(node.body)
        # self.visit_Documentation(node.body)
        # for keyword in node.body:
            # print(keyword)
            # if keyword.get_value(Token.DOCUMENTATION):
            #     # print(keyword.get_value(Token.ARGUMENT))
            #     self.doc = keyword.get_value(Token.ARGUMENT)
            # if keyword.get_value(Token.KEYWORD_NAME):
            #     self.name = keyword.get_value(Token.ARGUMENT)
            # if keyword.get_value(Token.ARGUMENTS):
            #     self.args = keyword.get_value(Token.ARGUMENT)
            # if keyword.get_value(Token.TAGS):
            #     self.tags = keyword.get_value(Token.ARGUMENT)
            # self.keywords.append(keyword.get_values(Token.ARGUMENT))
            # print(keyword.name)
            # for kw in keyword.body:
            #     if kw.get_value(Token.DOCUMENTATION):
            #         print(kw.get_values(Token.ARGUMENT))
    # def visit_Documentation(self, node):
    #     print(node)
            




@dataclass
class Keyword:
    name: str
    args: list[str] = field(default_factory=list)
    doc: str = str()
    tags: list[str] = field(default_factory=list)

@dataclass
class Library:
    name: str
    args: tuple[str] = field(default_factory=tuple)
    alias: str = str()

@dataclass
class Variable:
    name: str
    args: tuple[str] = field(default_factory=tuple)

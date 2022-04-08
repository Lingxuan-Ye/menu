import json
from copy import deepcopy
from functools import wraps
from types import NoneType
from typing import Union

from type_check import *

__all__ = ["Menu"]


def _raise(func):

    class Error(Exception):
        pass

    @wraps(func)
    def wrapper(*args, **kwargs):
        result: dict = func(*args, **kwargs)
        if not isinstance(result, dict):
            return result
        error_info = result.get("error_info", None)
        if error_info is not None:
            raise Error(error_info)
        return result

    return wrapper


class Menu:

    def __init__(self, menu_name: str = "untitled"):
        type_check(menu_name, str, "menu_name", False)
        if menu_name.strip() == "":
            menu_name = "untitled"
        self.__title = menu_name
        self.__submenus = []
        self.__attributes = {}
        self.__structure = []
        self.tree_indent = 4

    def get_title(self):
        return self.__title

    def rename(self, menu_name: str = "untitled"):
        type_check(menu_name, str, "menu_name", False)
        if menu_name.strip() == "":
            menu_name = "untitled"
        self.__title = menu_name

    def get_submenus(self):
        return self.__submenus

    def get_submenu(self, locator: tuple):
        type_check(locator, tuple, "locator", False)
        element_type_check(locator, int, "locator", False)
        menu_instance = self
        for index in locator:
            menu_instance = menu_instance.get_submenus()[index]
        return menu_instance

    def add_new_submenu(self,
                        submenu_name: str = "untitled",
                        index: Union[int, NoneType] = None):
        """
        This method will return newly-instantiated submenu for further editing.
        """
        type_check(submenu_name, str, "submenu_name", False)
        type_check(index, (str, NoneType), "index", False)
        if submenu_name.strip() == "":
            submenu_name = "untitled"
        sub_menu = type(self)(submenu_name)
        # 'type(self)' differs from 'Menu' in derived class
        if index is None:
            self.__submenus.append(sub_menu)
        else:
            self.__submenus.insert(sub_menu, index)
        return sub_menu

    @_raise
    def add_existing_submenu(self,
                             menu_instance,
                             index: Union[int, NoneType] = None):
        if not isinstance(menu_instance, Menu):
            error_info = "argument 'submenu' must be an " \
                       + "instance of 'Menu'"
            result = {"error_info": error_info}
            return result
        type_check(index, (str, NoneType), "index", False)
        if index is None:
            self.__submenus.append(menu_instance)
        else:
            self.__submenus.insert(menu_instance, index)

    def del_submenu(self, index: int = -1, *, delete_all: bool = False):
        type_check(delete_all, bool, "delete_all", False)
        if delete_all:
            self.__submenus = []
            return
        type_check(index, int, "index", False)
        self.__submenus.pop(index)

    def get_attributes(self):
        return self.__attributes

    @_raise
    def set_attributes(self, **kwargs):
        if len(kwargs) == 0:
            error_info = "set_attributes() requires at least one argument"
            result = {"error_info": error_info}
            return result
        element_type_check(kwargs.values(),
                           (int, float, str, bool, list, dict, NoneType),
                           "kwargs.values()", False)
        self.__attributes = kwargs

    @_raise
    def add_attributes(self, **kwargs):
        if len(kwargs) == 0:
            error_info = "add_attributes() requires at least one argument"
            result = {"error_info": error_info}
            return result
        element_type_check(kwargs.values(),
                           (int, float, str, bool, list, dict, NoneType),
                           "kwargs.values()", False)
        self.__attributes.update(kwargs)

    @_raise
    def del_attributes(self, *args: str, delete_all: bool = False):
        type_check(delete_all, bool, "delete_all", False)
        if delete_all:
            self.__attributes = {}
            return
        if len(args) == 0:
            error_info = "del_attributes() requires at least one argument"
            result = {"error_info": error_info}
            return result
        element_type_check(args, str, "arg", False)
        for key in args:
            self.__attributes.pop(key, None)

    def set_text(self, content: str):
        type_check(content, str, "content", False)
        self.add_attributes(__text__=content)

    def del_text(self):
        self.del_attributes("__text__")

    def set_comment(self, content: str):
        type_check(content, str, "content", False)
        self.add_attributes(__comment__=content)

    def del_comment(self):
        self.del_attributes("__comment__")

    @classmethod
    def instantiate_from_dict(cls, menu_dict: dict):
        menu_name: str = menu_dict["title"]
        submenu_dicts: list = menu_dict["submenus"]
        attributes: dict = menu_dict["attributes"]
        type_check(menu_name, str, 'menu_dict["title"]', False)
        type_check(submenu_dicts, list, 'menu_dict["submenus"]', False)
        if len(submenu_dicts) != 0:
            element_type_check(submenu_dicts, dict, 'menu_dict["submenus"]',
                               False)
        type_check(attributes, dict, 'menu_dict["attributes"]', False)
        if len(attributes) != 0:
            element_type_check(attributes.keys(), str,
                               'menu_dict["attributes"].keys()', False)
            element_type_check(attributes.values(),
                               (int, float, str, bool, list, dict, NoneType),
                               'menu_dict["attributes"].values()', False)
        if menu_name.strip() == "":
            menu_name = "untitled"
        menu = cls(menu_name)
        for submenu_dict in submenu_dicts:
            submenu = cls.instantiate_from_dict(submenu_dict)
            menu.add_existing_submenu(submenu)
        menu.__attributes = attributes
        return menu

    def __get_structure(self, __instance=None, __locator: list = []):
        """
        argument '__instnace' and '__locator' should not be given
        while calling this method.
        """
        if __instance is None:
            __instance = self
        self.__structure.append((tuple(__locator), __instance.get_title()))
        for index, submenu in enumerate(__instance.get_submenus()):
            __sublocator = deepcopy(__locator)
            __sublocator.append(index)
            self.__get_structure(submenu, __sublocator)

    @_raise
    def get_structure(self, type_of_return: str = "list"):
        type_check(type_of_return, str, "type_of_return", False)
        type_of_return = type_of_return.lower()
        if type_of_return not in ("list", "dict"):
            error_info = "undefined type of return"
            result = {"error_info": error_info}
            return result
        self.__structure = []
        self.__get_structure()
        structure_list = deepcopy(self.__structure)
        if type_of_return == "list":
            return structure_list
        else:
            structure_dict = {}
            for index, line_attr in enumerate(structure_list):
                structure_dict[line_attr[0]] = (index, line_attr[1])
            return structure_dict

    @_raise
    def set_tree_indent(self, indent: int):
        type_check(indent, int, "indent", False)
        if indent <= 0:
            error_info = "argument 'indent' must be greater than 0"
            result = {"error_info": error_info}
            return result
        self.tree_indent = indent

    @_raise
    def tree(self, type_of_return: str = "str", indent: int = -1):
        type_check(type_of_return, str, "type_of_return", False)
        type_check(indent, int, "indent", False)
        type_of_return = type_of_return.lower()
        if type_of_return not in ("str", "list"):
            error_info = "undefined type of return"
            result = {"error_info": error_info}
            return result

        structure: dict = self.get_structure("dict")
        lines_with_index = []

        if indent > 0:
            tree_indent = indent
        else:
            tree_indent = self.tree_indent
        stems = [
            "│" + " " * (tree_indent - 1), " " + " " * (tree_indent - 1),
            "├" + "─" * (tree_indent - 1), "└" + "─" * (tree_indent - 1)
        ]
        if tree_indent > 2:
            stems[2] = stems[2][0:-1] + " "
            stems[3] = stems[3][0:-1] + " "

        for locator in structure:
            if len(locator) == 0:
                prefix = ""
            else:
                prefix_list = []
                for i, j in enumerate(locator[0:-1]):
                    sup_dummy = (*locator[0:i], j + 1)
                    if structure.get(sup_dummy, None) is not None:
                        prefix_list.append(stems[0])
                    else:
                        prefix_list.append(stems[1])
                dummy = (*locator[0:-1], locator[-1] + 1)
                if structure.get(dummy, None) is not None:
                    prefix_list.append(stems[2])
                else:
                    prefix_list.append(stems[3])
                prefix = "".join(prefix_list)
            line_index: int = structure[locator][0]
            line: str = prefix + structure[locator][1]
            line_with_index: tuple = (line_index, line)
            lines_with_index.append(line_with_index)
        lines_with_index.sort(key=lambda x: x[0])
        lines = [i[1] for i in lines_with_index]
        if type_of_return == "str":
            return "\n".join(lines)
        else:
            return lines

    def export(self):
        menu_dict = {}
        menu_dict["title"] = self.__title
        menu_dict["submenus"] = []
        for submenu in self.__submenus:
            submenu_dict = submenu.export()
            menu_dict["submenus"].append(submenu_dict)
        menu_dict["attributes"] = deepcopy(self.__attributes)
        return menu_dict

    def save_as_json(self, path: str = r"./menu.json"):
        """
        Save Menu instance as json file.

        If file extension is missing, or not 'json', saving path will append
        suffix '.json'.
        """
        type_check(path, str, "path", False)
        if not path.endswith(".json"):
            path = path + ".json"
        with open(path, "w") as f:
            menu_dict = self.export()
            json.dump(menu_dict, f, indent=4)

    @classmethod
    def load_from_json(cls, path: str = r"./menu.json"):
        """
        Instantiate Menu instance from json file.

        If file extension is missing, or not 'json', loading path will append
        suffix '.json'.
        """
        type_check(path, str, "path", False)
        if not path.endswith(".json"):
            path = path + ".json"
        with open(path, "r") as f:
            menu_dict = json.load(f)
            menu = cls.instantiate_from_dict(menu_dict)
        return menu

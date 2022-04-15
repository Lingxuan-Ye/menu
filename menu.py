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

    @type_check
    def __init__(self, title: str = "untitled"):
        if title.strip() == "":
            title = "untitled"
        self.__title = title
        self.__attributes = {}
        self.__sub_menus = []
        self.__tree_indent = 4

    def __get_title(self):
        return self.__title

    @type_check
    def __set_title(self, title: str):
        if title.strip() == "":
            title = "untitled"
        self.__title = title

    def __del_title(self):
        self.__title = "untitled"

    title = property(fget=__get_title,
                     fset=__set_title,
                     fdel=__del_title)

    @property
    def attributes(self):
        return self.__attributes

    def set_attributes(self, **kwargs):
        if kwargs:
            element_type_check(kwargs.values(),
                               (int, float, str, bool, list, dict, NoneType),
                               "kwargs.values()")
        self.__attributes.clear()
        self.__attributes.update(kwargs)

    @_raise
    def add_attributes(self, **kwargs):
        if not kwargs:
            error_info = "add_attributes() requires at least one argument"
            return {"error_info": error_info}
        element_type_check(kwargs.values(),
                           (int, float, str, bool, list, dict, NoneType),
                           "kwargs.values()")
        self.__attributes.update(kwargs)

    @_raise
    def del_attributes(self, *args):
        if not args:
            error_info = "del_attributes() requires at least one argument "
            return {"error_info": error_info}
        element_type_check(args, str, "args")
        for key in args:
            self.__attributes.pop(key, None)

    def __get_text(self):
        return self.__attributes.get("__text__", None)

    @type_check
    def __set_text(self, content: str):
        self.add_attributes(__text__=content)

    def __del_text(self):
        self.del_attributes("__text__")

    text = property(fget=__get_text,
                    fset=__set_text,
                    fdel=__del_text)

    def __get_comment(self):
        return self.__attributes.get("__comment__", None)

    @type_check
    def __set_comment(self, content: str):
        self.add_attributes(__comment__=content)

    def __del_comment(self):
        self.del_attributes("__comment__")

    comment = property(fget=__get_comment,
                       fset=__set_comment,
                       fdel=__del_comment)

    @property
    def sub_menus(self):
        return self.__sub_menus

    @type_check
    def get_sub_menu(self, locator: Union[tuple, list]):
        if locator:
            element_type_check(locator, int, "locator")
        menu_instance = self
        for index in locator:
            menu_instance = menu_instance.sub_menus[index]
        return menu_instance

    @_raise
    @type_check
    def add_sub_menu(self,
                     *,
                     menu_instance=None,
                     title: Union[str, NoneType] = None,
                     index: Union[int, NoneType] = None):
        if menu_instance is None:
            menu_instance = type(self)("untitled")
            # 'type(self)' differs from 'Menu' in derived class
        elif not isinstance(menu_instance, type(self)):
            error_info = "argument 'menu_instance' must be an instance of " \
                       + "'Menu' or NoneType"
            return {"error_info": error_info}
        else:
            menu_instance = deepcopy(menu_instance)
        if title is not None:
            if title.strip() == "":
                title = "untitled"
            menu_instance.title = title
        if index is not None:
            self.__sub_menus.insert(index, menu_instance)
        else:
            self.__sub_menus.append(menu_instance)
        return menu_instance

    @type_check
    def del_sub_menu(self, index: int = -1, *, delete_all: bool = False):
        if delete_all:
            self.__sub_menus.clear()
        else:
            del self.__sub_menus[index]

    @classmethod
    @type_check
    def instantiate_from_dict(cls, menu_dict: dict):
        title: str = menu_dict["title"]
        attributes: dict = menu_dict["attributes"]
        sub_menus: list = menu_dict["sub_menus"]
        type_debug(title, str, 'menu_dict["title"]')
        type_debug(attributes, dict, 'menu_dict["attributes"]')
        type_debug(sub_menus, list, 'menu_dict["sub_menus"]')
        if attributes:
            element_type_check(attributes.keys(), str,
                               'menu_dict["attributes"].keys()')
            element_type_check(attributes.values(),
                               (int, float, str, bool, list, dict, NoneType),
                               'menu_dict["attributes"].values()')
        if sub_menus:
            element_type_check(sub_menus, dict, 'menu_dict["sub_menus"]')
        if title.strip() == "":
            title = "untitled"
        menu_instance = cls(title)
        menu_instance.__attributes.update(attributes)
        for _menu_dict in sub_menus:
            _menu_instance = cls.instantiate_from_dict(_menu_dict)
            menu_instance.add_sub_menu(menu_instance=_menu_instance)
        return menu_instance

    @_raise
    @type_check
    def get_structure(self, *, type_of_return: str = "generator"):
        structure = []
        locator = ()
        menu_instance = self
        stack = [(locator, menu_instance)]
        while stack:
            locator, menu_instance = stack.pop()
            structure.append((locator, menu_instance))
            temp = []
            for _index, _menu_instance in enumerate(menu_instance.sub_menus):
                _temp = list(locator)
                _temp.append(_index)
                _locator = tuple(_temp)
                temp.append((_locator, _menu_instance))
            temp.reverse()
            stack.extend(temp)
            del temp
        structure_printable = ((locator, menu_instance.title)
                               for locator, menu_instance in structure)
        match type_of_return.lower():
            case "g"|"generator":
                return structure_printable
            case "t"|"tuple":
                return tuple(structure_printable)
            case "l"|"list":
                return list(structure_printable)
            case "d"|"dict":
                result = {}
                for index, line_attr in enumerate(structure_printable):
                    result[line_attr[0]] = (index, line_attr[1])
                return result
            case _:
                return {"error_info": "undefined type of return"}

    def __get_tree_indent(self):
        return self.__tree_indent

    @_raise
    @type_check
    def __set_tree_indent(self, tree_indent: int):
        if tree_indent <= 0:
            error_info = "argument 'tree_indent' must be greater than 0"
            return {"error_info": error_info}
        self.__tree_indent = tree_indent

    def __del_tree_indent(self):
        del self.__tree_indent

    tree_indent = property(fget=__get_tree_indent,
                           fset=__set_tree_indent,
                           fdel=__del_tree_indent)

    @_raise
    @type_check
    def tree(self, *,
             type_of_return: str = "str",
             tree_indent: Union[int, NoneType] = None):
        """
        If argument 'tree_indent' is None, or
        less than or equal to 0, value of 'tree_indent' will be determined by
        property 'self.tree_indent'.
        """
        if tree_indent is None or tree_indent <= 0:
            tree_indent = self.tree_indent
        stems = [
            "│" + " " * (tree_indent - 1), " " + " " * (tree_indent - 1),
            "├" + "─" * (tree_indent - 1), "└" + "─" * (tree_indent - 1)
        ]
        if tree_indent > 2:
            stems[2] = stems[2][0:-1] + " "
            stems[3] = stems[3][0:-1] + " "

        structure_pritable: dict = self.get_structure(type_of_return="dict")
        lines_with_index = []
        for locator in structure_pritable:
            if not locator:
                prefix = ""
            else:
                prefix_list = []
                for i, j in enumerate(locator[0:-1]):
                    sup_dummy = (*locator[0:i], j + 1)
                    if structure_pritable.get(sup_dummy, None) is not None:
                        prefix_list.append(stems[0])
                    else:
                        prefix_list.append(stems[1])
                dummy = (*locator[0:-1], locator[-1] + 1)
                if structure_pritable.get(dummy, None) is not None:
                    prefix_list.append(stems[2])
                else:
                    prefix_list.append(stems[3])
                prefix = "".join(prefix_list)
            line_index: int = structure_pritable[locator][0]
            line: str = prefix + structure_pritable[locator][1]
            line_with_index: tuple = (line_index, line)
            lines_with_index.append(line_with_index)
        lines_with_index.sort(key=lambda x: x[0])
        lines = (i[1] for i in lines_with_index)
        match type_of_return.lower():
            case "s"|"str":
                return "\n".join(lines)
            case "g"|"generator":
                return lines
            case "t"|"tuple":
                return tuple(lines)
            case "l"|"list":
                return list(lines)
            case _:
                return {"error_info": "undefined type of return"}

    def export(self):
        menu_dict = {}
        menu_dict["title"] = self.title
        menu_dict["attributes"] = deepcopy(self.__attributes)
        menu_dict["sub_menus"] = []
        for _menu_instance in self.__sub_menus:
            sub_menu_dict = _menu_instance.export()
            menu_dict["sub_menus"].append(sub_menu_dict)
        return menu_dict

    def __str__(self) -> str:
        return str(self.export())

    @type_check
    def save_as_json(self, path: str = r"./menu.json"):
        """
        Save Menu instance as json file.

        If file extension is missing, or not 'json', saving path will append
        suffix '.json'.
        """
        if not path.endswith(".json"):
            path += ".json"
        with open(path, "w") as f:
            menu_dict = self.export()
            json.dump(menu_dict, f, indent=4)

    @classmethod
    @type_check
    def load_from_json(cls, path: str = r"./menu.json"):
        """
        Instantiate Menu instance from json file.

        If file extension is missing, or not 'json', loading path will append
        suffix '.json'.
        """
        if not path.endswith(".json"):
            path += ".json"
        with open(path, "r") as f:
            menu_dict = json.load(f)
            menu_instance = cls.instantiate_from_dict(menu_dict)
        return menu_instance

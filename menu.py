import json
import logging
from collections import deque
from copy import deepcopy
from functools import wraps
from types import NoneType
from typing import NamedTuple, Optional, Sequence, Union

from type_check import element_type_check, type_check, type_debug

__all__ = ["Menu"]

logging.basicConfig(format='%(levelname)s: %(message)s\n%(asctime)s')


class Error(Exception):
    pass


class ErrorInfo(NamedTuple):
    message: str
    action: str = "raise"


def _exception(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not isinstance(result, ErrorInfo):
            return result
        else:
            message = result.message
            action = result.action
        match action.lower():
            case "r" | "raise" | "raising":
                raise Error(message)
            case "l" | "log" | "logging":
                logging.error(message)
            case _:
                raise Error("undefined action")

    return wrapper


class Menu:

    @type_check
    def __init__(self, title: Optional[str] = None):
        if title is None or title.strip() == "":
            title = "untitled"
        self.__title: str = title
        self.__attributes: dict = {}
        self.__sub_menus: deque = deque()
        self.__tree_indent: int = 4

    def __get_title(self):
        return self.__title

    @type_check
    def __set_title(self, title: Optional[str] = None):
        if title is None or title.strip() == "":
            title = "untitled"
        self.__title = title

    def __del_title(self):
        self.__title = "untitled"

    title = property(fget=__get_title, fset=__set_title, fdel=__del_title)

    def __get_attributes(self):
        return self.__attributes

    @type_check
    def __set_attributes(self, kwargs: dict):
        if kwargs:
            element_type_check(
                kwargs.values(),
                Union[int, float, str, bool, list, dict, NoneType],
                "kwargs.values()"
            )
        self.__attributes.clear()
        self.__attributes.update(kwargs)

    def __del_attributes(self):
        self.__attributes.clear()

    attributes = property(
        fget=__get_attributes,
        fset=__set_attributes,
        fdel=__del_attributes
    )

    @_exception
    def add_attributes(self, **kwargs):
        if not kwargs:
            message = "add_attributes() requires at least one argument"
            return ErrorInfo(message)
        element_type_check(
            kwargs.values(),
            Union[int, float, str, bool, list, dict, NoneType],
            "kwargs.values()"
        )
        self.__attributes.update(kwargs)

    @_exception
    def del_attributes(self, *args):
        if not args:
            message = "del_attributes() requires at least one argument"
            return ErrorInfo(message)
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

    text = property(fget=__get_text, fset=__set_text, fdel=__del_text)

    def __get_comment(self):
        return self.__attributes.get("__comment__", None)

    @type_check
    def __set_comment(self, content: str):
        self.add_attributes(__comment__=content)

    def __del_comment(self):
        self.del_attributes("__comment__")

    comment = property(
        fget=__get_comment,
        fset=__set_comment,
        fdel=__del_comment
    )

    @property
    def sub_menus(self):
        return self.__sub_menus

    @type_check
    def get_sub_menu(self, locator: Sequence) -> "Menu":
        if locator:
            element_type_check(locator, int, "locator")
        menu_instance = self
        for index in locator:
            menu_instance = menu_instance.sub_menus[index]
        return menu_instance

    @_exception
    @type_check
    def add_sub_menu(
        self,
        title: Optional[str] = None, *,
        menu_instance = None,
        index: Optional[int] = None,
        add_deepcopy: bool = True
    ):
        if menu_instance is None:
            menu_instance = type(self)()
            # 'type(self)' differs from 'Menu' in derived class
        elif not isinstance(menu_instance, type(self)):
            message = "argument 'menu_instance' must be an instance of " \
                    + "'Menu' or NoneType"
            return ErrorInfo(message)
        elif add_deepcopy:
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
    def instantiate_from_dict(cls, menu_dict: dict) -> "Menu":
        title: str = menu_dict["title"]
        attributes: dict = menu_dict["attributes"]
        sub_menus: list = menu_dict["sub_menus"]
        type_debug(title, str, 'menu_dict["title"]')
        type_debug(attributes, dict, 'menu_dict["attributes"]')
        type_debug(sub_menus, list, 'menu_dict["sub_menus"]')
        if attributes:
            element_type_check(
                attributes.keys(),
                str,
                'menu_dict["attributes"].keys()'
            )
            element_type_check(
                attributes.values(),
                Union[int, float, str, bool, list, dict, NoneType],
                'menu_dict["attributes"].values()'
            )
        if sub_menus:
            element_type_check(
                sub_menus,
                dict,
                'menu_dict["sub_menus"]'
            )
        if title.strip() == "":
            title = "untitled"
        menu_instance = cls(title)
        menu_instance.__attributes.update(attributes)
        for _menu_dict in sub_menus:
            _menu_instance = cls.instantiate_from_dict(_menu_dict)
            menu_instance.add_sub_menu(menu_instance=_menu_instance)
        return menu_instance

    @_exception
    @type_check
    def get_structure(
        self,
        return_title: bool = True,
        type_of_return: str = "deque"
    ):
        structure: deque[tuple[int, "Menu" | str]] = deque()
        level = 0
        deque_ = deque([(level, self)])
        while deque_:
            level, menu_instance = deque_.popleft()
            if return_title:
                structure.append((level, menu_instance.title))
            else:
                structure.append((level, menu_instance))
            f = lambda menu_instance: (level + 1, menu_instance)
            children = map(f, reversed(menu_instance.sub_menus))
            deque_.extendleft(children)
        match type_of_return.lower():
            case "d" | "deque":
                return structure
            case "t" | "tuple":
                return tuple(structure)
            case "l" | "list":
                return list(structure)
            case "dict":
                cursor: list[int] = []
                structure_dict: dict[tuple, "Menu" | str] = {}
                for level, node in structure:
                    if level == 0:
                        structure_dict[()] = node
                        latest_level = level
                        continue
                    if level > latest_level:
                        cursor.append(0)
                    else:
                        if level < latest_level:
                            cursor = cursor[0:level]
                        cursor[-1] += 1
                    structure_dict[tuple(cursor)] = node
                    latest_level = level
                return structure_dict
            case _:
                return ErrorInfo("undefined type of return")

    def __get_tree_indent(self):
        return self.__tree_indent

    @_exception
    @type_check
    def __set_tree_indent(self, tree_indent: int):
        if tree_indent <= 0:
            message = "argument 'tree_indent' must be greater than 0"
            return ErrorInfo(message)
        self.__tree_indent = tree_indent

    def __del_tree_indent(self):
        del self.__tree_indent

    tree_indent = property(
        fget=__get_tree_indent,
        fset=__set_tree_indent,
        fdel=__del_tree_indent
    )

    @_exception
    @type_check
    def tree(
        self, *,
        type_of_return: str = "str",
        tree_indent: Optional[int] = None
    ):
        """
        If argument 'tree_indent' is None, or less than or equal to 0,
        value of 'tree_indent' will be determined by property
        'self.tree_indent'.

        This method depends on the feature that 'dict' is ordered in
        Python 3.7 or later.
        """
        if tree_indent is None or tree_indent <= 0:
            tree_indent = self.__tree_indent
        stems = {
            0: "│" + " " * (tree_indent - 1),
            1: " " + " " * (tree_indent - 1),
            2: "├" + "─" * (tree_indent - 1),
            3: "└" + "─" * (tree_indent - 1)
        }
        if tree_indent > 2:
            stems[2] = stems[2][0:-1] + " "
            stems[3] = stems[3][0:-1] + " "

        structure: dict[tuple, str] = self.get_structure(type_of_return="dict")
        line_deque: deque[str] = deque()
        for locator in structure:
            locator_len = len(locator)
            prefix_list = []
            for i, j in enumerate(locator):
                dummy = (*locator[0:i], j + 1)
                match (i < locator_len - 1, bool(structure.get(dummy, None))):
                    case (True, True):
                        prefix_list.append(stems[0])
                    case (True, False):
                        prefix_list.append(stems[1])
                    case (False, True):
                        prefix_list.append(stems[2])
                    case (False, False):
                        prefix_list.append(stems[3])
            line: str = "".join(prefix_list) + structure[locator]
            line_deque.append(line)
        match type_of_return.lower():
            case "d" | "deque":
                return line_deque
            case "t" | "tuple":
                return tuple(line_deque)
            case "l" | "list":
                return list(line_deque)
            case "s" | "str":
                return "\n".join(line_deque)
            case _:
                return ErrorInfo("undefined type of return")

    def export(self) -> dict:
        cursor: list[list[dict]] = []
        structure: deque[tuple[int, "Menu"]] = self.get_structure(False)
        for level, menu_instance in structure:
            _menu_dict: dict = {}
            _menu_dict["title"] = menu_instance.title
            _menu_dict["attributes"] = deepcopy(menu_instance.attributes)
            _menu_dict["sub_menus"] = []
            if level == 0:
                cursor.append([])
            elif level > latest_level:
                cursor.append(cursor[-1][-1]["sub_menus"])
            elif level == latest_level:
                pass
            elif level < latest_level:
                cursor = cursor[0:level + 1]
            cursor[-1].append(_menu_dict)
            latest_level: int = level
        menu_dict: dict = cursor[0][0]
        return menu_dict

    def __str__(self) -> str:
        return str(self.export())

    @type_check
    def save_as_json(self, path: Optional[str] = None):
        """
        Save Menu instance as json file.

        If file extension is missing, or not 'json', saving path will append
        suffix '.json'.
        """
        if path is None:
            path = "__menu__.json"
        if not path.endswith(".json"):
            path += ".json"
        with open(path, "w") as f:
            json.dump(self.export(), f, indent=4)

    @classmethod
    @type_check
    def load_from_json(cls, path: Optional[str] = None) -> "Menu":
        """
        Instantiate Menu instance from json file.

        If file extension is missing, or not 'json', loading path will append
        suffix '.json'.
        """
        if path is None:
            path = "__menu__.json"
        with open(path, "r") as f:
            menu_instance = cls.instantiate_from_dict(json.load(f))
        return menu_instance

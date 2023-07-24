from __future__ import annotations

import os
import platform
import sys
from typing import *

NULL = -1  # Value which represents a gate which has not received a valid input yet
TRUE = int(True)
FALSE = int(False)
POWER_TYPE = Literal[-1, 0, 1]

INFO = 0
WARNING = 1
ERROR = 2
INFO_PRINT_ON = True  # Set false to disable informational prints

GATE_ID = 0


def strip_num_from_label(label: str) -> str:
    index = label.find('#')
    if index != -1 and index < len(label) - 1:
        return label[:index + 1]
    else:
        return label


def new_gate_label(name: str) -> str:
    global GATE_ID
    name = strip_num_from_label(name) + str(GATE_ID)
    GATE_ID += 1
    return name


def turn_info_print_off() -> None:
    global INFO_PRINT_ON
    INFO_PRINT_ON = False


def turn_info_print_on() -> None:
    global INFO_PRINT_ON
    INFO_PRINT_ON = True


def log_msg(level: int, msg: str, err_type=None) -> None:
    global INFO, WARNING, ERROR
    if INFO_PRINT_ON and level == INFO:
        print("[INFO]:", msg)
    elif level == WARNING:
        print("[WARNING]:", msg)
    elif level == ERROR:
        print("[ERROR]:", msg)
        if err_type is None:
            sys.exit(-1)
        else:
            raise err_type(msg)


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = ""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS if Windows or _MEIDrqOib if Linux,
        # Mac is currently unknown
        if platform.system() == "Windows":
            base_path = sys._MEIPASS
        elif platform.system() == "Linux":
            base_path = sys._MEIDrqOib
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def join_folder_file(folder: str, file: str):
    """Gets actual file path"""
    return resource_path(os.path.join(folder, file))


def list_contains(ls: list[Any], val: Any) -> (bool, int):
    """Returns (bool: if val is in ls, int: gate index if exists)"""
    for i in range(len(ls)):
        if ls[i] == val:
            return True, i
    return False, -1


def output(value: list[int]) -> int:
    """Function for output gates, doesn't do anything"""
    return value[0]


def power(value: list[int]) -> int:
    """Function for power gates, doesn't do anything"""
    return value[0]


def logic_not(value: list[int]) -> int:
    return int(not value[0]) if value[0] != NULL else NULL


def logic_and(input_gates: list[int]) -> int:
    if len(input_gates) < 2 or list_contains(input_gates, NULL)[0]:
        return NULL

    result = TRUE
    for val in input_gates:
        result &= val
    return result


def logic_nand(input_gates: list[int]) -> int:
    ret = logic_and(input_gates)
    return int(not ret) if ret != NULL else NULL


def logic_or(input_gates: list[int]) -> int:
    if len(input_gates) < 2 or list_contains(input_gates, NULL)[0]:
        return NULL
    result = FALSE
    for val in input_gates:
        result |= val
    return result


def logic_xor(input_gates: list[int]) -> int:
    """(A XOR B) OR (B XOR C) OR ...(n XOR n+1)"""
    if len(input_gates) < 2 or list_contains(input_gates, NULL)[0]:
        return NULL

    result = FALSE
    for i in range(len(input_gates)):
        result |= (input_gates[i - 1] ^ input_gates[i])
    return result


# Folder for button images
IMG_FOLDER = "images/"
GATE_IMG_FOLDER = "images/gates"
CIRCUIT_IMG_FOLDER = "images/custom_circuits"


class FunctionCallback:
    """Stores a function, its positional arguments, and it's named arguments.
       Useful for when you need a callback function that takes arguments"""
    def __init__(self, fn: Callable, *args, **kwargs):  #: Optional[list] = None):
        self.fn = fn
        self.args = [*args]
        self.kwargs = {**kwargs}

    def __call__(self):
        return self.fn(*self.args, **self.kwargs)


class IntClass:
    """Store an int that multiple objects might reference, changing this will affect all referencing objects."""
    def __init__(self, value: int = 0, trace: Optional[FunctionCallback] = None):
        self.value = value
        self.cb = trace

    def set(self, val: int) -> None:
        self.value = val
        if self.cb:
            self.cb()

    def get(self) -> int:
        return self.value

    def trace(self, callback: FunctionCallback) -> None:
        self.cb = callback


class BaseGate:
    """The virtual form of the logic gate, does the gate value calculations.
       Stores the input gates to calculate its current value.  Stores the output gates to update their values."""
    def __init__(self, func: Callable, label: str, ins: Optional[list[BaseGate]] = None,
                 outs: Optional[list[BaseGate]] = None,
                 out: IntClass = IntClass(value=NULL)):
        self.func = func
        self.inputs = ins if ins is not None else []
        self.out = out
        # self.out.trace(FunctionCallback())
        self.output_gates = outs if outs is not None else []
        self.label = label

    def output(self) -> int:
        """Returns output of the gate by recursively calculating the outputs of the gate's inputs"""
        if len(self.inputs) == 0:
            return self.out.get()

        self.out.set(self.func([inp.output() for inp in self.inputs]))

        return self.out.get()

    def set_label(self, label: str) -> None:
        """Set gate name"""
        self.label = label

    def get_label(self) -> str:
        return self.label

    def remove_input(self, inp: BaseGate) -> None:
        """Remove gate from inputs"""
        if inp in self.inputs:
            self.inputs.remove(inp)

    def remove_output(self, out: BaseGate) -> None:
        """remove gate from outputs"""
        if out in self.output_gates:
            self.output_gates.remove(out)

    def get_all_input_gates(self, ls: list) -> list[BaseGate]:
        """Returns list of all parent gates"""
        for gate in self.inputs:
            ls.append(gate)
            gate.get_all_input_gates(ls)

        return ls

    def get_func(self) -> Callable:
        return self.func

    def get_input_gates(self) -> list[BaseGate]:
        return self.inputs

    def get_output_gates(self) -> list[BaseGate]:
        return self.output_gates

    def set_output(self, out: int) -> None:
        """Sets value of the gate"""
        self.out.set(out)

    def update_output_values(self) -> None:
        """Updates the values of all child gates.
        Called when the value of a gate is changed and needs to be propogated forward"""
        self.output()
        for gate in self.output_gates:
            gate.update_output_values()

    def delete(self) -> None:
        self.set_output(NULL)
        for input_gate in self.inputs:
            input_gate.remove_output(self)

        for output_gate in self.output_gates:
            output_gate.remove_input(self)
            output_gate.set_output(NULL)
            output_gate.update_output_values()

    def __str__(self) -> str:
        return "{0},{1},{2}".format(hex(id(self)), self.func.__name__, self.out.get())


def test_half_adder():
    inputs = [[0, 0],
              [0, 1],
              [1, 0],
              [1, 1]]

    for input_list in inputs:
        in1 = BaseGate(power, label=new_gate_label(power.__name__), ins=None, out=IntClass(input_list[0]))
        in2 = BaseGate(power, label=new_gate_label(power.__name__), ins=None, out=IntClass(input_list[1]))
        xor = BaseGate(logic_xor, label=new_gate_label(logic_xor.__name__), ins=[in1, in2])
        and_gate = BaseGate(logic_and, label=new_gate_label(logic_and.__name__), ins=[in1, in2])

        sum1 = xor.output()
        carry = and_gate.output()
        print("Inputs:", input_list)
        print("Sum: {0} Carry: {1}".format(int(sum1), int(carry)))


def test_full_adder():
    inputs = [[0, 0, 0],
              [0, 0, 1],
              [0, 1, 0],
              [0, 1, 1],
              [1, 0, 0],
              [1, 0, 1],
              [1, 1, 0],
              [1, 1, 1]]

    for input_list in inputs:
        in1 = BaseGate(power, label=new_gate_label(power.__name__), ins=None, out=IntClass(input_list[0]))
        in2 = BaseGate(power, label=new_gate_label(power.__name__), ins=None, out=IntClass(input_list[1]))
        carry = BaseGate(power, label=new_gate_label(power.__name__), ins=None, out=IntClass(input_list[2]))

        xor1 = BaseGate(logic_xor, label=new_gate_label(logic_xor.__name__), ins=[in1, in2])
        and1 = BaseGate(logic_and, label=new_gate_label(logic_and.__name__), ins=[in1, in2])

        xor2 = BaseGate(logic_xor, label=new_gate_label(logic_xor.__name__), ins=[xor1, carry])
        and2 = BaseGate(logic_and, label=new_gate_label(logic_and.__name__), ins=[xor1, carry])

        or1 = BaseGate(logic_or, label=new_gate_label(logic_or.__name__), ins=[and1, and2])

        sum1 = xor2.output()
        carry = or1.output()

        print("Inputs:", input_list)
        print("Sum: {0} Carry: {1}".format(int(sum1), int(carry)))


if __name__ == "__main__":
    test_half_adder()
    test_full_adder()

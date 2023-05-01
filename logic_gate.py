########################################################################################################################
# File: logic_gate.py
# Author: Peter McCusker
# License:
# Date: 01/04/2023
# Description: Defines global variables used throughout the program. Defines the logical functions used by the gates.
#              Constructs the LogicGate class which is what each gate is made of. Consists of a function which returns
#              TRUE/FALSE/NULL, a picture
########################################################################################################################
from __future__ import annotations
import sys
import os
import threading
import platform
from time import *
from typing import *
from tkinter import *
import tkinter.font as font

NULL = -1  # Value which represents a gate which has not received a valid input yet
TRUE = int(True)
FALSE = int(False)
POWER_TYPE = Literal[-1, 0, 1]

INFO = 0
WARNING = 1
ERROR = 2
INFO_PRINT_ON = True  # Set false to disable informational prints

GATE_ID = 0


def new_gate_label(name: str) -> str:
    global GATE_ID
    name = name + str(GATE_ID)
    GATE_ID += 1
    return name


def turn_info_print_off():
    global INFO_PRINT_ON
    INFO_PRINT_ON = False


def turn_info_print_on():
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
            raise err_type()


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = ""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS if Windows or _MEIDrqOib if Linux
        if platform.system() == "Windows":
            base_path = sys._MEIPASS
        elif platform.system() == "Linux":
            base_path = sys._MEIDrqOib
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def join_folder_file(folder: str, file: str):
    return resource_path(os.path.join(folder, file))


def list_contains(ls: list[Any], val: Any) -> (bool, int):
    for i in range(len(ls)):
        if ls[i] == val:
            return True, i
    return False, -1


def output(value: list[int]) -> int:
    return value[0]


def power(value: list[int]) -> int:
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


def logic_clock(gate) -> int:
    if not gate.get_event().is_set() and not ClockTk.clocks_paused:  # Might be broke
        # call f() again in 60 seconds
        threading.Timer(gate.get_rate(), logic_clock, [gate]).start()
        gate.toggle()

    return gate.output()


# Folder for button images
IMG_FOLDER = "images/"
GATE_IMG_FOLDER = "images/gates"
CIRCUIT_IMG_FOLDER = "images/custom_circuits"


class FunctionCallback:

    def __init__(self, fn: Callable, *args, **kwargs):  #: Optional[list] = None):
        self.fn = fn
        self.args = [*args]
        self.kwargs = {**kwargs}

    def __call__(self):
        return self.fn(*self.args, **self.kwargs)


class IntClass:
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


# Add new gates to this list
# If you change the order of these gates, then the order must be the same in gui_build_input_selection_menu()
######################### Testing Class ################################################################################
class TestInput:
    """The barest form of the input class, just does the output"""

    def __init__(self, func: Callable, label: str, ins: Optional[list[TestInput]] = None, outs: Optional[list[TestInput]] = None,
                 out: IntClass = IntClass(value=NULL)):
        self.func = func
        self.inputs = ins if ins is not None else []
        self.out = out
        # self.out.trace(FunctionCallback())
        self.output_gates = outs if outs is not None else []
        self.label = label

    def output(self) -> int:
        if len(self.inputs) == 0:
            return self.out.get()

        self.out.set(self.func([inp.output() for inp in self.inputs]))

        return self.out.get()

    def set_label(self, label: str) -> None:
        self.label = label

    def get_label(self) -> str:
        return self.label

    def add_connection(self, out: TestInput) -> None:
        out.inputs.append(self)
        self.output_gates.append(out)
        print("Added Connection between:", self, out)

    def remove_input(self, inp: TestInput) -> None:
        if inp in self.inputs:
            self.inputs.remove(inp)

    def remove_output(self, out: TestInput) -> None:
        if out in self.output_gates:
            self.output_gates.remove(out)

    def get_all_input_gates(self, ls: list) -> list:
        for gate in self.inputs:
            ls.append(gate)
            gate.get_all_input_gates(ls)

        return ls

    def get_func(self) -> Callable:
        return self.func

    def get_input_gates(self) -> list[TestInput]:
        return self.inputs

    def get_output_gates(self) -> list[TestInput]:
        return self.output_gates

    def set_output(self, out: int) -> None:
        self.out.set(out)

    def __str__(self) -> str:
        return "{0},{1},{2}".format(hex(id(self)), self.func.__name__, self.out.get())


def test_half_adder():
    inputs = [[0, 0],
              [0, 1],
              [1, 0],
              [1, 1]]

    for input_list in inputs:
        in1 = TestInput(power, ins=None, out=input_list[0])
        in2 = TestInput(power, ins=None, out=input_list[1])
        xor = TestInput(logic_xor, ins=[in1, in2])
        and_gate = TestInput(logic_and, ins=[in1, in2])

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
        in1 = TestInput(power, ins=None, out=input_list[0])
        in2 = TestInput(power, ins=None, out=input_list[1])
        carry = TestInput(power, ins=None, out=input_list[2])

        xor1 = TestInput(logic_xor, ins=[in1, in2])
        and1 = TestInput(logic_and, ins=[in1, in2])

        xor2 = TestInput(logic_xor, ins=[xor1, carry])
        and2 = TestInput(logic_and, ins=[xor1, carry])

        or1 = TestInput(logic_or, ins=[and1, and2])

        sum1 = xor2.output()
        carry = or1.output()

        print("Inputs:", input_list)
        print("Sum: {0} Carry: {1}".format(int(sum1), int(carry)))


def get_line_fill(value: int) -> str:
    """Gets what color a line should be based on its value"""
    if value == NULL or not bool(LogicGate.line_colors_on):
        return LogicGate.line_fill_null
    elif value == TRUE:
        return LogicGate.line_fill_true
    else:
        return LogicGate.line_fill_false


class Input:
    def __init__(self, image_file: str, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL)):
        self.label = label  # Gate Name
        self.output_gates = []
        self.inputs = []
        self.image_file = image_file
        self.img = PhotoImage(file=self.image_file)
        self.center = center
        self.border_width = 1  # Width of border when gate is selected
        # If this is an output gate, make the border box larger to increase visibility
        self.border_offset = self.border_width
        self.canvas = canvas
        self.rect_id = NULL
        self.input_line_ids = []
        self.output_line_ids = []
        self.width, self.height = 0, 0
        self.input_id = self.canvas.create_image(self.center[0], self.center[1], image=self.img) \
            if center != (NULL, NULL) else NULL

        bbox = self.canvas.bbox(self.input_id)
        if bbox is not None:  # Bbox is not None when the gate is placed on the canvas
            self.width, self.height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    def set_image_file(self, filename: str) -> None:
        self.image_file = filename
        if self.input_id is not NULL:
            self.canvas.delete(self.input_id)
            self.img = PhotoImage(file=self.image_file)
            self.input_id = self.canvas.create_image(self.center[0], self.center[1], image=self.img) \
                                                     if self.center != (NULL, NULL) else NULL

    def get_image_file(self) -> str:
        return self.image_file

    def set_label(self, label: str) -> None:
        self.label = label

    def get_label(self) -> str:
        return self.label

    def get_output_gates(self) -> list[LogicGate]:
        return self.output_gates

    def add_rect(self) -> int:
        if self.rect_id < 0:
            self.rect_id = self.canvas.create_rectangle(self.top_left()[0] - self.border_offset,
                                                        self.top_left()[1] - self.border_offset,
                                                        self.bottom_right()[0] + self.border_offset,
                                                        self.bottom_right()[1] + self.border_offset,
                                                        width=self.border_width, outline='black')
        return self.rect_id

    def add_input_line(self, line_id: int) -> None:
        self.input_line_ids.append(line_id)

    def add_output_line(self, line_id: int) -> None:
        self.output_line_ids.append(line_id)

    def add_connection(self, dest: Union[Input | TestInput | Circuit]) -> None:
        self.output_gates.append(dest)
        dest.inputs.append(self)
        print("[Input] Added Connection between:", self, dest)

    def num_outputs(self) -> int:
        return len(self.output_gates)

    def remove_rect(self) -> None:
        if self.rect_id >= 0:
            self.canvas.delete(self.rect_id)
            self.rect_id = -1

    def remove_line(self, line_id: int) -> None:
        self.canvas.delete(line_id)

        if list_contains(self.input_line_ids, line_id)[0]:
            self.input_line_ids.remove(line_id)
        if list_contains(self.output_line_ids, line_id)[0]:
            self.output_line_ids.remove(line_id)

    def remove_all_lines(self) -> None:
        for line_id in self.input_line_ids:
            self.remove_line(line_id)

        for line_id in self.output_line_ids:
            self.remove_line(line_id)

    def get_input_gates(self) -> list:
        return self.inputs

    def get_all_input_gates(self, ls: list) -> list:
        for gate in self.inputs:
            ls.append(gate)
            gate.get_all_input_gates(ls)

        return ls

    def move(self, x: int, y: int) -> None:
        pass

    def set_id(self, new_id: int) -> None:
        self.input_id = new_id

    def get_id(self) -> int:
        return self.input_id

    def set_rect_id(self, new_id: int) -> None:
        self.rect_id = new_id

    def get_rect_id(self) -> int:
        return self.rect_id

    def image(self) -> PhotoImage:
        return self.img

    def get_center(self) -> (int, int):
        return self.center

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def remove_input(self, inp: Input):
        contains, gate_index = list_contains(self.inputs, inp)
        if contains:
            self.inputs.remove(inp)
            self.remove_line(self.input_line_ids[gate_index])

    def remove_output(self, destination: Input) -> None:
        contains, gate_index = list_contains(self.output_gates, destination)
        if contains:
            self.output_gates.remove(destination)
            self.remove_line(self.output_line_ids[gate_index])

    def num_inputs(self) -> int:
        return len(self.inputs)

    def delete_img(self) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)
        self.remove_all_lines()
        self.input_id = self.rect_id = NULL

    def delete(self) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)

        for input_gate in self.inputs:
            input_gate.remove_output(self)

        for output_gate in self.output_gates:
            output_gate.remove_input(self)
            output_gate.set_output(NULL)

        self.remove_all_lines()

        self.input_id = self.rect_id = NULL

    def get_canvas(self) -> Canvas:
        return self.canvas

    def top_left(self) -> (int, int):
        return self.center[0] - self.get_width() // 2, self.center[1] - self.get_height() // 2

    def bottom_right(self) -> (int, int):
        return self.center[0] + self.get_width() // 2, self.center[1] + self.get_height() // 2


class LogicGate(Input):
    """Class used to depict a logic gate.  Each has an associated function and image"""
    line_colors_on = True
    line_fill_true = "green"
    line_fill_false = "red"
    line_fill_null = "black"

    def __init__(self, func: Callable, image_file: str, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), out: int = NULL):
        Input.__init__(self, image_file, label=label, canvas=canvas, center=center)
        self.func = func
        self.out = IntClass(value=out)  # Output value
        self.base_gate = TestInput(func=func, label=label, out=self.out)
        self.border_offset = self.border_width
        bbox = self.canvas.bbox(self.input_id)
        if bbox is not None:  # Bbox is not None when the gate is placed on the canvas
            self.width, self.height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    @staticmethod
    def construct_copy(old: LogicGate, pos: (int, int)) -> LogicGate:
        return LogicGate(old.get_func(), image_file=old.get_image_file(), label=new_gate_label(old.get_label()),
                         canvas=old.get_canvas(), center=pos, out=old.output())

    def base(self) -> TestInput:
        return self.base_gate

    def get_base_input_gates(self) -> list[TestInput]:
        return self.base_gate.get_input_gates()

    def get_base_output_gates(self) -> list[TestInput]:
        return self.base_gate.get_output_gates()

    def output(self) -> int:
        return self.base().output()

    def add_connection(self, out: Union[LogicGate | Circuit | TestInput]) -> None:
        if not isinstance(out, TestInput):
            self.output_gates.append(out)
            out.inputs.append(self)
            if isinstance(out, LogicGate):
                self.base_gate.add_connection(out.base())
        else:
            self.base_gate.add_connection(out)
        print("[LogicGate] Added Connection between:", self, self.output_gates, out, out.get_input_gates())

    def remove_input(self, inp: LogicGate | TestInput):
        if isinstance(inp, LogicGate):
            contains, gate_index = list_contains(self.inputs, inp)
            if contains:
                self.inputs.remove(inp)
                self.base_gate.remove_input(inp.base())
                self.remove_line(self.input_line_ids[gate_index])
        else:
            contains, gate_index = list_contains(self.base().get_input_gates(), inp)
            if contains:
                self.base().remove_input(inp)

    def remove_output(self, destination: LogicGate | TestInput) -> None:
        contains, gate_index = list_contains(self.output_gates, destination)
        if contains:
            self.output_gates.remove(destination)
            self.remove_line(self.output_line_ids[gate_index])

        if isinstance(destination, LogicGate):
            contains, gate_index = list_contains(self.output_gates, destination)
            if contains:
                self.output_gates.remove(destination)
                self.base_gate.remove_output(destination.base())
                self.remove_line(self.input_line_ids[gate_index])
        else:
            contains, gate_index = list_contains(self.base().get_output_gates(), destination)
            if contains:
                self.base().remove_output(destination)

    def set_output(self, out: int) -> None:
        self.out.set(out)
        self.update_line_colors()

    def get_func(self) -> Callable:
        return self.func

    def update_line_colors(self) -> None:
        output_val = self.output()
        if self.output_gates is None:
            return

        fill = get_line_fill(output_val)
        print("OG:", self,  self.output_gates, self.output_line_ids)
        for i in range(len(self.output_gates)):
            self.canvas.itemconfig(self.output_line_ids[i], fill=fill)
        # for base_out in self.base().get_output_gates():
        #     base_out.output()

        for gate in self.output_gates:
            gate.update_line_colors()

    def add_line(self, dest_gate: LogicGate) -> int:
        if is_power_gate(dest_gate) or is_clock(dest_gate) or (is_not_gate(dest_gate) and len(dest_gate.inputs) > 0) \
           or not (not is_parent(dest_gate, self) and dest_gate not in self.get_output_gates()) or \
                (is_output_gate(dest_gate) and len(dest_gate.inputs) > 0):
            print("invalid line between", self, type(self), dest_gate, type(dest_gate))
            return -1

        src_pos, dest_pos = (self.bottom_right()[0], self.get_center()[1]), \
                            (dest_gate.top_left()[0], dest_gate.get_center()[1])

        self.add_connection(dest_gate)
        dest_out = dest_gate.output()

        line_color = get_line_fill(dest_out)

        line_id = self.canvas.create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4, fill=line_color)
        self.add_output_line(line_id)
        dest_gate.add_input_line(line_id)

        self.update_line_colors()

        return line_id

    def move(self, x: int, y: int) -> None:
        self.center = (x, y)
        # Move Gate Image and Border
        self.canvas.coords(self.rect_id, self.top_left()[0] - self.border_offset,
                           self.top_left()[1] - self.border_offset,
                           self.bottom_right()[0] + self.border_offset, self.bottom_right()[1] + self.border_offset)

        self.canvas.coords(self.input_id, x, y)
        # Update all incoming lines to new position
        left_center_pos = (self.top_left()[0], self.get_center()[1])  # Left-Center Point to connect src gates
        for i in range(len(self.inputs)):
            src_pos = (self.inputs[i].bottom_right()[0], self.inputs[i].get_center()[1])
            self.canvas.coords(self.input_line_ids[i], src_pos[0], src_pos[1], left_center_pos[0], left_center_pos[1])
        # Update all outgoing lines to new position
        right_center_pos = (self.bottom_right()[0], self.get_center()[1])  # Right-Center Point to connect src gates
        for i in range(len(self.output_gates)):
            dest_pos = (self.output_gates[i].top_left()[0], self.output_gates[i].get_center()[1])
            self.canvas.coords(self.output_line_ids[i], dest_pos[0], dest_pos[1],
                               right_center_pos[0], right_center_pos[1])

    def remove_connection(self, other: LogicGate, self_is_parent: bool) -> None:
        if self_is_parent:
            self.remove_output(other)
            other.remove_input(self)
            other.set_output(NULL)
        else:
            self.remove_input(other)
            other.remove_output(self)
            self.set_output(NULL)

    def remove_base_connection(self, other: TestInput, self_is_parent: bool) -> None:
        if self_is_parent:
            self.base_gate.remove_output(other)
            other.remove_input(self.base_gate)
            other.set_output(NULL)
        else:
            self.base_gate.remove_input(other)
            other.remove_output(self.base_gate)
            self.set_output(NULL)

    def __str__(self) -> str:
        return "{0},{1},{2}".format(self.func.__name__, self.center, self.out.get())


class OutputGate(LogicGate):

    def __init__(self, image_file: str, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), out: int = NULL):
        LogicGate.__init__(self, output, image_file, label=label, canvas=canvas, center=center, out=out)
        self.output_gates = None
        # If this is an output gate, make the border box larger to increase visibility
        self.border_offset = self.border_width + 5
        # If this is an output gate, create a rectangle for the gate instead of using an image, allows rectangle
        # to change color when the output value changes
        self.canvas.delete(self.input_id)
        self.input_id = self.canvas.create_rectangle(self.top_left()[0],
                                                     self.top_left()[1],
                                                     self.bottom_right()[0],
                                                     self.bottom_right()[1],
                                                     width=2, outline='black')

        bbox = self.canvas.bbox(self.input_id)
        if bbox is not None:  # Bbox is not None when the gate is placed on the canvas
            self.width, self.height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    @staticmethod
    def construct_copy(old: OutputGate, pos: (int, int)) -> OutputGate:
        return OutputGate(image_file=old.get_image_file(), label=new_gate_label(old.get_label()), canvas=old.get_canvas(),
                          center=pos)

    def add_line(self, dest_gate: LogicGate) -> int:
        pass

    def move(self, x: int, y: int) -> None:
        self.center = (x, y)
        # Move Gate Image and Border
        self.canvas.coords(self.rect_id, self.top_left()[0] - self.border_offset,
                           self.top_left()[1] - self.border_offset,
                           self.bottom_right()[0] + self.border_offset, self.bottom_right()[1] + self.border_offset)

        self.canvas.coords(self.input_id, self.top_left()[0], self.top_left()[1],
                           self.bottom_right()[0], self.bottom_right()[1])
        # Update all incoming lines to new position
        left_center_pos = (self.top_left()[0], self.get_center()[1])  # Left-Center Point to connect src gates
        for i in range(len(self.inputs)):
            src_pos = (self.inputs[i].bottom_right()[0], self.inputs[i].get_center()[1])
            self.canvas.coords(self.input_line_ids[i], src_pos[0], src_pos[1],
                                                       left_center_pos[0], left_center_pos[1])

    def update_line_colors(self) -> None:
        output_val = self.output()
        fill = get_line_fill(output_val)
        # If line colors are off, still color output gate
        if not LogicGate.line_colors_on:
            fill = self.line_fill_true if output_val == TRUE else self.line_fill_false \
                if output_val == FALSE else self.line_fill_null

        self.canvas.itemconfig(self.input_id, outline=fill)

        LogicGate.update_line_colors(self)

    def delete(self) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)

        for input_gate in self.inputs:
            input_gate.remove_output(self)

        self.remove_all_lines()
        self.input_id = self.rect_id = -1


class ClockTimer:
    """Asynchronous Timer for a clock object"""

    def __init__(self, func, rate, gate):
        self.startTime = 0
        self.endTime = 0
        self.gate = gate
        self.func = func
        self.rate = rate
        self.timer = threading.Timer(self.rate, self.func, args=[self.gate])
        self.started = False

    def pause(self) -> float:
        self.endTime = time()
        self.timer.cancel()
        return self.endTime

    def start(self) -> float:
        self.timer.cancel()
        self.startTime = self.endTime = time()
        self.timer = threading.Timer(self.rate, self.func, args=[self.gate])
        self.timer.start()
        self.started = True
        return self.startTime

    def resume(self) -> None:
        self.timer = threading.Timer(self.rate - (self.endTime - self.startTime), self.func, args=[self.gate])
        self.timer.start()

    def cancel(self) -> None:
        self.timer.cancel()
        self.startTime = self.endTime = 0
        self.started = False


class ClockTk(LogicGate):
    """An alternating power source, which toggles after self.rate seconds have passed"""
    clocks_paused = True

    def __init__(self, image_file: str, update_rate: float, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), default_state: int = TRUE):
        # A clock has no inputs
        super().__init__(logic_clock, image_file, label, canvas, center, out=default_state)
        self.timer = ClockTimer(logic_clock, update_rate, self)
        self.rate = update_rate
        self.default_state = default_state
        self.stop_event = threading.Event()
        self.first_run = True

    @staticmethod
    def construct_copy(old: ClockTk, pos: (int, int)) -> ClockTk:
        return ClockTk(update_rate=old.get_rate(), image_file=old.get_image_file(), label=new_gate_label(old.get_label()),
                       canvas=old.get_canvas(), center=pos, default_state=old.default_state)

    def output(self) -> int:
        if len(self.inputs) == 0:
            return self.out.get()

        self.out.set(self.func(self))

        return self.out.get()

    def toggle(self) -> int:
        self.set_output(not self.out.get())
        return self.out.get()

    def delete(self) -> None:
        self.stop()
        LogicGate.delete(self)

    def start(self) -> None:
        if not self.timer.started:
            self.timer.start()
        else:
            self.timer.resume()

    def stop(self) -> None:
        self.timer.cancel()
        self.set_output(self.default_state)

    def pause(self) -> None:
        self.timer.pause()

    def set_default_state(self, state: int) -> None:
        self.out = state
        self.default_state = state

    def set_rate(self, rate: float) -> None:
        self.rate = rate

    def get_rate(self) -> float:
        return self.rate

    def get_event(self) -> threading.Event:
        return self.stop_event

    def is_first_run(self) -> bool:
        return self.first_run

    def first_run_done(self) -> None:
        self.first_run = False

    def __str__(self) -> str:
        return "{0},{1},{2},{3}".format(self.func.__name__, self.center, self.default_state, self.rate)


class Circuit(Input):
    def __init__(self, image_file: str, canvas: Canvas, font: font.Font, label: str = "",
                 center: (int, int) = (NULL, NULL), ):
        Input.__init__(self, image_file=image_file, label=label, canvas=canvas, center=center)
        # Holds which inside gates are marked as input/output
        self.connections = {
            "inputs": {},
            "outputs": {}
        }
        self.label_id = NULL
        self.font = font

        self.output_line_info = {}
        self.inside_gates = {}

        self.label_id = self.canvas.create_text(center[0], center[1] + 10 + self.get_height() // 2,
                                                text=self.get_label(), fill='black', font=self.font)

    @staticmethod
    def construct_copy(old: Circuit, pos: (int, int)) -> Circuit:
        new_circuit = Circuit(old.get_image_file(), old.get_canvas(), font=old.font, label=old.get_label(), center=pos)

        # Create Copies of each gate in the circuit
        old_gates = old.get_gates()
        for gate in old_gates:
            print("Old gate label:", gate.get_label())
            new_circuit.add_inner_gate(TestInput(gate.get_func(), gate.get_label(),
                                                 ins=[TestInput(in_gate.get_func(), in_gate.get_label(), None, None) for in_gate in gate.get_input_gates()],
                                                 outs=[TestInput(out_gate.get_func(), out_gate.get_label(), None, None) for out_gate in gate.get_output_gates()]))

        new_gates = new_circuit.get_gates()

        for in_label in old.connections["inputs"].keys():
            for gate in new_gates:
                if gate.get_label() == old.connections["inputs"][in_label].get_label():
                    new_circuit.connections["inputs"][in_label] = gate

        for out_label in old.connections["outputs"].keys():
            for gate in new_gates:
                print("checking", gate.get_label(), "==", old.connections["outputs"][out_label].get_label())
                if gate.get_label() == old.connections["outputs"][out_label].get_label():
                    print("Set", new_circuit.connections["outputs"], out_label, 'to', gate)
                    new_circuit.connections["outputs"][out_label] = gate
                    # break

        for label in new_circuit.connections["outputs"].keys():
            gate = new_circuit.connections["outputs"][label]
            for old_out in old.output_line_info.keys():
                if gate.get_label() == old_out.get_label():
                    new_circuit.output_line_info[gate] = []

        print("new:", new_circuit.connections)
        return new_circuit

    def set_font(self, new_font: font.Font) -> None:
        self.font = new_font
        self.canvas.itemconfig(self.label_id, font=self.font)

    def add_inner_gate(self, gate: Union[TestInput]) -> None:
        if gate.get_func() in self.inside_gates.keys():
            self.inside_gates[gate.get_func()].append(gate)
        else:
            self.inside_gates[gate.get_func()] = [gate]

    def add_logic_gate_input(self, src_gate: LogicGate, dest_gate: TestInput) -> None:
        if is_output_gate(src_gate) or (is_not_gate(dest_gate) and len(dest_gate.inputs) > 0) \
           or not (not is_parent(dest_gate, src_gate.base()) and dest_gate not in src_gate.get_output_gates()):
            print("[CIRCUIT]: invalid line between", self, type(self), dest_gate, type(dest_gate))
            return

        src_gate.add_connection(self)
        src_gate.add_connection(dest_gate)
        src_pos, dest_pos = (src_gate.bottom_right()[0], src_gate.get_center()[1]), \
                            (self.top_left()[0], self.get_center()[1])

        line_color = get_line_fill(src_gate.output())

        line_id = self.canvas.create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4, fill=line_color)
        src_gate.add_output_line(line_id)
        self.add_input_line(line_id)
        self.update_line_colors()

    def add_logic_gate_output(self, src_gate: TestInput, dest_gate: LogicGate) -> None:
        if is_power_gate(dest_gate) or is_clock(dest_gate) or (is_not_gate(dest_gate) and len(dest_gate.inputs) > 0) \
                or not (not is_parent(dest_gate.base(), src_gate) and dest_gate not in self.get_output_gates()) or \
                (is_output_gate(dest_gate) and len(dest_gate.inputs) > 0):
            print("[CIRCUIT]: invalid line between", self, type(self), dest_gate, type(dest_gate))
            return

        src_gate.add_connection(dest_gate.base())
        self.add_connection(dest_gate)
        src_pos, dest_pos = (self.bottom_right()[0], self.get_center()[1]), \
                            (dest_gate.top_left()[0], dest_gate.get_center()[1])

        line_color = get_line_fill(src_gate.output())

        line_id = self.canvas.create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4, fill=line_color)
        dest_gate.add_input_line(line_id)
        # self.add_output_line(line_id)
        self.output_line_info[src_gate].append((line_id, dest_gate))
        self.update_line_colors()

    def connect_to_circuit(self, src_gate: TestInput, dest_circuit: Circuit, dest_gate: TestInput) -> None:
        if (is_not_gate(dest_gate) and len(dest_gate.inputs) > 0) \
           or not (not is_parent(dest_gate, src_gate) and dest_gate not in self.get_output_gates()):
            print("[CIRCUIT]: invalid line between", self, type(self), dest_gate, type(dest_gate))
            return

        src_gate.add_connection(dest_gate)
        self.add_connection(dest_circuit)

        src_pos, dest_pos = (self.bottom_right()[0], self.get_center()[1]), \
                            (dest_circuit.top_left()[0], dest_circuit.get_center()[1])

        line_color = get_line_fill(dest_gate.output())

        line_id = self.canvas.create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4, fill=line_color)
        self.output_line_info[src_gate].append((line_id, dest_circuit))
        dest_circuit.add_input_line(line_id)
        self.update_line_colors()

    def remove_inner_gate(self, gate: LogicGate):
        if gate.get_func() in self.inside_gates.keys():
            self.inside_gates[gate.get_func()].remove(gate)

    def update_line_colors(self) -> None:
        # print(self.connections)
        for name in self.connections["outputs"].keys():
            gate = self.connections["outputs"][name]
            fill = get_line_fill(gate.output())
            for (line_id, gate) in self.output_line_info[gate]:
                self.canvas.itemconfig(line_id, fill=fill)
                gate.update_line_colors()

    def move(self, x: int, y: int) -> None:
        self.center = (x, y)
        # Move Gate Image and Border
        self.canvas.coords(self.rect_id, self.top_left()[0] - self.border_offset,
                           self.top_left()[1] - self.border_offset,
                           self.bottom_right()[0] + self.border_offset, self.bottom_right()[1] + self.border_offset)

        self.canvas.coords(self.input_id, x, y)
        self.canvas.coords(self.label_id, x, y + 10 + self.get_height() // 2)
        # Update all incoming lines to new position
        left_center_pos = (self.top_left()[0], self.get_center()[1])  # Left-Center Point to connect src gates
        for i in range(len(self.inputs)):
            src_pos = (self.inputs[i].bottom_right()[0], self.inputs[i].get_center()[1])
            self.canvas.coords(self.input_line_ids[i], src_pos[0], src_pos[1], left_center_pos[0], left_center_pos[1])
        # Update all outgoing lines to new position
        right_center_pos = (self.bottom_right()[0], self.get_center()[1])  # Right-Center Point to connect src gates
        for gate in self.output_line_info.keys():
            for (line_id, dest_gate) in self.output_line_info[gate]:
                dest_pos = (dest_gate.top_left()[0], dest_gate.get_center()[1])
                self.canvas.coords(line_id, dest_pos[0], dest_pos[1], right_center_pos[0], right_center_pos[1])

    def reset_inputs(self) -> None:
        self.connections["inputs"] = {}

    def reset_outputs(self) -> None:
        self.connections["outputs"] = {}
        print("reset outputs")

    def get_output_gates(self) -> list[LogicGate | Circuit]:
        ls = []
        for gate in self.output_line_info:
            for pair in self.output_line_info[gate]:
                ls.append(pair)
        return ls

    def remove_output(self, destination: Circuit | LogicGate,  src: Optional[TestInput] = None) -> None:
        contains, gate_index = list_contains(self.get_output_gates(), destination)
        if contains:
            (line_id, dest_gate) = self.output_line_info[src][gate_index]
            self.output_line_info[src].remove((line_id, dest_gate))
            self.remove_line(line_id)

    def remove_connection(self, src: TestInput, other: LogicGate | Circuit, self_is_parent: bool,
                          other_base: Optional[TestInput] = None) -> None:
        if self_is_parent:
            self.remove_output(other)
            other.remove_input(self)
            src.remove_output(other_base)
            other_base.remove_input(src)
            if not isinstance(other, Circuit):
                other.set_output(NULL)
            else:
                other_base.set_output(NULL)
        else:
            self.remove_input(other)
            other.remove_output(self)
            src.remove_input(other_base)
            other_base.remove_output(src)
            src.set_output(NULL)

    def remove_all_lines(self, gate: Optional[TestInput] = None) -> None:
        for line_id in self.input_line_ids:
            self.remove_line(line_id)

        if gate is not None:
            for (line_id, dest_gate) in self.output_line_info[gate]:
                self.remove_line(line_id)
            self.output_line_info[gate] = []
        else:
            for gate in self.output_line_info:
                for (line_id, dest_gate) in self.output_line_info[gate]:
                    self.remove_line(line_id)
                self.output_line_info[gate] = []

    def set_input(self,  name: str, gate: Optional[TestInput] = None) -> None:
        self.connections["inputs"][name] = gate

    def get_input(self, name: str) -> TestInput:
        return self.connections["inputs"][name]

    def set_output(self,  name: str, gate: Optional[TestInput] = None) -> None:
        self.connections["outputs"][name] = gate
        if gate is not None:
            self.output_line_info[gate] = []

    def get_output(self, name: str) -> TestInput:
        return self.connections["outputs"][name]

    def get_gates(self, key: Optional[Callable] = None) -> list:
        if key and key in self.inside_gates.keys():
            return self.inside_gates[key]
        else:
            ls = []
            for fn in self.inside_gates.keys():
                for gate in self.inside_gates[fn]:
                    ls.append(gate)
            return ls

    def delete(self) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)
        self.delete_text()

        for input_gate in self.inputs:
            input_gate.remove_output(self)

        for (line_id, output_gate) in self.get_output_gates():
            output_gate.remove_input(self)
            output_gate.set_output(NULL)

        self.remove_all_lines()

        self.input_id = self.rect_id = NULL

    def delete_text(self) -> None:
        if self.label_id != NULL:
            self.canvas.delete(self.label_id)
            self.label_id = NULL

    def get_io_gates(self, mode: str) -> dict:
        if mode == 'in':
            return self.connections["inputs"]
        elif mode == 'out':
            return self.connections['outputs']


def is_output_gate(gate: Any) -> bool:
    return isinstance(gate, OutputGate)


def is_power_gate(gate: Input | TestInput) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, TestInput)) and gate.get_func() == power


def is_and_gate(gate: Input | TestInput) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, TestInput)) and gate.get_func() == logic_and


def is_nand_gate(gate: Input | TestInput) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, TestInput)) and gate.get_func() == logic_nand


def is_or_gate(gate: Input | TestInput) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, TestInput)) and gate.get_func() == logic_or


def is_xor_gat(gate: Input | TestInput) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, TestInput)) and gate.get_func() == logic_xor


def is_not_gate(gate: Input | TestInput) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, TestInput)) and gate.get_func() == logic_not


def is_clock(gate: Any) -> bool:
    # return gate.get_func() == logic_clock
    return isinstance(gate, ClockTk)


def is_circuit(gate: Any) -> bool:
    return isinstance(gate, Circuit)


def gate_id(gate: LogicGate) -> int:
    return gate.get_id()


def connection_exists(gate1: TestInput, gate2: TestInput) -> bool:
    return list_contains(gate1.get_input_gates(), gate2)[0] or list_contains(gate1.get_output_gates(), gate2)[0]


def is_parent(parent: TestInput, child: TestInput) -> bool:
    return list_contains(child.get_all_input_gates([]), parent)[0]


class GateInfo:
    def __init__(self, func: Callable, name: str = "", desc: str = "", image_file: Optional[str] = None,
                 callback: Optional[Callable] = None):
        self.info = {
            "func": func,
            "name": name,
            "desc": desc if desc is not None else "",
            "callback": callback,
            "image_file": image_file if image_file is not None else "",
            "image": PhotoImage(file=image_file) if image_file is not None else None
        }
        self.active_gates = []

    def add_active_gate(self, gate: Union[LogicGate | Circuit]) -> None:
        self.active_gates.append(gate)

    def get_active_gates(self) -> list[LogicGate | ClockTk | OutputGate | Circuit]:
        return self.active_gates

    def remove(self, gate: LogicGate) -> None:
        if gate in self.active_gates:
            self.active_gates.remove(gate)

    def keys(self):
        return self.info.keys()

    def __getitem__(self, item: str) -> Union[str | Callable | PhotoImage]:
        return self.info[item]

    def __setitem__(self, key: str, value: Union[str | Callable | PhotoImage]) -> None:
        self.info[key] = value


class GatesInfoRepo:
    def __init__(self):
        self.gate_infos = {}
        self.funcs_dispatch = {}

    def register_gate(self, key: Union[Callable, Circuit], **kwargs) -> None:
        if not isinstance(key, Callable):
            self.register_circuit(key, **kwargs)
            return
        self.gate_infos[key] = GateInfo(key, **kwargs)
        self.funcs_dispatch[key.__name__] = key

    def register_circuit(self, circuit: Circuit, callback: FunctionCallback, image_file: str) -> None:
        self.gate_infos[circuit.get_label()] = GateInfo(None, name=circuit.get_label(), desc="",
                                                        callback=callback, image_file=image_file)
        self.funcs_dispatch[circuit.get_label()] = circuit

    def proper_key(self, gate) -> Union[Callable | str]:
        return gate.get_func() if isinstance(gate, LogicGate) else gate.get_label()

    def attr(self, key, attr: str) -> Union[str | PhotoImage | Callable]:
        if key in self.gate_infos.keys():
            return self.gate_infos[key][attr]

    def get_gate_name(self, gate: Union[LogicGate | Circuit]) -> str:
        return gate.get_func().__name__ if isinstance(gate, LogicGate) else gate.get_label()

    def add_gate(self, gate: Union[LogicGate | Circuit]):
        if self.proper_key(gate) in self.gate_infos.keys():
            self.gate_infos[self.proper_key(gate)].add_active_gate(gate)
        else:
            if isinstance(gate, LogicGate):
                self.register_gate(gate.get_func(), name=self.get_gate_name(gate), desc=None, callback=None)
            elif isinstance(gate, Circuit):
                self.register_gate(gate, image_file=gate.get_image_file(), callback=None)
            self.gate_infos[self.proper_key(gate)].add_active_gate(gate)

    def get_gates(self, func: Union[Callable | str]) -> Optional[list[LogicGate]]:
        if func in self.gate_infos.keys():
            return self.gate_infos[func].get_active_gates()
        return None

    def keys(self):
        return self.gate_infos.keys()

    def func_from_name(self, name: str) -> Callable:
        if name in self.funcs_dispatch.keys():
            return self.funcs_dispatch[name]

    def __getitem__(self, key: Union[Callable | str]) -> Union[GateInfo | Callable]:
        if isinstance(key, Callable) or isinstance(key, str):
            return self.gate_infos[key]
        elif isinstance(key, tuple):
            return self.funcs_dispatch[key[0]]

    def __setitem__(self, key: Callable, value: GateInfo) -> None:
        self.gate_infos[key] = value

    def __len__(self):
        return len(self.keys())

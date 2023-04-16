########################################################################################################################
# File: logic_gate.py
# Author: Peter McCusker
# License:
# Date: 01/04/2023
# Description: Defines global variables used throughout the program. Defines the logical functions used by the gates.
#              Constructs the InputTK class which is what each gate is made of. Consists of a function which returns
#              TRUE/FALSE/NULL, a picture
########################################################################################################################
import sys
from tkinter import *
import threading
import os
from typing import *
from time import *


NULL = -1  # Value which represents a gate which has not received a valid input yet
TRUE = int(True)
FALSE = int(False)

INFO = 0
WARNING = 1
ERROR = 2

INFO_PRINT_ON = True  # Set false to disable informational prints


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
        result |= (input_gates[i-1] ^ input_gates[i])
    return result


def logic_clock(gate) -> int:
    if not gate.get_event().is_set() and not ClockTk.clocks_paused:  # Might be broke
        # call f() again in 60 seconds
        threading.Timer(gate.get_rate(), logic_clock, [gate]).start()
        gate.toggle()

    return gate.output()


# Folder for button images
IMG_FOLDER = "./images"

"""
def get_logic_func_from_name(name: str) -> Optional[Callable]:
    if name == "power":
        return power
    elif name == "output":
        return output
    elif name == "logic_not":
        return logic_not
    elif name == "logic_and":
        return logic_and
    elif name == "logic_nand":
        return logic_nand
    elif name == "logic_or":
        return logic_or
    elif name == "logic_xor":
        return logic_xor
    elif name == "logic_clock":
        return logic_clock
    else:
        return None

def get_input_img_file(func: Callable) -> str:
    global IMG_FOLDER
    img_name = ""
    if func == output:
        img_name = "output.png"
    if func == power:
        img_name = "power.png"
    if func == logic_not:
        img_name = "not.png"
    elif func == logic_and:
        img_name = "and.png"
    elif func == logic_nand:
        img_name = "nand.png"
    elif func == logic_or:
        img_name = "or.png"
    elif func == logic_xor:
        img_name = "xor.png"
    elif func == logic_clock:
        img_name = "clock.png"

    return os.path.join(IMG_FOLDER, img_name)
"""


# Add new gates to this list
# If you change the order of these gates, then the order must be the same in gui_build_input_selection_menu()
######################### Testing Class ################################################################################
class Input:
    """The barest form of the input class, just does the output"""
    def __init__(self, func, ins: Optional[list] = None, out: int = NULL):
        self.func = func
        self.inputs = ins if ins is not None else []
        self.out = out
        self.output_gates = []

    def output(self) -> int:
        if len(self.inputs) == 0:
            return self.out

        if self.func == logic_clock:
            return self.func([inp.output() for inp in self.inputs], self)

        return self.func([inp.output() for inp in self.inputs])

    def add_input(self, inp) -> None:
        self.inputs.append(inp)

    def add_output(self, inp) -> None:
        self.output_gates.append(inp)

    def get_func(self) -> Any:
        return self.func

    def get_input_gates(self) -> list:
        return self.inputs

    def get_output_gates(self) -> list:
        return self.output_gates

    def __str__(self) -> str:
        return "<Input {0} {1} {2}>".format(hex(id(self)), self.func.__name__, self.output())


def test_half_adder():
    inputs = [[0, 0],
              [0, 1],
              [1, 0],
              [1, 1]]

    for input_list in inputs:
        in1 = Input(power, ins=None, out=input_list[0])
        in2 = Input(power, ins=None, out=input_list[1])
        xor = Input(logic_xor, ins=[in1, in2])
        and_gate = Input(logic_and, ins=[in1, in2])

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
        in1 = Input(power, ins=None, out=input_list[0])
        in2 = Input(power, ins=None, out=input_list[1])
        carry = Input(power, ins=None, out=input_list[2])

        xor1 = Input(logic_xor, ins=[in1, in2])
        and1 = Input(logic_and, ins=[in1, in2])

        xor2 = Input(logic_xor, ins=[xor1, carry])
        and2 = Input(logic_and, ins=[xor1, carry])

        or1 = Input(logic_or, ins=[and1, and2])

        sum1 = xor2.output()
        carry = or1.output()

        print("Inputs:", input_list)
        print("Sum: {0} Carry: {1}".format(int(sum1), int(carry)))


def get_line_fill(value: int) -> str:
    """Gets what color a line should be based on its value"""
    if value == NULL or not bool(InputTk.line_colors_on):
        return InputTk.line_fill_null
    elif value == TRUE:
        return InputTk.line_fill_true
    else:
        return InputTk.line_fill_false


class InputTk:
    """Class used to depict a logic gate.  Each has an associated function and image"""
    line_colors_on = True
    line_fill_true = "green"
    line_fill_false = "red"
    line_fill_null = "black"

    def __init__(self, func, gate_info_repo,  label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), ins: Optional[list] = None,
                 out: int = NULL, dims: (int, int) = (0, 0)):
        self.func = func
        self.label = label  # Gate Name
        self.inputs = ins if ins is not None else []
        self.out = out  # Output value
        self.output_gates = []
        self.img = PhotoImage(file=gate_info_repo[func]["image_file"])
        self.center = center
        self.border_width = 1  # Width of border when gate is selected
        # If this is an output gate, make the border box larger to increase visibility
        self.border_offset = self.border_width + 5 if is_output_gate(self) else self.border_width
        self.canvas = canvas
        self.rect_id = NULL
        self.input_line_ids = []
        self.output_line_ids = []
        self.width, self.height = dims[0], dims[1]
        if func != output:
            self.input_id = self.canvas.create_image(self.center[0], self.center[1], image=self.img) \
                if center != (NULL, NULL) else NULL
        else:
            # If this is an output gate, create a rectangle for the gate instead of using an image, allows rectangle
            # to change color when the output value changes
            self.input_id = self.canvas.create_rectangle(self.top_left()[0],
                                                         self.top_left()[1],
                                                         self.bottom_right()[0],
                                                         self.bottom_right()[1],
                                                         width=2, outline='black')

        bbox = self.canvas.bbox(self.input_id)
        if bbox is not None:  # Bbox is not None when the gate is placed on the canvas
            self.width, self.height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    def output(self) -> int:
        if len(self.inputs) == 0:
            return self.out

        if self.func == logic_clock:
            self.out = self.func(self)
        else:
            self.out = self.func([inp.output() for inp in self.inputs])

        return self.out

    def add_input(self, inp) -> None:
        self.inputs.append(inp)

    def add_output(self, inp) -> None:
        self.output_gates.append(inp)

    def set_label(self, label: str) -> None:
        self.label = label

    def get_label(self) -> str:
        return self.label

    def set_output(self, out: int) -> None:
        self.out = out
        self.update_line_colors()

    def get_func(self) -> Any:
        return self.func

    def get_input_gates(self) -> list:
        return self.inputs

    def get_all_input_gates(self, ls: list) -> Union[Any | list]:
        for gate in self.inputs:
            ls.append(gate)
            gate.get_all_input_gates(ls)

        return ls

    def get_output_gates(self) -> list:
        return self.output_gates

    def update_line_colors(self) -> None:
        output_val = self.output()
        fill = get_line_fill(output_val)
        if is_output_gate(self):
            # If line colors are off, still color output gate
            if not InputTk.line_colors_on:
                fill = self.line_fill_true if output_val == TRUE else self.line_fill_false \
                    if output_val == FALSE else self.line_fill_null

            self.canvas.itemconfig(self.input_id, outline=fill)

        for i in range(len(self.output_line_ids)):
            self.canvas.itemconfig(self.output_line_ids[i], fill=fill)
            self.output_gates[i].update_line_colors()

    def add_rect(self) -> int:
        if self.rect_id < 0:
            self.rect_id = self.canvas.create_rectangle(self.top_left()[0] - self.border_offset,
                                                        self.top_left()[1] - self.border_offset,
                                                        self.bottom_right()[0] + self.border_offset,
                                                        self.bottom_right()[1] + self.border_offset,
                                                        width=self.border_width, outline='black')
        return self.rect_id

    def add_line(self, src_gate) -> int:
        if self.func == power:
            return -1

        src_pos, dest_pos = (src_gate.bottom_right()[0], src_gate.get_center()[1]), \
                            (self.top_left()[0], self.get_center()[1])

        self.add_input(src_gate)
        src_gate.add_output(self)
        src_out = src_gate.output()

        line_color = get_line_fill(src_out)

        line_id = self.canvas.create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4, fill=line_color)
        self.add_input_line(line_id)
        src_gate.add_output_line(line_id)

        self.update_line_colors()

        return line_id

    def add_input_line(self, line_id: int) -> None:
        self.input_line_ids.append(line_id)

    def add_output_line(self, line_id: int) -> None:
        self.output_line_ids.append(line_id)

    def remove_input(self, inp):
        contains, gate_index = list_contains(self.inputs, inp)
        if contains:
            self.inputs.remove(inp)
            self.remove_line(self.input_line_ids[gate_index])

    def num_inputs(self) -> int:
        return len(self.inputs)

    def num_outputs(self) -> int:
        return len(self.output_gates)

    def remove_output(self, destination):
        contains, gate_index = list_contains(self.output_gates, destination)
        if contains:
            self.output_gates.remove(destination)
            self.remove_line(self.output_line_ids[gate_index])

    def remove_connection(self, other, self_is_parent: bool) -> None:
        if self_is_parent:
            self.remove_output(other)
            other.remove_input(self)
            other.set_output(NULL)
        else:
            self.remove_input(other)
            other.remove_output(self)
            self.set_output(NULL)

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

    def delete(self) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)

        for input_gate in self.inputs:
            input_gate.remove_output(self)

        for output_gate in self.output_gates:
            output_gate.remove_input(self)
            output_gate.set_output(NULL)

        self.remove_all_lines()

        self.input_id = self.rect_id = -1

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

    def move(self, x: int, y: int) -> None:
        self.center = (x, y)
        # Move Gate Image and Border
        self.canvas.coords(self.rect_id, self.top_left()[0] - self.border_offset, self.top_left()[1] - self.border_offset,
                           self.bottom_right()[0] + self.border_offset, self.bottom_right()[1] + self.border_offset)

        if not is_output_gate(self):
            self.canvas.coords(self.input_id, x, y)
        else:
            self.canvas.coords(self.input_id, self.top_left()[0], self.top_left()[1],
                               self.bottom_right()[0], self.bottom_right()[1])
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

    def get_center(self) -> (int, int):
        return self.center

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def top_left(self) -> (int, int):
        return self.center[0] - self.get_width() // 2, self.center[1] - self.get_height() // 2

    def bottom_right(self) -> (int, int):
        return self.center[0] + self.get_width() // 2, self.center[1] + self.get_height() // 2

    def __str__(self) -> str:
        return "{0},{1},{2}".format(self.func.__name__, self.center, self.out)


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
        self.timer = threading.Timer(self.rate-(self.endTime-self.startTime), self.func, args=[self.gate])
        self.timer.start()

    def cancel(self) -> None:
        self.timer.cancel()
        self.startTime = self.endTime = 0
        self.started = False


class ClockTk(InputTk):
    """An alternating power source, which toggles after self.rate seconds have passed"""
    clocks_paused = True

    def __init__(self, gate_info_repo, update_rate: float, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), default_state: int = TRUE):
        # A clock has no inputs
        super().__init__(logic_clock, gate_info_repo, label, canvas, center, ins=None, out=default_state)
        self.timer = ClockTimer(logic_clock, update_rate, self)
        self.rate = update_rate
        self.default_state = default_state
        self.stop_event = threading.Event()
        self.first_run = True

    def toggle(self) -> int:
        self.set_output(not self.out)
        return self.out

    def delete(self):
        self.stop()
        InputTk.delete(self)

    def start(self):
        if not self.timer.started:
            self.timer.start()
        else:
            self.timer.resume()

    def stop(self):
        self.timer.cancel()
        self.set_output(self.default_state)

    def pause(self):
        self.timer.pause()

    def set_default_state(self, state: int):
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


def is_output_gate(gate: InputTk) -> bool:
    return gate.get_func() == output


def is_power_gate(gate: InputTk) -> bool:
    return gate.get_func() == power


def is_and_gate(gate: InputTk) -> bool:
    return gate.get_func() == logic_and


def is_nand_gate(gate: InputTk) -> bool:
    return gate.get_func() == logic_nand


def is_or_gate(gate: InputTk) -> bool:
    return gate.get_func() == logic_or


def is_xor_gat(gate: InputTk) -> bool:
    return gate.get_func() == logic_xor


def is_not_gate(gate: InputTk) -> bool:
    return gate.get_func() == logic_not


def is_clock(gate: InputTk) -> bool:
    # return gate.get_func() == logic_clock
    return isinstance(gate, ClockTk)


def gate_id(gate: InputTk) -> int:
    return gate.get_id()


def connect_gates(src_gate: InputTk, dest_gate: InputTk) -> None:
    # Only allow one input to a not gate
    # Clocks/Power sources can only be outputs, so return if one is set as a destination gate
    if (is_not_gate(dest_gate) and len(dest_gate.get_input_gates()) == 1) or \
       (is_output_gate(dest_gate) and len(dest_gate.get_input_gates()) == 1) or is_output_gate(src_gate)\
            or is_clock(dest_gate):
        return

    if not is_parent(dest_gate, src_gate) and dest_gate not in src_gate.get_output_gates():
        dest_gate.add_line(src_gate)


def connection_exists(gate1: InputTk, gate2: InputTk) -> bool:
    return list_contains(gate1.get_input_gates(), gate2)[0] or list_contains(gate1.get_output_gates(), gate2)[0]


def is_parent(parent: InputTk, child: InputTk) -> bool:
    return list_contains(child.get_all_input_gates([]), parent)[0]


class GateInfo:
    def __init__(self, func: Callable, name: Optional[str] = None, desc: str = "", image_file: Optional[str] = None,
                 callback: Optional[Callable] = None):
        self.info = {
            "func": func,
            "name": name if name is not None else func.__name__,
            "desc": desc if desc is not None else "",
            "callback": callback,
            "image_file": image_file if image_file is not None else ""
        }
        self.active_gates = []

    def add_active_gate(self, gate: InputTk) -> None:
        self.active_gates.append(gate)

    def get_active_gates(self) -> list[InputTk]:
        return self.active_gates

    def remove(self, gate: InputTk) -> None:
        if gate in self.active_gates:
            self.active_gates.remove(gate)

    def keys(self):
        return self.info.keys()

    def __getitem__(self, item: str) -> Union[str | Callable]:
        return self.info[item]

    def __setitem__(self, key: str, value: Union[str | Callable]) -> None:
        self.info[key] = value


class GatesInfoRepo:
    def __init__(self):
        self.gate_infos = {}
        self.funcs_dispatch = {}

    def register_gate(self, func: Callable, **kwargs) -> None:
        self.gate_infos[func] = GateInfo(func, **kwargs)
        self.funcs_dispatch[func.__name__] = func

    def add_gate(self, gate: InputTk):
        if gate.get_func() in self.gate_infos.keys():
            self.gate_infos[gate.get_func()].add_active_gate(gate)
        else:
            self.register_gate(gate.get_func(), name=None, desc=None, callback=None)
            self.gate_infos[gate.get_func()].add_active_gate(gate)

    def get_gates(self, func: Callable) -> Optional[list[InputTk]]:
        if func in self.gate_infos.keys():
            return self.gate_infos[func].get_active_gates()
        return None

    def keys(self):
        return self.gate_infos.keys()

    def __getitem__(self, item: Union[Callable | str]) -> Union[GateInfo | Callable]:
        if isinstance(item, Callable):
            return self.gate_infos[item]
        elif isinstance(item, str):
            return self.funcs_dispatch[item]

    def __setitem__(self, key: Callable, value: GateInfo) -> None:
        self.gate_infos[key] = value

    def __len__(self):
        return len(self.keys())

########################################################################################################################
# File: Circuit.py
# Author: Peter McCusker
# License:
# Date: 01/04/2023
# Description:
########################################################################################################################
# TODO:
#   - Scrolling for canvas
#   - Zoom In/Out
#   - Save/Load
#
########################################################################################################################
import tkinter
from tkinter import *
from tkinter import scrolledtext
from tkinter import filedialog as fd
import tkinter.font as font
import tkinter.ttk as ttk
import sys, threading, os
from time import time
from typing import *

NULL = -1  # Value which represents a gate which has not received a valid input yet
TRUE = int(True)
FALSE = int(False)


def list_contains(ls: list[Any], val: Any) -> (bool, int):
    for i in range(len(ls)):
        if ls[i] == val:
            return True, i
    return False, -1


def logic_output(value: list[int]) -> int:
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
    if not gate.get_event().is_set() and not Application.clocks_paused:  # Might be broke
        # call f() again in 60 seconds
        threading.Timer(gate.get_rate(), logic_clock, [gate]).start()
        gate.toggle()

    return gate.output()


def get_logic_func_from_name(name: str):
    if name == "power":
        return power
    elif name == "logic_output":
        return logic_output
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


# Global counter for each input object, gives each object a unique id
IMG_FOLDER = "images"
INPUT_GATES = [logic_output, power, logic_not, logic_and, logic_nand, logic_or, logic_xor, logic_clock]


def get_input_img_file(func) -> str:
    global IMG_FOLDER
    img_name = ""
    if func == logic_output:
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


def get_input_img(func, output: Optional[list[PhotoImage]] = None) -> Optional[PhotoImage]:
    if output is not None:
        output.append(PhotoImage(file=get_input_img_file(func)))
        return None

    return PhotoImage(file=get_input_img_file(func))


def get_all_input_imgs(output: Optional[list[PhotoImage]] = None) -> Optional[list[PhotoImage]]:
    if output is not None:
        for input_src in INPUT_GATES:
            get_input_img(input_src, output)
        return None

    return [get_input_img(input_src) for input_src in INPUT_GATES]


class Input:
    """Class to test basic gate functionality"""
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
    if value == NULL:
        return Application.line_fill_null
    elif value == TRUE:
        return Application.line_fill_true
    else:
        return Application.line_fill_false


class InputTk:
    def __init__(self, func, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), ins: Optional[list] = None,
                 out: int = NULL, dims: (int, int) = (0, 0)):
        self.func = func
        self.label = label  # Gate Name
        self.inputs = ins if ins is not None else []
        self.out = out
        self.output_gates = []
        self.img = get_input_img(func)
        self.img_path = get_input_img_file(func)
        self.center = center
        self.border_width = 1
        self.border_offset = self.border_width + 5 if is_output_gate(self) else self.border_width
        self.canvas = canvas
        self.rect_id = NULL
        self.input_line_ids = []
        self.output_line_ids = []
        self.width, self.height = dims[0], dims[1]
        if func != logic_output:
            self.input_id = self.canvas.create_image(self.center[0], self.center[1], image=self.img) \
                if center != (NULL, NULL) else NULL
        else:
            self.input_id = self.canvas.create_rectangle(self.top_left()[0],
                                                         self.top_left()[1],
                                                         self.bottom_right()[0],
                                                         self.bottom_right()[1],
                                                         width=2, outline='black', )

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

    def update_line_colors(self):
        fill = get_line_fill(self.output())
        if is_output_gate(self):
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

    def image_path(self) -> str:
        return self.img_path

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
    def __init__(self, update_rate: float, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), default_state: int = TRUE):
        super().__init__(logic_clock, label, canvas, center, ins=None, out=default_state)  # A clock has not inputs
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
    return gate.get_func() == logic_output


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


def point_in_rect(x, y, tl: (int, int), br: (int, int)):
    return (tl[0] <= x <= br[0]) and (tl[1] <= y <= br[1])


# Returns true if two rectangles (l1, r1) and (l2, r2) overlap
def do_overlap(l1: (int, int), r1: (int, int), l2: (int, int), r2: (int, int)) -> bool:
    # if any rectangle has area 0, no overlap
    if l1[0] == r1[0] or l1[1] == r1[1] or r2[0] == l2[0] or l2[1] == r2[1]:
        return False

    # If one rectangle is on left side of other
    if l1[0] > r2[0] or l2[0] > r1[0]:
        return False
    # If one rectangle is above other
    if r1[1] < l2[1] or r2[1] < l1[1]:
        return False

    return True


class TableCheckbutton(Frame):
    def __init__(self, parent: Optional[Widget], gate, return_focus_to: Widget, *args,
                 checkbutton_padding: Optional[dict] = None,
                 **kwargs):  # Maybe add padding option for label
        super().__init__(parent, *args, bg="white", **kwargs)
        self.gate = gate
        self.return_focus_to = return_focus_to
        if gate is not None:
            self.check_var = IntVar(value=gate.output())
            # self.check_var.set(1)  # Default the checkbox to on
            self.checkbutton = Checkbutton(self, variable=self.check_var, text=self.gate.get_label(),
                                           onvalue=TRUE, offvalue=FALSE, width=10, command=self.click_cb,
                                           font="Helvetica 10")
            if checkbutton_padding is not None:
                self.checkbutton.grid(row=0, column=0, **checkbutton_padding)
            else:
                self.checkbutton.grid(row=0, column=0)
        else:
            self.checkbutton = Label(self.master)
            self.grid()
            self.check_var = None

    def click_cb(self):
        self.return_focus_to.focus_force()
        self.gate.set_output(self.check_var.get())

    def update_text(self, text: str) -> None:
        self.gate.set_label(text)
        self.checkbutton.config(text=self.gate.get_label())

    def get(self) -> int:
        return self.check_var.get()


class CheckbuttonTable(LabelFrame):
    def __init__(self, parent, title: str, return_focus_to: Widget, *args,  **kwargs):
        super().__init__(parent, *args, text=title, font="Helvetica 10", **kwargs)
        self.checkbox_padding = {"padx": (20, 5), "pady": (5, 5)}
        self.return_focus_to = return_focus_to
        self.entries = []  # List holding list of TableCheckbutton

        self.empty_text_label = Label(self, bg="white", text="You have no inputs...", font="Helvetica 11")
        self.empty_text_label.grid()
        self.null = True

    def add_entry(self, gate) -> None:
        if self.null:
            self.empty_text_label.grid_forget()
            self.null = False
        tbl_entry = TableCheckbutton(self, gate, self.return_focus_to, checkbutton_padding=self.checkbox_padding)
        tbl_entry.grid(row=len(self.entries), sticky='w')
        self.entries.append(tbl_entry)

    def del_entry(self, row: int) -> None:
        if abs(row) > len(self.entries):
            return
        entry = self.entries[row]
        entry.grid_forget()
        entry.destroy()
        self.entries.remove(entry)

        # Subtract one from each checkbutton label number
        for i in range(len(self.entries)):
            stripped_label = self.entries[i].gate.get_label()[:-1]
            self.entries[i].update_text(stripped_label + str(i+1))

        if len(self.entries) == 0:
            self.empty_text_label.grid()
            self.null = True

    def get_row(self, row: int) -> Optional[int]:
        if abs(row) > len(self.entries):
            return None
        return self.entries[row].get()

    def del_gate_entry(self, gate: InputTk) -> None:
        for i in range(len(self.entries)):
            if self.entries[i].gate == gate:
                self.del_entry(i)
                return

    def clear(self) -> None:
        for entry in self.entries:
            print(entry)
            entry.grid_forget()
            entry.destroy()

        self.entries.clear()

        self.empty_text_label.grid()
        self.null = True


class LabeledEntry(Frame):
    def __init__(self, *arg, label_text: str = "", entry_text: str = "", entry_var: Optional[StringVar] = None,
                 widget_font: Optional[str | font.Font] = None, **kwargs):
        Frame.__init__(self, *arg, **kwargs)
        self.label = Label(self, text=label_text) if widget_font is None else Label(self, text=label_text,
                                                                                    font=widget_font)
        self.label.grid(row=0, column=0)
        self.entry_var = StringVar(value=entry_text) if entry_var is None else entry_var
        self.entry = Entry(self, textvariable=self.entry_var) if widget_font is None else \
                     Entry(self, textvariable=self.entry_var, font=widget_font)
        self.entry.grid(row=0, column=1)

    def set_label(self, text: str) -> None:
        self.label.config(text=text)

    def set_label_padding(self, **kwargs) -> None:
        self.label.grid(**kwargs)

    def set_entry_padding(self, **kwargs) -> None:
        self.entry.grid(**kwargs)

    def get(self) -> str:
        return self.entry_var.get()


class BorderedSideFrame(Frame):
    def __init__(self, side: str, border_width: int, border_fill: str = "black", inner_color: str = "white", *args, **kwargs):
        Frame.__init__(self, *args, background=border_fill, **kwargs)
        self.inner_frame = None
        self.propagate(False)  # prevent frame from auto-fitting to contents
        side = side.lower()
        if side in ['left', 'right']:
            # self.border_frame = Frame(self, background=border_fill, width=border_width, height=self.winfo_height())
            self.inner_frame = Frame(self, background=inner_color, width=self.winfo_width() - border_width, height=self.winfo_height())
            if side == 'left':
                # self.border_frame.grid(row=0, column=0)
                self.inner_frame.grid(padx=(border_width, 0))
            else:
                # self.border_frame.grid(row=0, column=1)
                self.inner_frame.grid(padx=(border_width, 0))
        elif side in ['up', 'down']:
            # self.border_frame = Frame(self, background=border_fill, width=self.winfo_reqwidth(), height=border_width)
            self.inner_frame = Frame(self, background=inner_color, width=self.winfo_reqwidth(), height=self.winfo_reqheight() - border_width)
            if side == 'up':
                # self.border_frame.grid(row=0, column=0)
                self.inner_frame.grid(pady=(border_width, 0))
            else:
                # self.border_frame.grid(row=1, column=0)
                self.inner_frame.grid(pady=(0, border_width))


class Application(Tk):
    img_width = 100
    img_height = 50
    line_fill_true = "green"
    line_fill_false = "red"
    line_fill_null = "black"
    max_selectable_gates = 100
    clocks_paused = True
    border_width = 3
    input_selection_screen_width = 150 + border_width  # Width of the frame
    bg_colors = ["white", "black", "red", "green", "blue", "cyan", "yellow", "magenta"]

    def __init__(self, width: int = 1600, height: int = 900):
        super().__init__()
        # Parse command line arguments
        for i, arg in enumerate(sys.argv):
            if arg == '-w':
                try:
                    width = int(sys.argv[i+1])
                except ValueError:
                    print(sys.argv[i+1], ": width must be an integer")
                    sys.exit(-1)
            if arg == '-h':
                try:
                    height = int(sys.argv[i + 1])
                except ValueError:
                    print(sys.argv[i + 1], ": height must be an integer")
                    sys.exit(-1)

        self.width = width - self.input_selection_screen_width
        self.height = height
        self.x = self.width / 2
        self.y = self.height / 2
        self.background_color = StringVar(value="white")
        # self.iconphoto = PhotoImage(file="circuit_icon.svg")

        self.title("Interactive Circuit Builder")
        self.geometry(str(self.width) + "x" + str(self.height))
        self.resizable(False, False)
        self.config(background=self.background_color.get())

        # List to hold references to the Photoimages of the input gates so that Tkinter doesn't garbage collect
        # prematurely
        self.imgs = get_all_input_imgs()
        self.default_update_rate = 2  # Default Update for a new clock in seconds, default to 2s
        self.update_lines = False  # Set to true when a new gate/power source is added/changed to redraw lines

        # Dictionary to hold the input gates, where the gate type is the key and the value is the list of gates
        self.inputs = {}
        for func in INPUT_GATES:
            self.inputs[func] = []

        self.active_input = None  # The input object to be placed when the user clicks the mouse
        self.active_input_pi = None  # Photoimage for active gate
        self.active_input_img_index = 0  # Canvas image index of active gate
        # Fonts #####################
        self.font_family = "Helvetica"
        self.default_font_size = 10
        self.default_font = font.Font(family=self.font_family, weight=tkinter.font.NORMAL, slant=tkinter.font.ROMAN)
        self.font_top = font.Font(family=self.font_family, size=11, weight=tkinter.font.NORMAL,slant=tkinter.font.ROMAN)
        self.font_prompt = self.default_font
        #############################
        # ICB Widgets ###############
        self.screen_icb = None  # Canvas gates are placed on
        self.icb_menubar = None  # Top Menu (File, Edit, Help...)
        self.icb_is_gate_active = False  # If True, shows input gate as cursor is dragged around
        self.icb_selected_gates = []  # Holds references to all currently selected gates when performing operations
        self.icb_click_drag_gate = None  # The gate currently being moved by the mouse
        self.icb_play_pause_button = None  # Button which starts and stops
        self.icb_play_pause_pi = None  # Photoimage for play/pause button
        #############################
        # Prompt Widgets ############
        self.screen_prompt = None  # Toplevel popup window for prompt
        self.prompt_label = None  # Label to display prompt message
        self.prompt_button_confirm = None  # Confirmation button
        self.prompt_button_cancel = None  # Cancellation button
        #############################
        # Input Selection Widgets ###
        self.screen_is = None  # Separate Window to select which gate input to place
        self.screen_is_height = self.height  # The window is as tall as the window
        self.is_button_frame = None  # Frame a button is placed on
        self.is_border_frame = None  # Border frame for a button
        self.is_button = None  # Stores reference to a button so Tk doesn't GC it prematurely
        self.is_buttons = []  # Holds tuple: the buttons for each input gate and its border frame
        self.is_edit_table = None  # Table to toggle inputs on/off
        #############################
        #############################
        # Timer Window Widgets ######
        self.timer_popup = None  # Toplevel popup window for window
        self.timer_labelframe = None  # Label Frame for popup
        self.timer_title_label = None  # Label to give instructions to user
        self.selected_timer = None  # The timer that is currently being modified
        self.timer_state_label = None  # Text label for checkbox, use instead of checkbox text to put left of checkbox
        self.timer_state_cb = None  # Checkbox to toggle the timer's default state
        self.timer_state_intvar = IntVar(value=TRUE)  # Value of the default state checkbox
        self.timer_entry_label = None  # Label next to timer entry
        self.timer_entry = None  # Entry for timer toggle rate
        self.timer_entry_strvar = StringVar(value=str(self.default_update_rate))  # Value of the timer update rate
        self.timer_done_button = None  # Button to close window
        #############################
        # Saving/Loading Vars #######
        self.filename = ""
        self.file_separator = "<--CONNECTIONS-->"
        self.file_type = ".cir"
        #############################
        # Preference Vars ###########
        self.font_families = list(font.families())

        #############################

    def input_gates_intersect(self, event: Event) -> (bool, Optional[InputTk]):
        """Checks if a new gate would intersect an existing gate if it was placed at (event.x, event.y) on the canvas,
         if they do, return true and the intersecting gate, otherwise return False, None"""
        img1_center_x, img1_center_y = event.x, event.y
        center_x_offset, center_y_offset = (Application.img_width / 2), (Application.img_height / 2)
        # Get Top-Left Coordinates of gate to be placed
        img1_tl_x, img1_tl_y = int(img1_center_x - center_x_offset), int(img1_center_y - center_y_offset)
        # Get Bottom-Right Coordinates of gate to be placed
        img1_br_x, img1_br_y = int(img1_center_x + center_x_offset), int(img1_center_y + center_y_offset)
        # Loop through all placed input gates to check if the new gate intersects with any placed gate
        for func in self.inputs.keys():
            for i in range(len(self.inputs[func])):
                item = self.inputs[func][i]
                if do_overlap((img1_tl_x, img1_tl_y), (img1_br_x, img1_br_y),
                              item.top_left(), item.bottom_right()):
                    return True, item
        return False, None

    def intersects_input_gate(self, event: Event) -> (bool, list[InputTk]):
        """Checks if the coordinate (event.x, event.y) intersects any existing gate(s) on canvas,
        if so, return true and the list of all gates which were intersected (in the case of overlapping gates),
        otherwise return False, []"""
        intersected_gates = []
        intersects = False
        for func in self.inputs.keys():
            for item in self.inputs[func]:
                if point_in_rect(event.x, event.y, item.top_left(), item.bottom_right()):  # If event is withing gate...
                    intersects = True
                    intersected_gates.append(item)

        return intersects, intersected_gates

    def deselect_active_gates(self) -> None:
        """Removes border around gates and clear selected gates"""
        for gate in self.icb_selected_gates:
            gate.remove_rect()
        self.icb_selected_gates.clear()
        self.icb_click_drag_gate = None

    def left_click_cb(self, event: Event) -> None:
        """If user selected a gate button, place the gate on the canvas, otherwise (de)select the gate"""
        if 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            if self.icb_is_gate_active:  # If user pressed a gate button...
                self.place_gate(event)
            else:
                self.deselect_active_gates()
                intersect, gates = self.intersects_input_gate(event)
                if intersect:  # If mouse click intersects any gate(s) select the first one
                    self.icb_selected_gates.append(gates[0])
                    self.icb_selected_gates[0].add_rect()

    def lclick_and_drag_cb(self, event: Event) -> None:
        """Moves a gate around on the canvas while the left mouse button is clicked and held"""
        if self.icb_is_gate_active or len(self.icb_selected_gates) != 1:  # If user selected a gate button, then leave
            return

        if self.icb_click_drag_gate is not None:  # if a gate is currently being drug around, keep using it
            self.icb_click_drag_gate.move(event.x, event.y)
            return

        intersects, gates = self.intersects_input_gate(event)
        if not intersects:
            return

        first_gate = gates[0]
        self.deselect_active_gates()
        if point_in_rect(event.x, event.y, first_gate.top_left(), first_gate.bottom_right()):
            self.icb_click_drag_gate = first_gate
            self.icb_click_drag_gate.add_rect()
            self.icb_selected_gates.append(first_gate)
            self.icb_click_drag_gate.move(event.x, event.y)

    def right_click_cb(self, event: Event) -> None:
        """Clears a gate button press if present.  If not, select two gates and connect them"""
        if 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            if self.icb_is_gate_active:  # Right-clicking clears the gate that a user selects with a button
                self.set_active_fn_none()
                self.deselect_active_gates()
                return

            intersects, gates = self.intersects_input_gate(event)
            if not intersects:
                return

            first_gate = gates[0]

            if len(self.icb_selected_gates) == 0:
                first_gate.add_rect()
                self.icb_selected_gates.append(first_gate)
            elif len(self.icb_selected_gates) == 1 and self.icb_selected_gates[0] != first_gate:
                # Gate is already selected and the second gate is different from the first
                connect_gates(self.icb_selected_gates[0], first_gate)
                self.deselect_active_gates()
            elif len(self.icb_selected_gates) == 1 and self.icb_selected_gates[0] == first_gate:
                # Gate is already selected and the second gate is the same as the first
                if is_clock(first_gate):
                    self.selected_timer = first_gate
                    self.timer_prompt()
                    self.deselect_active_gates()
            else:
                self.deselect_active_gates()

    def multi_select_cb(self, event: Event) -> None:
        """Selects multiple gates to be deleted"""
        if self.icb_is_gate_active:
            return

        intersects, gates = self.intersects_input_gate(event)
        print(intersects, gates)
        if not intersects:
            return

        first_gate = gates[0]
        if len(self.icb_selected_gates) < self.max_selectable_gates:
            first_gate.add_rect()
            self.icb_selected_gates.append(first_gate)
        else:  # Deselect first gate and add select this new gate
            self.icb_selected_gates[0].remove_rect()
            self.icb_selected_gates = self.icb_selected_gates[1:]
            self.icb_selected_gates.append(first_gate)

    def motion_cb(self, event: Event) -> None:
        """Move the image of the selected gate with the mouse"""
        if self.icb_is_gate_active and 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            self.active_input_pi = PhotoImage(file=self.active_input.image_path())
            self.active_input_img_index = self.screen_icb.create_image(event.x, event.y, image=self.active_input_pi)
            self.active_input.set_id(self.active_input_img_index)

    def delete_cb(self, event: Event) -> None:
        """Delete all selected gates from the canvas"""
        for i in range(len(self.icb_selected_gates)):
            gate = self.icb_selected_gates[i]
            self.inputs[gate.get_func()].remove(gate)
            if is_power_gate(gate):  # Remove entries from the power table
                self.is_edit_table.del_gate_entry(gate)
            gate.delete()

        self.deselect_active_gates()

    def remove_connection_cb(self, event: Event) -> None:
        """Removed the connection between 2 gates"""
        if not self.icb_is_gate_active:
            # self.select_gate_under_cursor(event, selectable_gates=2)
            if len(self.icb_selected_gates) == 2 and self.icb_selected_gates[0] != self.icb_selected_gates[1]:
                g1 = self.icb_selected_gates[0]
                g2 = self.icb_selected_gates[1]
                g1.remove_connection(g2, self_is_parent=is_parent(g1, g2))
                # self.icb_selected_gates[1].remove_connection(self.icb_selected_gates[0])
                self.deselect_active_gates()
            else:
                print("You can only disconnect two gates!")

    def place_gate(self, event: Event) -> None:
        """Places a gate on the canvas after pressing a gate button"""
        if self.icb_is_gate_active and 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            if self.input_gates_intersect(event)[0]:
                return

            self.active_input_pi = PhotoImage(file=self.active_input.image_path())
            inst_num = len(self.inputs[self.active_input.get_func()]) + 1

            if is_clock(self.active_input):
                self.inputs[self.active_input.get_func()].append(ClockTk(update_rate=self.default_update_rate,
                                                                         label=self.active_input.get_label() + str(inst_num),
                                                                         canvas=self.screen_icb,
                                                                         center=(event.x, event.y)))
                self.selected_timer = self.inputs[self.active_input.get_func()][-1]
                print(self.selected_timer.get_label())
                self.timer_prompt()  # Configure this new timer on placement
            elif isinstance(self.active_input, InputTk):
                self.inputs[self.active_input.func].append(InputTk(self.active_input.get_func(),
                                                                   label=self.active_input.get_label() + str(inst_num),
                                                                   canvas=self.screen_icb, center=(event.x, event.y),
                                                                   out=self.active_input.out,
                                                                   # If output gate, make it smaller to fit with border
                                                                   dims=(self.img_width - 5, self.img_height - 5) if is_output_gate(self.active_input)
                                                                   else (0, 0)))
            last_input = self.inputs[self.active_input.func][-1]
            self.active_input_img_index = last_input.get_id()
            # Add checkbox entry to entry menu if gate is a power source
            if is_power_gate(last_input):
                self.is_edit_table.add_entry(last_input)

    def save(self) -> None:
        """Save the current circuit to a file, if this is the first save, prompt for file name"""
        if self.filename == "":
            print("No save file has been specified")
            self.save_as()

        save_file = open(self.filename, 'w')
        if save_file is None:
            raise OSError("Failed to open: " + self.filename)

        self.deselect_active_gates()
        self.reset()
        gates = []

        for func in self.inputs.keys():  # Create one list out of all gates
            for gate in self.inputs[func]:
                gates.append(gate)

        for idx, gate in enumerate(gates):  # For each gate, write the gate and its enumeration,which is used as its id
            print("{0},{1}".format(gate, int(idx)), file=save_file)
            gates[idx] = (gate, idx)

        print(self.file_separator, file=save_file)  # Add seperator between the gates and their connections

        # Write connections to file
        # Get the input and output gates for each gate, convert each gate to its id and write to file
        for (gate, cnt) in gates:
            in_gates = gate.get_input_gates()
            out_gates = gate.get_output_gates()

            # Get the id of each input gate, store in list
            # Strip spaces from input and output gate lists to simplify reading
            in_fmt = "[" if len(in_gates) > 0 else "[]"
            for in_gate in in_gates:
                for other_gate in gates:
                    if other_gate[0] == in_gate:
                        # print(other_gate[1])
                        in_fmt += str(other_gate[1]) + "|"
                        break
            in_fmt = in_fmt[:-1] + ']'

            # For every output, find the gate in the master list and add its id number to the list, to reconstruct later
            out_fmt = "[" if len(out_gates) > 0 else "[]"
            for out_gate in out_gates:
                for other_gate in gates:
                    if other_gate[0] == out_gate:
                        out_fmt += str(other_gate[1]) + "|"
                        break
            out_fmt = out_fmt[:-1] + ']'

            print('{0},{1},{2}'.format(cnt, in_fmt, out_fmt), file=save_file)

        save_file.close()

    def save_as(self):
        """Create save file prompt and set self.filename to this file"""
        # using with statement
        self.filename = fd.asksaveasfilename(initialfile=self.filename,
                                             filetypes=[("Circuit Diagram", "*" + self.file_type)])

    def open(self):
        """"Load circuit from file"""
        self.filename = fd.askopenfilename(filetypes=[("Circuit Diagram", "*" + self.file_type)])
        if self.filename == "":
            return

        load_file = open(self.filename, 'r')
        if load_file is None:
            raise FileNotFoundError("Unable to open: " + self.filename)

        self.clear()

        # Get list of lines in file, then parse each line
        file_lines = load_file.readlines()
        connection_start_index = -1
        gates = []
        for idx, line in enumerate(file_lines):  # Load every gate into the canvas
            if line.strip() == self.file_separator:
                connection_start_index = idx + 1
                break

            line_list = line.strip('\n').split(sep=',')
            # line_list[0]: Function Name
            # line_list[1]: Center X of Gate on canvas
            # line_list[2]: Center Y of Gate on canvas
            # line_list[3]: Gate Output
            # line_list[-1]: Gate Num
            gate_func = get_logic_func_from_name(line_list[0])
            # Strip parenthesis and space from center str, then split
            gate_inst = len(self.inputs[gate_func]) + 1
            position_x = int(line_list[1].strip("("))
            position_y = int(line_list[2].strip(") "))
            gate_out = int(line_list[3])
            gate_center = (position_x, position_y)
            gate = None
            if gate_func == logic_clock:  # If this input is clock, it has a different format
                # line_list[3]: Default Value
                # line_list[4]: Update Rate
                # line_list[5]: gate number
                gate = ClockTk(update_rate=float(line_list[4]), label="Clock #" + str(gate_inst),
                               canvas=self.screen_icb, center=gate_center, default_state=int(line_list[5]))
            else:  # Otherwise all the other gates have the same format
                gate = InputTk(func=gate_func, label=gate_func.__name__ + " #" + str(gate_inst), canvas=self.screen_icb,
                               center=gate_center, out=gate_out, dims=(95, 45) if gate_func == logic_output else (0, 0))
                if is_power_gate(gate):
                    self.is_edit_table.add_entry(gate)
                    gate.set_label("Power #" + str(gate_inst))
            gates.append((gate, idx))
            self.inputs[gate_func].append(gate)

        # Strip input gate section from file to work with connections
        file_lines = file_lines[connection_start_index:]
        for connection_line in file_lines:
            connection_line = connection_line.strip()
            line_list = connection_line.split(sep=',')
            # line_list[0]: gate id
            # line_list[1]: gate input ids
            # line_list[2]: gate output ids
            curr_gate_id = int(line_list[0])
            current_gate = None
            for (gate, num) in gates:
                if num == curr_gate_id:
                    current_gate = gate
                    break

            # Read gate inputs
            # Find input gates based on gate num
            inputs_id_list = [int(input_gate_num) for input_gate_num in line_list[1][1:-1].split('|')] \
                if len(line_list[1]) != 2 else []

            outputs_id_list = [int(output_gate_num) for output_gate_num in line_list[2][1:-1].split('|')] \
                if len(line_list[2]) != 2 else []

            # Get list of input and output gates using gate ids
            for input_id in inputs_id_list:
                for (gate, num) in gates:
                    if num == input_id:
                        connect_gates(gate, current_gate)
                        break

            for output_id in outputs_id_list:
                for (gate, num) in gates:
                    if num == output_id:
                        connect_gates(current_gate, gate)
                        break

    def clear(self):
        """Clear the canvas, clear all entries from the power table, and delete all gates"""
        self.deselect_active_gates()
        self.reset()
        self.is_edit_table.clear()
        print(self.is_edit_table.entries)

        # Destroy Gates
        for func in self.inputs.keys():
            for gate in self.inputs[func]:
                gate.delete()
            self.inputs[func] = []

        # Reset all reference to gates
        self.icb_is_gate_active = False
        self.set_active_fn_none()
        # Clear Canvas
        self.screen_icb.delete('all')

    def about(self):
        pass

    def help(self):
        pass

    def pause(self, event: Event):
        """Pauses all clocks"""
        print("pause")
        Application.clocks_paused = True
        for clock in self.inputs[logic_clock]:
            clock.pause()

    def play(self, event: Optional[Event] = None):
        """Starts all clocks"""
        print("play")
        Application.clocks_paused = False
        for clock in self.inputs[logic_clock]:
            clock.start()

    def reset(self, event: Optional[Event] = None):
        """Resets the clocks in the program"""
        Application.clocks_paused = True
        for clock in self.inputs[logic_clock]:
            clock.stop()

    def toggle_play_pause(self, event: Optional[Event] = None):
        """Toggle the clocks"""
        if not Application.clocks_paused:
            """Pauses all timers"""
            Application.clocks_paused = True
            for clock in self.inputs[logic_clock]:
                clock.pause()
        else:
            """Starts all timers"""
            Application.clocks_paused = False
            for clock in self.inputs[logic_clock]:
                clock.start()

    def set_active_fn_none(self) -> None:
        """Set when a gate button is clear"""
        self.deselect_active_gates()
        self.icb_is_gate_active = False
        self.screen_icb.delete(self.active_input_img_index)

    def set_active_fn_output(self) -> None:
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_output, label="Output #", canvas=self.screen_icb, out=TRUE)

    def set_active_fn_power(self) -> None:
        self.icb_is_gate_active = True
        self.active_input = InputTk(power, label="Power #", canvas=self.screen_icb, out=TRUE)

    def set_active_fn_and(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_and, label="And Gate #", canvas=self.screen_icb)

    def set_active_fn_nand(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_nand, label="Nand Gate #", canvas=self.screen_icb)

    def set_active_fn_xor(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_xor, label="Xor Gate #", canvas=self.screen_icb)

    def set_active_fn_not(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_not, label="Not Gate #", canvas=self.screen_icb)

    def set_active_fn_or(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_or, label="Or Gate #", canvas=self.screen_icb)

    def set_active_fn_clock(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = ClockTk(self.default_update_rate, label="Clock #", canvas=self.screen_icb)

    def gui_build_icb(self) -> None:
        """Builds the canvas for the gates to exist on and create all the key bindings"""
        self.screen_icb = Canvas(self, width=self.width, height=self.height, bg='white', highlightthickness=0)
        self.screen_icb.grid(row=0, column=0, sticky="NESW")
        self.screen_icb.bind('<Motion>', self.motion_cb)
        self.screen_icb.bind('<Button-1>', self.left_click_cb)
        self.screen_icb.bind('<B1-Motion>', self.lclick_and_drag_cb)
        self.screen_icb.bind('<Button-3>', self.right_click_cb)
        self.screen_icb.bind('<Button-4>', self.delete_cb)
        self.screen_icb.bind('<KeyRelease-BackSpace>', self.delete_cb)
        self.screen_icb.bind('<Control-Button-1>', self.multi_select_cb)
        self.screen_icb.bind('<c>', self.remove_connection_cb)
        self.screen_icb.bind('<r>', self.reset)
        self.screen_icb.bind('<F3>', self.reset)
        self.screen_icb.bind('<p>', self.play)
        self.screen_icb.bind('<F1>', self.play)
        self.screen_icb.bind('<P>', self.pause)
        self.screen_icb.bind('<F2>', self.pause)
        self.screen_icb.bind('<space>', self.toggle_play_pause)
        # Force the canvas to stay focused, keybindings only take effect when this widget is active
        self.screen_icb.focus_force()

    def gui_build_input_selection_menu(self) -> None:
        """Build the side pane: the power table and gate buttons"""
        self.geometry(str(self.width + self.input_selection_screen_width) + "x" + str(self.height))
        self.border_width = 3
        self.screen_is = BorderedSideFrame(master=self, side='left', border_width=self.border_width, border_fill='black',
                                           width=self.input_selection_screen_width, height=self.screen_is_height)
        self.screen_is.grid(row=0, column=1, sticky="nse", padx=(self.border_width, 0))

        # Add table to this side pane
        table_padding = {"padx": (0, 5), "pady": (5, 5)}
        self.is_edit_table = CheckbuttonTable(self.screen_is.inner_frame, "Edit Inputs", self.screen_icb,
                                              background="white",
                                              width=self.input_selection_screen_width - self.border_width,
                                              height=self.height / 3)
        # self.is_edit_table.grid_propagate(False)
        self.is_edit_table.grid(row=0, column=0, sticky="ns", **table_padding)

        # Build the button layouts
        self.is_button_frame = Frame(self.screen_is.inner_frame, bg="white",
                                     width=self.input_selection_screen_width - self.border_width,
                                     height=self.height)
        self.is_button_frame.grid_propagate(False)
        self.is_button_frame.grid(row=1, column=0, sticky='nesw', padx=(self.border_width, 0))
        logic_funcs_cbs = [self.set_active_fn_output, self.set_active_fn_power, self.set_active_fn_not,
                           self.set_active_fn_and, self.set_active_fn_nand, self.set_active_fn_or,
                           self.set_active_fn_xor, self.set_active_fn_clock]

        for i in range(len(INPUT_GATES)):
            image = PhotoImage(file=get_input_img_file(INPUT_GATES[i]))
            self.imgs[i] = image
            self.is_border_frame = Frame(self.is_button_frame, highlightbackground="black",
                                         highlightthickness=1, bd=0)
            # self.is_border_frame.propagate(False)
            self.is_border_frame.grid(row=i, column=0, sticky="ns", padx=(15, 0))

            self.is_button = Button(self.is_border_frame, image=self.imgs[i], bg="white", relief="flat",
                                    command=logic_funcs_cbs[i])
            self.is_button.grid(sticky='ns')

            self.is_buttons.append((self.is_button, self.is_border_frame))

    def gui_build_top_menu(self) -> None:
        """Build the top menu bar"""
        self.icb_menubar = Menu(self)
        file_menu = Menu(self.icb_menubar, tearoff=0)
        edit_menu = Menu(self.icb_menubar, tearoff=0)
        help_menu = Menu(self.icb_menubar, tearoff=0)

        file_menu.add_command(label="Open...", command=self.open, font=self.font_top)
        file_menu.add_command(label="Save", command=self.save, font=self.font_top)
        file_menu.add_command(label="Save as...", command=self.save_as, font=self.font_top)
        file_menu.add_command(label="Preferences", command=self.preference_prompt, font=self.font_top)
        file_menu.add_command(label="Clear", command=self.clear, font=self.font_top)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit, font=self.font_top)

        self.icb_menubar.add_cascade(label="File", menu=file_menu, font=self.font_top)

        edit_menu.add_command(label="Play", command=self.play, font=self.font_top)
        edit_menu.add_command(label="Pause", command=self.pause, font=self.font_top)
        edit_menu.add_command(label="Toggle", command=self.toggle_play_pause, font=self.font_top)
        edit_menu.add_command(label="Reset", command=self.reset, font=self.font_top)
        self.icb_menubar.add_cascade(label="Run", menu=edit_menu, font=self.font_top)

        help_menu.add_command(label="Help", command=self.help, font=self.font_top)
        help_menu.add_command(label="About...", command=self.about, font=self.font_top)

        self.icb_menubar.add_cascade(label="Help", menu=help_menu, font=self.font_top)

        self.config(menu=self.icb_menubar)

    def gui_build_all(self) -> None:
        self.gui_build_top_menu()
        self.gui_build_icb()
        self.gui_build_input_selection_menu()

    def gui_reconfig_dimensions(self):
        """Updates the width and height of the application"""
        self.geometry(str(self.width) + "x" + str(self.height))
        self.screen_icb.config(width=self.width-self.input_selection_screen_width, height=self.height)
        self.screen_is.config(width=self.input_selection_screen_width, height=self.height)
        self.is_edit_table.config(width=self.input_selection_screen_width - self.border_width, height=self.height / 3)

    def preference_prompt(self):
        """ Resolution: 2 Entries
            Bg color: Entry/Scroll menu
            Font Family: Entry
            Font size: Entry
            Toggle Line Colors: Checkbox"""
        self.preference_toplevel = Toplevel(self)
        self.preference_toplevel.resizable(False, False)
        self.preference_toplevel.title("Preferences")
        # Make window modal, meaning actions won't take effect while this window is open
        self.preference_toplevel.wait_visibility()
        self.preference_toplevel.grab_set()
        self.preference_toplevel.transient(self)
        # Build the Resolution entries
        self.res_frame = Frame(self.preference_toplevel)
        self.res_frame.pack()
        self.res_label = Label(self.res_frame, text=" Set Resolution:", font=self.font_prompt)
        self.res_label.pack(side=TOP)
        self.res_width_labelentry = LabeledEntry(master=self.res_frame, label_text="Width:",
                                                 entry_text=str(self.winfo_width()), widget_font=self.font_prompt)
        self.res_width_labelentry.grid(row=0, column=1)
        self.res_height_labelentry = LabeledEntry(master=self.res_frame, label_text="Height:",
                                                  entry_text=str(self.height), widget_font=self.font_prompt)
        self.res_height_labelentry.grid(row=0, column=2)
        # Build background color
        self.color_frame = Frame(self.preference_toplevel)
        self.color_frame.grid(row=1)
        self.color_labelentry = LabeledEntry(master=self.color_frame,
                                             label_text="Background color (string or hex code):",
                                             entry_var=self.background_color, widget_font=self.font_prompt)
        self.color_labelentry.grid(row=0)
        # Buil
        self.font_frame = Frame(self.preference_toplevel)
        self.font_frame.grid(row=2)

        self.font_family_label = Label(self.font_frame, text="Font Family", font=self.font_prompt)
        self.font_family_label.grid(row=0, column=0)
        self.font_family_listbox = Listbox(self.font_frame)
        self.font_family_listbox.grid(row=1, column=0)
        self.font_family_scrollbar = Scrollbar(self.font_frame)
        self.font_family_scrollbar.grid(row=1, column=1)

        for family in self.font_families:
            self.font_family_listbox.insert(END, family)

        self.font_family_listbox.config(yscrollcommand=self.font_family_scrollbar.set)
        self.font_family_scrollbar.config(command=self.font_family_listbox.yview)

        self.font_size_label = Label(self.font_frame, text="Font Size", font=self.font_prompt)
        self.font_size_label.grid(row=0, column=2)
        self.font_size_listbox = Listbox(self.font_frame)
        self.font_size_listbox.grid(row=1, column=2)
        self.font_size_scrollbar = Scrollbar(self.font_frame)
        self.font_size_scrollbar.grid(row=1, column=3)

        for font_size in ['10', '11', '12', '13', '14']:
            self.font_size_listbox.insert(END, font_size)

        self.font_family_listbox.config(yscrollcommand=self.font_size_scrollbar.set)
        self.font_size_scrollbar.config(command=self.font_size_listbox.yview)

        self.preference_done_button = Button(self.preference_toplevel, text="Done",
                                             command=self.close_preference_prompt,
                                             font=self.default_font)
        self.preference_done_button.grid(row=3)
        self.wait_window(self.preference_toplevel)

    def close_preference_prompt(self) -> None:
        # Update settings...
        # Needs work
        width, height = int(self.res_width_labelentry.get()), int(self.res_height_labelentry.get())
        if width >= 800 and height >= 600:
            self.width = int(self.res_width_labelentry.get())
            self.height = int(self.res_height_labelentry.get())
            self.gui_reconfig_dimensions()
        else:
            print("[WARNING]: Resolution must be at least 800x600")

        self.screen_icb.config(background=self.background_color.get())
        # Reset popup state
        self.preference_toplevel.grab_release()
        self.preference_toplevel.destroy()
        self.preference_toplevel.update()

    def timer_prompt(self):
        if self.selected_timer is None:
            return

        self.reset()
        self.timer_popup = Toplevel(self)
        self.timer_popup.resizable(False, False)
        self.timer_popup.title("Editing " + self.selected_timer.get_label())
        # Make window modal, meaning actions wont take effect while this window is open
        self.timer_popup.wait_visibility()
        self.timer_popup.grab_set()
        self.timer_popup.transient(self)

        self.timer_state_intvar.set(self.selected_timer.output())
        self.timer_entry_strvar.set(str(self.selected_timer.get_rate()))

        self.timer_labelframe = LabelFrame(self.timer_popup, text="Set Clock Properties", font=self.font_top)
        self.timer_labelframe.grid(padx=(5, 5), pady=(0, 5))

        entry_frame = Frame(self.timer_labelframe)
        entry_frame.grid(row=0, column=0, padx=(10, 10), pady=(5, 10))

        self.timer_entry_label = Label(entry_frame, text="Timer Update Rate (seconds):", font=self.font_prompt)
        self.timer_entry_label.grid(row=0, column=0, padx=(0, 5), pady=(0, 0), sticky=W)
        self.timer_entry = Entry(entry_frame, textvariable=self.timer_entry_strvar, width=5, font=self.default_font)
        self.timer_entry.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        cb_frame = Frame(self.timer_labelframe)
        cb_frame.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))
        self.timer_state_label = Label(cb_frame, text="Set Timer State (Default On):", font=self.font_prompt)
        self.timer_state_label.grid(row=0, column=0, padx=(0, 5))
        self.timer_state_cb = Checkbutton(cb_frame, variable=self.timer_state_intvar, font=self.default_font)
        self.timer_state_cb.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        self.timer_done_button = Button(self.timer_labelframe, text="Done", command=self.close_timer_prompt,
                                        font=self.default_font)
        self.timer_done_button.grid(row=2, column=0)
        self.wait_window(self.timer_popup)

    def close_timer_prompt(self):
        # Update timer settings
        self.selected_timer.set_rate(float(self.timer_entry_strvar.get()))
        self.selected_timer.set_output(self.timer_state_intvar.get())
        print("Updated timer:", self.selected_timer)
        # Reset popup state
        self.selected_timer = None
        self.timer_state_intvar = IntVar(value=True)
        self.timer_entry_strvar.set(str(self.default_update_rate))

        self.timer_popup.grab_release()
        self.timer_popup.destroy()
        self.timer_popup.update()

    def exit_prompt(self, title: str, msg: str, callback):
        self.screen_exit_prompt = Toplevel(self)
        self.screen_exit_prompt.title(title)
        # Modal window.
        self.screen_exit_prompt.wait_visibility()
        self.screen_exit_prompt.grab_set()
        self.screen_exit_prompt.transient(self)

        self.prompt_label = ttk.Label(self.screen_exit_prompt, text=msg, font=self.font_prompt)
        self.prompt_label.pack(padx=(15, 15), pady=(15, 15))

        self.prompt_button_confirm = Button(self.screen_exit_prompt, text="Yes", command=callback,
                                            font=self.font_prompt)
        self.prompt_button_confirm.pack(side=LEFT, padx=(55, 5), pady=(10, 20))

        self.prompt_button_cancel = Button(self.screen_exit_prompt, text="Cancel", command=self.close_exit_prompt,
                                           font=self.font_prompt)
        self.prompt_button_cancel.pack(side=RIGHT, padx=(5, 55), pady=(10, 20))

        self.screen_exit_prompt.resizable(False, False)

        self.wait_window(self.screen_exit_prompt)

    def close_exit_prompt(self) -> None:
        self.screen_exit_prompt.grab_release()
        self.screen_exit_prompt.destroy()
        self.screen_exit_prompt.update()

    def exit(self):
        self.exit_prompt("Exit Confirmation", "Are You Sure You Want To Exit?", self.exit_app)

    def exit_app(self) -> None:
        self.reset(None)
        self.quit()
        self.destroy()
        self.update()
        sys.exit(0)

    def run(self) -> None:
        self.gui_build_all()
        self.mainloop()


if __name__ == "__main__":
    app = Application()
    app.run()

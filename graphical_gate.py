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

import threading
from time import *
from tkinter import *
from tkinter.font import *

from base_input import *


def logic_clock(gate) -> int:
    """Checks if the timer has expired, if so, toggle the clock and restart the timer"""
    if not gate.get_event().is_set() and not ClockTk.clocks_paused:
        threading.Timer(gate.get_rate(), logic_clock, [gate]).start()
        gate.toggle()

    return gate.output()


def get_logic_func_from_name(name: str) -> Optional[Callable]:
    if name == logic_not.__name__:
        return logic_not
    elif name == logic_and.__name__:
        return logic_and
    elif name == logic_nand.__name__:
        return logic_nand
    elif name == logic_or.__name__:
        return logic_or
    elif name == logic_xor.__name__:
        return logic_xor
    elif name == power.__name__:
        return power
    elif name == output.__name__:
        return output
    elif name == logic_clock.__name__:
        return logic_clock
    else:
        print("Invalid name:", name)
        return None


class LineRepository:
    """Stores the lines between gates.  The tuple (source gate, destination gate) is the key to get the Canvas item id
       which can be used to modify/delete the line"""
    lines = {}
    canvas = None

    @staticmethod
    def set_canvas(canvas: Canvas):
        LineRepository.canvas = canvas

    @staticmethod
    def store(src: BaseGate, dest: BaseGate, line_id: object) -> None:
        """Stores line_id in a dict with the key (src, dest)"""
        if (dest, src) in LineRepository.lines.keys():  # If this line is already here in a different order, keep it
            LineRepository.lines[(dest, src)] = line_id
        else:
            LineRepository.lines[(src, dest)] = line_id

    @staticmethod
    def remove_by_id(line_id: int) -> None:
        """Delete line by its id"""
        for key in LineRepository.lines.keys():
            if LineRepository.lines[key] == line_id:
                LineRepository.canvas.delete(LineRepository.lines[key])
                del LineRepository.lines[key]

    @staticmethod
    def remove_by_key(key: (BaseGate, BaseGate)) -> None:
        """Delete line by its key"""
        if key in LineRepository.lines.keys():
            # print("Removed line", LineRepository.lines[key],"between:", key)
            LineRepository.canvas.delete(LineRepository.lines[key])
            del LineRepository.lines[key]
        elif key[::-1] in LineRepository.lines.keys():  # Check if the reversed key is in the repo
            # print("Removed line", LineRepository.lines[key[::-1]],"between:", key[::-1])
            LineRepository.canvas.delete(LineRepository.lines[key[::-1]])
            del LineRepository.lines[key[::-1]]
        else:
            pass
            # print("No line between", key[0].get_label(), key[1].get_label())

    @staticmethod
    def get(key: (BaseGate, BaseGate)) -> int:
        """Get line id from key"""
        if key in LineRepository.lines.keys():
            # print("Getting line id: {0} for ({1}, {2})".format(LineRepository.lines[key], key[0], key[1]))
            return LineRepository.lines[key]
        elif key[::-1] in LineRepository.lines.keys():
            # print("Getting line id: {0} for ({1}, {2})".format(LineRepository.lines[key[::-1]], key[1], key[0]))
            return LineRepository.lines[key[::-1]]

    @staticmethod
    def get_all_ids(gate) -> list[int]:
        """Returns all line ids in the repo"""
        ids = []
        for key in LineRepository.lines.keys():
            if gate in key:
                ids.append(LineRepository.lines[key])
        return ids

    @staticmethod
    def get_all_other_gates(gate) -> list[BaseGate]:
        """Gets all gates in which gate is in the key"""
        other_gates = []
        for key in LineRepository.lines.keys():
            if gate in key:
                other_gates.append(LineRepository.lines[key])
        return other_gates


def get_line_fill(value: int) -> str:
    """Gets what color a line should be based on its value"""
    if value == NULL or not LogicGate.line_colors_on:
        return LogicGate.line_fill_null
    elif value == TRUE:
        return LogicGate.line_fill_true
    else:
        return LogicGate.line_fill_false


class GraphicalGate:
    """Superclass for graphical gates. Only to be inherited from.  Stores the common information between all: the label, 
       image, canvas position, and more."""
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
        self.rect_id = NULL  # Canvas item id for the selected rectangle
        self.width, self.height = 0, 0  # Image width, height
        self.input_id = self.canvas.create_image(self.center[0], self.center[1], image=self.img) \
            if center != (NULL, NULL) else NULL

        bbox = self.canvas.bbox(self.input_id)
        if bbox is not None:  # Bbox is not None when the gate is placed on the canvas
            self.width, self.height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    def set_image_file(self, filename: str) -> None:
        """Replaces image file of the gate"""
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
        """Adds border rectangle around the gate, returns the rectangle id"""
        if self.rect_id < 0:
            self.rect_id = self.canvas.create_rectangle(self.top_left()[0] - self.border_offset,
                                                        self.top_left()[1] - self.border_offset,
                                                        self.bottom_right()[0] + self.border_offset,
                                                        self.bottom_right()[1] + self.border_offset,
                                                        width=self.border_width, outline='black')
        return self.rect_id

    def num_outputs(self) -> int:
        return len(self.output_gates)

    def remove_rect(self) -> None:
        if self.rect_id >= 0:
            self.canvas.delete(self.rect_id)
            self.rect_id = -1

    def remove_line(self, other: GraphicalGate) -> None:
        pass

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

    def remove_input(self, inp: GraphicalGate):
        self.inputs.remove(inp)
        self.remove_line(inp)

    def remove_output(self, destination: GraphicalGate) -> None:
        self.output_gates.remove(destination)
        self.remove_line(destination)

    def num_inputs(self) -> int:
        return len(self.inputs)

    def delete(self) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)

        for input_gate in self.inputs:
            input_gate.remove_output(self)

        for output_gate in self.output_gates:
            output_gate.remove_input(self)
            output_gate.set_output(NULL)

        self.input_id = self.rect_id = NULL

    def get_canvas(self) -> Canvas:
        return self.canvas

    def top_left(self) -> (int, int):
        return self.center[0] - self.get_width() // 2, self.center[1] - self.get_height() // 2

    def bottom_right(self) -> (int, int):
        return self.center[0] + self.get_width() // 2, self.center[1] + self.get_height() // 2


class LogicGate(GraphicalGate):
    """Class used to depict a logic gate.  Each has an associated function and image"""
    line_colors_on = True
    line_fill_true = "green"
    line_fill_false = "red"
    line_fill_null = "black"

    def __init__(self, func: Callable, image_file: str, label: str = "", canvas: Optional[Canvas] = None,
                 center: (int, int) = (NULL, NULL), out: int = NULL):
        GraphicalGate.__init__(self, image_file, label=label, canvas=canvas, center=center)
        self.func = func
        self.out = IntClass(value=out)  # Output value
        self.base_gate = BaseGate(func=func, label=label, out=self.out)

    @staticmethod
    def construct_copy(old: LogicGate, pos: (int, int)) -> LogicGate:
        return LogicGate(old.get_func(), image_file=old.get_image_file(), label=new_gate_label(old.get_label()),
                         canvas=old.get_canvas(), center=pos, out=old.output())

    def base(self) -> BaseGate:
        return self.base_gate

    def get_base_input_gates(self) -> list[BaseGate]:
        return self.base_gate.get_input_gates()

    def get_base_output_gates(self) -> list[BaseGate]:
        return self.base_gate.get_output_gates()

    def output(self) -> int:
        return self.base().output()

    def delete(self) -> None:
        self.base().delete()
        GraphicalGate.delete(self)

    def remove_input(self, inp: GraphicalGate):
        self.inputs.remove(inp)
        self.remove_line(inp)

    def remove_output(self, destination: GraphicalGate) -> None:
        self.output_gates.remove(destination)
        self.remove_line(destination)

    def set_output(self, out: int) -> None:
        self.out.set(out)
        self.update_line_colors()

    def get_func(self) -> Callable:
        return self.func

    def remove_line(self, other: LogicGate) -> None:
        LineRepository.remove_by_key((self.base(), other.base()))

    def update_line_colors(self) -> None:
        output_val = self.output()
        if self.output_gates is None:
            return

        fill = get_line_fill(output_val)
        for out_gate in self.output_gates:
            self.canvas.itemconfig(LineRepository.get((self.base(), out_gate.base())), fill=fill)

        for gate in self.output_gates:
            gate.update_line_colors()

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
            self.canvas.coords(LineRepository.get((self.inputs[i].base(), self.base())), src_pos[0], src_pos[1], left_center_pos[0], left_center_pos[1])
        # Update all outgoing lines to new position
        right_center_pos = (self.bottom_right()[0], self.get_center()[1])  # Right-Center Point to connect src gates
        for i in range(len(self.output_gates)):
            dest_pos = (self.output_gates[i].top_left()[0], self.output_gates[i].get_center()[1])
            self.canvas.coords(LineRepository.get((self.base(), self.output_gates[i].base())), dest_pos[0], dest_pos[1],
                               right_center_pos[0], right_center_pos[1])

    def remove_base_connection(self, other: BaseGate, self_is_parent: bool) -> None:
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
        return OutputGate(image_file=old.get_image_file(), label=new_gate_label(old.get_label()),
                          canvas=old.get_canvas(),
                          center=pos)

    def set_output(self, out: int) -> None:
        self.out.set(out)
        self.update_line_colors()

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
            self.canvas.coords(LineRepository.get((self.inputs[i].base(), self.base())), src_pos[0], src_pos[1],
                               left_center_pos[0], left_center_pos[1])

    def update_line_colors(self) -> None:
        output_val = self.output()
        fill = LogicGate.line_fill_true if output_val == TRUE else LogicGate.line_fill_false if output_val == FALSE else LogicGate.line_fill_null
        self.canvas.itemconfig(self.input_id, outline=fill)

    def delete(self, ) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)

        for input_gate in self.inputs:
            if isinstance(input_gate, Circuit):
                pass
            input_gate.remove_output(self)

        self.input_id = self.rect_id = -1
        self.set_output(NULL)


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
        """Starts clock object"""
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
        """Creates new clock from copy of old"""
        return ClockTk(update_rate=old.get_rate(), image_file=old.get_image_file(),
                       label=new_gate_label(old.get_label()),
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


def connect_bg_to_bg(src: BaseGate, out: BaseGate) -> None:
    """Connects src base gate to out base gate, adding them to their appropriate inputs/outputs"""
    if src not in out.inputs:
        out.inputs.append(src)
    if out not in src.output_gates:
        src.output_gates.append(out)
    src.update_output_values()


def connect_lgate_to_lgate(src: LogicGate, dest: LogicGate) -> None:
    """Connects a logic gate to another"""
    if          is_power_gate(dest) or is_clock(dest) \
            or (is_not_gate(dest) and len(dest.inputs) > 0) \
            or not (not is_parent(dest, src) and dest not in src.get_output_gates()) \
            or (is_output_gate(dest) and len(dest.inputs) > 0):
        #print("[connect_lgate_to_lgate]: invalid line between", src, type(src), dest, type(dest))
        return

    connect_bg_to_bg(src.base(), dest.base())
    if src not in dest.get_input_gates():
        dest.inputs.append(src)
    if dest not in src.get_output_gates():
        src.output_gates.append(dest)

    src_pos, dest_pos = (src.bottom_right()[0], src.get_center()[1]), \
                        (dest.top_left()[0], dest.get_center()[1])

    src_out = src.output()

    line_color = get_line_fill(src_out)

    line_id = src.get_canvas().create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4, fill=line_color)
    LineRepository.store(src.base(), dest.base(), line_id)

    src.update_line_colors()


def connect_lgate_to_circuit(src: LogicGate, circuit: Circuit, dest: BaseGate) -> None:
    """Connects a source logic gate to a destination circuit"""
    # print("connect_lgate_to_circuit")
    # print(is_output_gate(src))
    # print(is_not_gate(dest) and len(dest.inputs) > 0)
    # print(not (not is_parent(dest, src.base()) and circuit not in src.get_output_gates()))
    if      is_output_gate(src) or \
            (is_not_gate(dest) and len(dest.inputs) > 0) or \
            not (not is_parent(dest, src.base()) and circuit not in src.get_output_gates()):
        print("[connect_lg_to_circuit]: invalid line between", src, type(src), dest, type(dest))
        return

    connect_bg_to_bg(src.base(), dest)
    if src not in circuit.get_input_gates(dest):
        circuit.inputs[dest].append(src)
    if circuit not in src.get_output_gates():
        src.output_gates.append(circuit)

    src_pos, dest_pos = (src.bottom_right()[0], src.get_center()[1]), \
                        (circuit.top_left()[0], circuit.get_center()[1])

    line_id = src.get_canvas().create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4,
                                           fill=get_line_fill(src.output()))
    LineRepository.store(src.base(), dest, line_id)
    src.update_line_colors()


def connect_circuit_to_lgate(circuit: Circuit, src: BaseGate, dest: LogicGate) -> None:
    """Connects a source circuit to a destination logic"""
    # or circuit in dest.get_input_gates()\
    if          is_power_gate(dest) or is_clock(dest) \
            or (is_not_gate(dest) and len(dest.inputs) > 0) \
            or (is_parent(dest.base(), src) or dest.base() in src.get_output_gates()) \
            or (is_output_gate(dest) and len(dest.inputs) > 0) \
            or dest.base() in src.get_output_gates():
        print("[connect_circuit_to_lgate]: invalid line between", src, type(src), dest, type(dest))
        return

    connect_bg_to_bg(src, dest.base())
    if circuit not in dest.get_input_gates():
        dest.inputs.append(circuit)
    if dest not in circuit.get_output_gates(src):
        circuit.output_gates[src].append(dest)

    src_pos, dest_pos = (circuit.bottom_right()[0], circuit.get_center()[1]), \
                        (dest.top_left()[0], dest.get_center()[1])

    line_id = circuit.get_canvas().create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4, fill=get_line_fill(src.output()))
    LineRepository.store(src, dest.base(), line_id)

    circuit.update_line_colors()


def connect_circuit_to_circuit(src_circuit: Circuit, src: BaseGate, dest_circuit: Circuit, dest: BaseGate) -> None:
    """Connect src circuit to dest circuit"""
    # or src_circuit in dest_circuit.get_input_gates() \
    if         (is_not_gate(dest) and len(dest.inputs) > 0) \
            or (is_parent(dest, src) or dest in src.get_output_gates()) \
            or dest in src.get_output_gates():
        print("[connect_circuit_to_circuit]: invalid line between", src, type(src), dest, type(dest))
        return

    connect_bg_to_bg(src, dest)
    if src_circuit not in dest_circuit.get_input_gates(dest):
        dest_circuit.inputs[dest].append(src_circuit)
    if dest_circuit not in src_circuit.get_output_gates(src):
        src_circuit.output_gates[src].append(dest_circuit)

    src_pos, dest_pos = (src_circuit.bottom_right()[0], src_circuit.get_center()[1]), \
                        (dest_circuit.top_left()[0],    dest_circuit.get_center()[1])

    line_id = src_circuit.get_canvas().create_line(src_pos[0], src_pos[1], dest_pos[0], dest_pos[1], width=4,
                                                   fill=get_line_fill(src.output()))
    LineRepository.store(src, dest, line_id)
    src_circuit.update_line_colors()


def disconnect_bg_to_bg(gate1: BaseGate, gate2: BaseGate) -> None:
    """Disconnects two BaseGates"""
    src, dest = (gate1, gate2) if is_parent(gate1, gate2) else (gate2, gate1) if is_parent(gate2, gate1) else (None, None)
    if not src or not dest:
        return
    src.remove_output(dest)
    dest.remove_input(src)
    dest.set_output(NULL)
    dest.update_output_values()


def disconnect_lgate_to_lgate(gate1: LogicGate, gate2: LogicGate) -> None:
    """Disconnects two logic gates"""
    src, dest = (gate1, gate2) if is_parent(gate1, gate2) else (gate2, gate1) if is_parent(gate2, gate1) else (None, None)
    if not src or not dest:
        return
    src.remove_output(dest)
    dest.remove_input(src)
    dest.set_output(NULL)
    LineRepository.remove_by_key((src.base(), dest.base()))
    disconnect_bg_to_bg(gate1.base(), gate2.base())
    dest.update_line_colors()


def disconnect_circuit_to_lgate(circuit: Circuit, cir_bg: Optional[BaseGate], lgate: LogicGate) -> None:
    """Removes connection between circuit and logic gate"""
    if cir_bg is None:
        return

    src, dest = (circuit, lgate) if is_parent(cir_bg, lgate.base()) else (lgate, circuit) if is_parent(lgate.base(), cir_bg) else (None, None)
    if not src or not dest:
        return
    src.remove_output(dest) if isinstance(src, LogicGate) else src.remove_output(dest, cir_bg)
    dest.remove_input(src)
    dest.set_output(NULL) if isinstance(dest, LogicGate) else dest.set_output(NULL, cir_bg)
    LineRepository.remove_by_key((cir_bg, lgate.base()))
    disconnect_bg_to_bg(cir_bg, lgate.base())
    dest.update_line_colors()


def disconnect_circuit_to_circuit(circuit1: Circuit, cir_bg1: BaseGate, circuit2: Circuit, cir_bg2: BaseGate) -> None:
    # Determine whichi Circuit, BaseGate tuple is the child and parent
    (src, src_base), (dest, dest_base) = ((circuit1, cir_bg1), (circuit2, cir_bg2)) if is_parent(cir_bg1, cir_bg2) else ((circuit2, cir_bg2), (circuit1, cir_bg1)) if is_parent(cir_bg2, cir_bg1) else ((None, None), (None, None))
    if not src or not dest:
        return
    src.remove_output(dest, src_base)
    dest.remove_input(src, dest_base)
    dest.set_output(NULL, cir_bg2)
    LineRepository.remove_by_key((cir_bg1, cir_bg2))
    disconnect_bg_to_bg(cir_bg1, cir_bg2)
    dest.update_line_colors()


class Circuit(GraphicalGate):
    def __init__(self, image_file: str, canvas: Canvas, font: Font, label: str = "",
                 center: (int, int) = (NULL, NULL)):
        GraphicalGate.__init__(self, image_file=image_file, label=label, canvas=canvas, center=center)
        # Holds which inside gates are marked as input/output
        self.connections = {
            "inputs": {},
            "outputs": {}
        }
        self.label_id = NULL
        self.font = font

        self.inputs =  {}
        self.output_gates = {}
        self.inside_gates = {}

        self.label_id = self.canvas.create_text(center[0], center[1] + 10 + self.get_height() // 2,
                                                text=self.get_label(), fill='black', font=self.font)

    @staticmethod
    def construct_copy(old: Circuit, pos: (int, int)) -> Circuit:
        """Creates a copy of the provided circuit, including the inner gates so that each copy is independent of each
        other."""
        new_circuit = Circuit(old.get_image_file(), old.get_canvas(), font=old.font, label=old.get_label(), center=pos)

        # Create Copies of each gate in the circuit
        old_gates = old.get_gates()
        for gate in old_gates:
            new_gate = BaseGate(gate.get_func(), new_gate_label(gate.get_label()), None, None, IntClass(value=NULL))
            new_gate.output()
            for label in old.connections["inputs"].keys():
                if gate == old.connections["inputs"][label]:
                    new_circuit.set_circuit_input(label, new_gate)

            for label in old.connections["outputs"].keys():
                if gate == old.connections["outputs"][label]:
                    new_circuit.set_circuit_output(label, new_gate)

            new_circuit.add_inner_gate(new_gate)

        # Connect the copied gates in the appropriate manner
        new_gates = new_circuit.get_gates()
        for (i, (old_out_gate1, new_out_gate1)) in enumerate(zip(old_gates, new_gates)):
            for (j, (old_out_gate2, new_out_gate2)) in enumerate(zip(old_gates, new_gates)):
                if old_out_gate2 in old_out_gate1.get_input_gates():
                    connect_bg_to_bg(new_out_gate2, new_out_gate1)
                elif old_out_gate2 in old_out_gate1.get_output_gates():
                    connect_bg_to_bg(new_out_gate1, new_out_gate2)

        return new_circuit

    def set_font(self, new_font: Font) -> None:
        self.font = new_font
        self.canvas.itemconfig(self.label_id, font=self.font)

    def add_inner_gate(self, gate: BaseGate) -> None:
        if gate.get_func() in self.inside_gates.keys():
            self.inside_gates[gate.get_func()].append(gate)
        else:
            self.inside_gates[gate.get_func()] = [gate]

    def remove_inner_gate(self, gate: BaseGate):
        if gate.get_func() in self.inside_gates.keys() and gate in self.inside_gates[gate.get_func()]:
            self.inside_gates[gate.get_func()].remove(gate)

    def update_line_colors(self) -> None:
        for name in self.connections["outputs"].keys():
            gate = self.connections["outputs"][name]
            if gate:
                fill = get_line_fill(gate.output())
                for dest_gate in self.output_gates[gate]:
                    self.canvas.itemconfig(LineRepository.get((gate, dest_gate)), fill=fill)
                    dest_gate.update_line_colors()

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
        for base_input_gate in self.inputs.keys():
            for input_gate in self.inputs[base_input_gate]:
                src_pos = (input_gate.bottom_right()[0], input_gate.get_center()[1])
                self.canvas.coords(LineRepository.get((input_gate, self)), src_pos[0], src_pos[1], left_center_pos[0], left_center_pos[1])
        # Update all outgoing lines to new position
        right_center_pos = (self.bottom_right()[0], self.get_center()[1])  # Right-Center Point to connect src gates
        for gate in self.output_gates.keys():
            for dest_gate in self.output_gates[gate]:
                dest_pos = (dest_gate.top_left()[0], dest_gate.get_center()[1])
                self.canvas.coords(LineRepository.get((self, dest_gate)), dest_pos[0], dest_pos[1], right_center_pos[0], right_center_pos[1])

    def reset_inputs(self) -> None:
        self.connections["inputs"] = {}

    def reset_outputs(self) -> None:
        self.connections["outputs"] = {}

    def get_output_gates(self, gate: Optional[BaseGate] = None) -> list[LogicGate | Circuit]:
        if gate:
            if gate in self.output_gates.keys():
                return self.output_gates[gate]
            else:
                return []
        else:
            return [self.output_gates[gate] for gate in self.output_gates]

    def get_input_gates(self, gate: Optional[BaseGate] = None) -> list[LogicGate | Circuit]:
        if gate:
            if gate in self.inputs.keys():
                return self.inputs[gate]
            else:
                return []

        return [self.inputs[gate] for gate in self.inputs]

    def get_all_input_gates(self, ls: list) -> list:
        for gate in self.inputs.keys():
            for in_gate in self.inputs[gate]:
                if in_gate not in ls:
                    ls.append(in_gate)
                gate.get_all_input_gates(ls)

        return ls

    def remove_output(self, destination: Circuit | LogicGate, src: Optional[BaseGate] = None) -> None:
        if src is None:
            return
        if list_contains(self.get_output_gates(src), destination)[0]:
            self.output_gates[src].remove(destination)
            LineRepository.remove_by_key((self, destination))

    def remove_input(self, src: Circuit | LogicGate, dest: Optional[BaseGate] = None):
        if dest is None:
            return
        if list_contains(self.get_input_gates(dest), input)[0]:
            self.inputs[dest].remove(src)
            LineRepository.remove_by_key((src, self))

    def remove_all_lines(self, gate: Optional[BaseGate] = None) -> None:
        for input_gate in self.get_input_gates():
            LineRepository.remove_by_key((input_gate, self))

        if gate is not None:
            for dest in self.output_gates[gate]:
                LineRepository.remove_by_key((self, dest))
        else:
            for gate in self.output_gates.keys():
                for dest_gate in self.output_gates[gate]:
                    LineRepository.remove_by_key((self, dest_gate))

    def get_input(self, name: str) -> BaseGate:
        return self.connections["inputs"][name]

    def remove(self, gate: BaseGate) -> None:
        for label in self.get_io_gates("in"):
            if self.connections["inputs"][label] == gate:
                self.connections["inputs"][label] = None

        for label in self.get_io_gates("out"):
            if self.connections["outputs"][label] == gate:
                self.connections["outputs"][label] = None

        if gate in self.output_gates.keys():
            for dest_gate in self.output_gates[gate]:
                if isinstance(dest_gate, LogicGate):
                    disconnect_circuit_to_lgate(self, gate, dest_gate)
                elif isinstance(dest_gate, Circuit):
                    for dest_cir_ti in gate.get_output_gates():
                        if dest_cir_ti in dest_gate.get_input_gates():
                            disconnect_circuit_to_circuit(self, gate, dest_gate, dest_cir_ti)
                LineRepository.remove_by_key((self, dest_gate))
            del self.output_gates[gate]

        self.remove_inner_gate(gate)
        gate.delete()

        self.update_line_colors()

    def set_circuit_output(self, name: str, gate: Optional[BaseGate] = None) -> None:
        self.connections["outputs"][name] = gate
        if gate is not None:
            self.output_gates[gate] = []

    def set_circuit_input(self, name: str, gate: Optional[BaseGate] = None) -> None:
        self.connections["inputs"][name] = gate
        if gate is not None:
            self.inputs[gate] = []

    def get_output(self, name: str) -> BaseGate:
        return self.connections["outputs"][name]

    def get_gates(self, key: Optional[Callable] = None) -> list[BaseGate]:
        if key and key in self.inside_gates.keys():
            return self.inside_gates[key]
        else:
            ls = []
            for fn in self.inside_gates.keys():
                ls += self.inside_gates[fn]
            return ls

    def set_output(self, value: int, gate: Optional[BaseGate] = None):
        if gate and gate in self.get_gates(gate.get_func()):
            gate.set_output(value)

    def delete(self) -> None:
        self.canvas.delete(self.input_id)
        self.canvas.delete(self.rect_id)
        self.delete_text()

        for gate in self.inputs.keys():
            for in_gate in self.inputs[gate]:
                if is_circuit(in_gate):
                    for out_base in in_gate.get_io_gates("out"):
                        for input_circuit_base_output in in_gate.get_output_gates(out_base):
                            if gate in input_circuit_base_output.get_output_gates():
                                disconnect_circuit_to_circuit(in_gate, input_circuit_base_output, self, gate)
                else:
                    disconnect_circuit_to_lgate(self, gate, in_gate)

        for gate in self.output_gates.keys():
            for out_gate in self.output_gates[gate]:
                if is_circuit(out_gate):
                    for in_base in out_gate.get_io_gates("in"):
                        for output_circuit_base_output in out_gate.get_input_gates(in_base):
                            if gate in output_circuit_base_output.get_input_gates():
                                disconnect_circuit_to_circuit(self, gate, out_gate, output_circuit_base_output)
                else:
                    disconnect_circuit_to_lgate(self, gate, out_gate)

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


def is_and_gate(gate: Any) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, BaseGate)) and gate.get_func() == logic_and


def is_nand_gate(gate: Any) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, BaseGate)) and gate.get_func() == logic_nand


def is_or_gate(gate: Any) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, BaseGate)) and gate.get_func() == logic_or


def is_xor_gat(gate: Any) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, BaseGate)) and gate.get_func() == logic_xor


def is_not_gate(gate: Any) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, BaseGate)) and gate.get_func() == logic_not


def is_power_gate(gate: Any) -> bool:
    return (isinstance(gate, LogicGate) or isinstance(gate, BaseGate)) and gate.get_func() == power


def is_output_gate(gate: Any) -> bool:
    return isinstance(gate, OutputGate)


def is_clock(gate: Any) -> bool:
    return isinstance(gate, ClockTk)


def is_circuit(gate: GraphicalGate) -> bool:
    return isinstance(gate, Circuit)


def connection_exists(gate1: LogicGate, gate2: LogicGate) -> bool:
    return list_contains(gate1.get_input_gates(), gate2)[0] or list_contains(gate1.get_output_gates(), gate2)[0]


def is_parent(parent: GraphicalGate | BaseGate, child: GraphicalGate | BaseGate) -> bool:
    if (isinstance(parent, GraphicalGate) and isinstance(child, GraphicalGate)) or (isinstance(parent, BaseGate) and isinstance(child, BaseGate)):
        return list_contains(child.get_all_input_gates([]), parent)[0]
    else:
        log_msg(ERROR, "Invalid is_parent types: {0}:{1}".format(type(parent), type(child)), ValueError)


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
        if key in self.gate_infos.keys():
            return self.gate_infos[key]

    def __setitem__(self, key: Callable, value: GateInfo) -> None:
        self.gate_infos[key] = value

    def __len__(self):
        return len(self.keys())

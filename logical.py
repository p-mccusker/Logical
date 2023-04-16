########################################################################################################################
# File: circuit.py
# Author: Peter McCusker
# License:
# Date: 01/04/2023
# Description:
########################################################################################################################
# TODO:
#   - Scrolling/Resizing for canvas
#   - Zoom In/Out
#   - Proper resizing of side pane on font changes
#   - Method of creating custom circuits to be place and used as other gates
########################################################################################################################
import platform
import os
from tkinter import filedialog as fd

import tomlkit

from tk_widgets import *


def capitalize(string: str) -> str:
    """Capitalizes the first letter of a string"""
    if len(string) == 0:
        return string
    return string[0].upper() + (string[1:] if len(string) > 1 else "")


def point_in_rect(x, y, tl: (int, int), br: (int, int)):
    """Return True if x,y is in rectangle (tl, br) """
    return (tl[0] <= x <= br[0]) and (tl[1] <= y <= br[1])


def do_overlap(l1: (int, int), r1: (int, int), l2: (int, int), r2: (int, int)) -> bool:
    """Returns true if two rectangles (l1, r1) and (l2, r2) overlap"""
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


def join_folder_file(folder: str, file: str):
    return os.path.join(folder, file)


def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Application(Tk):
    img_width = 75
    img_height = 50
    max_selectable_gates = 100
    border_width = 3  # Width of border separating canvas from the right pane
    input_selection_screen_width = 250  # Width of the right pane
    # bg_colors = ["white", "black", "red", "green", "blue", "cyan", "yellow", "magenta"]
    # Fonts #####################
    font_family = "Helvetica"
    font_size = 12
    active_font = None
    font_top = None
    # Preference Dirs ###########
    user_home_dir = os.path.expanduser('~')
    preference_file_name = "logical.toml"

    def __init__(self, width: int = 1280, height: int = 720):
        super().__init__()
        # Parse command line arguments
        for i, arg in enumerate(sys.argv):
            if arg == '-w':
                width = int(sys.argv[i + 1])
                if width < 800:
                    log_msg(ERROR, "Width must be >= 800", ValueError)

            if arg == '-h':
                height = int(sys.argv[i + 1])
                if height < 600:
                    log_msg(ERROR, sys.argv[i + 1] + ": height must be an integer >", ValueError)

        self.width = width
        self.height = height
        self.x = self.width / 2
        self.y = self.height / 2
        self.background_color = StringVar(value="white")
        self.icon = PhotoImage(file=resource_path(join_folder_file(IMG_FOLDER, "icon.png")))

        self.title("Logical")
        self.geometry(str(self.width) + "x" + str(self.height))
        self.resizable(False, False)
        self.config(background=self.background_color.get())
        self.iconphoto(True, self.icon)

        self.imgs = []  # [PhotoImage(file=self.gates[func]["image_file"]) for func in self.gates.keys()]
        # Dictionary to hold the input gates, where the gate type is the key and the value is the list of gates
        self.gates = GatesInfoRepo()
        self.build_gate_repo()

        if platform.system() == "Windows":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)

        # List to hold references to the Photoimages of the input gates so that Tkinter doesn't garbage collect
        # prematurely

        self.default_update_rate = 2  # Default Update for a new clock in seconds, default to 2s

        self.active_input = None  # The input object to be placed when the user clicks the mouse
        self.active_input_pi = None  # Photoimage for active gate
        self.active_input_img_index = 0  # Canvas image index of active gate
        # Fonts #####################
        self.active_font = font.Font(family=Application.font_family, size=Application.font_size, weight=font.NORMAL,
                                     slant=font.ROMAN)
        self.font_top = font.Font(family=Application.font_family, size=Application.font_size - 1, weight=font.NORMAL,
                                  slant=font.ROMAN)
        #############################
        # ICB Widgets ###############
        self.screen_icb = None  # Canvas gates are placed on
        self.icb_menubar = None  # Top Menu (File, Edit, Help...)
        self.icb_is_gate_active = False  # If True, shows input gate as cursor is dragged around
        self.icb_selected_gates = []  # Holds references to all currently selected gates when performing operations
        self.icb_click_drag_gate = None  # The gate currently being moved by the mouse
        #############################
        # Prompt Widgets ############
        self.screen_exit_prompt = None  # Toplevel popup window for prompt
        #############################
        # Input Selection Widgets ###
        self.bordered_frame = None  # Border Frame to separate canvas and the right pane
        self.screen_is = None  # Separate Window to select which gate input to place
        self.is_buttons = []  # Holds tuple: the buttons for each input gate and its border frame
        self.is_edit_table = None  # Table to toggle inputs on/off
        self.is_button_frame = None  # LabelFrame to hold the buttons and their labels
        #############################
        #############################
        # Timer Window Widgets ######
        self.timer_popup = None  # Toplevel popup window for window

        self.selected_timer = None  # The timer that is currently being modified
        self.timer_state_cb = None  # Checkbox to toggle the timer's default state
        self.timer_state_intvar = IntVar(value=TRUE)  # Value of the default state checkbox
        self.timer_entry = None  # Entry for timer toggle rate
        self.timer_entry_strvar = StringVar(value=str(self.default_update_rate))  # Value of the timer update rate
        #############################
        # Saving/Loading Vars #######
        self.filename = ""
        self.file_separator = "<--CONNECTIONS-->"
        self.file_type = ".cir"
        self.open_filename = ""
        self.preference_path = ""
        self.save_path = ""
        #############################
        # Preference Vars ###########
        self.preference_toplevel = None
        self.res_width_var = None
        self.res_width_entry = None
        self.res_height_var = None
        self.res_height_entry = None
        self.color_labelentry = None
        self.line_colors_checkbox = None
        self.font_family_listbox = None
        self.font_size_listbox = None
        self.font_families = [*set(list(font.families()))]
        self.font_families.sort()
        #############################
        # Help Vars ###########
        self.help_window = None
        #############################

        self.init_file_paths()

    def build_gate_repo(self):
        """Compiles repository for gates, the active ones, their names, and descriptions.  When adding new functions,
        register them here"""
        self.gates.register_gate(power, name=None,
                                 desc="This is a discrete power source.  It is either on and off and can be toggled by "
                                      "clicking on the Power Gate Table",
                                 callback=self.set_active_fn_power,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "power.png")))
        self.gates.register_gate(logic_not, name=None, desc="", callback=self.set_active_fn_not,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "not.png")))
        self.gates.register_gate(logic_and, name=None, desc="", callback=self.set_active_fn_and,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "and.png")))
        self.gates.register_gate(logic_nand, name=None, desc="", callback=self.set_active_fn_nand,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "nand.png")))
        self.gates.register_gate(logic_or, name=None, desc="", callback=self.set_active_fn_or,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "or.png")))
        self.gates.register_gate(logic_xor, name=None, desc="", callback=self.set_active_fn_xor,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "xor.png")))
        self.gates.register_gate(output, name=None, desc="", callback=self.set_active_fn_output,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "output.png")))
        self.gates.register_gate(logic_clock, name=None, desc="", callback=self.set_active_fn_clock,
                                 image_file=resource_path(join_folder_file(IMG_FOLDER, "clock.png")))

    def update_font(self, family: str, size: int) -> None:
        self.font_family = family
        self.font_size = size
        self.active_font = font.Font(family=self.font_family, size=self.font_size, weight=font.NORMAL,
                                     slant=font.ROMAN)
        self.font_top = font.Font(family=self.font_family, size=self.font_size - 1, weight=font.NORMAL,
                                  slant=font.ROMAN)

        self.gui_build_top_menu()
        self.is_edit_table.set_font(self.active_font)
        self.is_edit_table.set_focus_widget(self.screen_icb)
        self.is_button_frame.config(font=self.active_font)
        for (btn, label) in self.is_buttons:
            label.config(font=reconfig_font(self.active_font, offset=-2, weight='bold'))

    def init_file_paths(self) -> None:
        if platform.system() == "Windows":  # If current platform is Windows...
            self.preference_path = os.path.join(self.user_home_dir, "Documents", "logical")
            self.save_path = os.path.join(self.preference_path, "circuits")
        elif platform.system() == "Linux":  # Else assume this is linux
            self.preference_path = os.path.join(self.user_home_dir, ".config", "logical")
            self.save_path = os.path.join(self.preference_path, "circuits")
        else:  # If on Mac or some other OS, then just write settings to home directory
            self.preference_path = os.path.join(self.user_home_dir, "logical")
            self.save_path = os.path.join(self.preference_path, "circuits")

        log_msg(INFO, "Preference Path: " + self.preference_path)
        log_msg(INFO, "Circuit Save Path: " + self.save_path)

        old_mask = os.umask(0)
        if not os.path.exists(self.preference_path):
            os.mkdir(self.preference_path, 0o744)
            os.chmod(self.preference_path, 0o744)
        if not os.path.exists(self.save_path):
            os.mkdir(self.save_path, 0o744)
            os.chmod(self.save_path, 0o744)
        os.umask(old_mask)

        self.preference_file_name = os.path.join(self.preference_path, self.preference_file_name)

    def reset_gui(self) -> None:
        """Resets the gui on a significant change, such as a font change"""
        self.clear()
        self.gui_build_all()

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
        for func in self.gates.keys():
            for gate in self.gates[func].get_active_gates():
                if do_overlap((img1_tl_x, img1_tl_y), (img1_br_x, img1_br_y),
                              gate.top_left(), gate.bottom_right()):
                    return True, gate
        return False, None

    def intersects_input_gate(self, event: Event) -> (bool, list[InputTk]):
        """Checks if the coordinate (event.x, event.y) intersects any existing gate(s) on canvas,
        if so, return true and the list of all gates which were intersected (in the case of overlapping gates),
        otherwise return False, []"""
        intersected_gates = []
        intersects = False
        for func in self.gates.keys():
            for item in self.gates[func].get_active_gates():
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

    def click_and_drag_cb(self, event: Event) -> None:
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
            curr_func = self.active_input.get_func()
            self.active_input_pi = PhotoImage(file=self.gates[curr_func]["image_file"])
            self.active_input_img_index = self.screen_icb.create_image(event.x, event.y, image=self.active_input_pi)
            self.active_input.set_id(self.active_input_img_index)

    def delete_cb(self, event: Event) -> None:
        """Delete all selected gates from the canvas"""
        for i in range(len(self.icb_selected_gates)):
            gate = self.icb_selected_gates[i]
            self.gates[gate.get_func()].remove(gate)
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
                log_msg(WARNING, "You can only disconnect two gates!")

    def place_gate(self, event: Event) -> None:
        """Places a gate on the canvas after pressing a gate button"""
        if self.icb_is_gate_active and 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            if self.input_gates_intersect(event)[0]:
                return

            self.active_input_pi = PhotoImage(file=self.gates[self.active_input.get_func()]["image_file"])
            inst_num = len(self.gates[self.active_input.get_func()].get_active_gates()) + 1

            if is_clock(self.active_input):
                self.gates[self.active_input.get_func()].add_active_gate(ClockTk(update_rate=self.default_update_rate,
                                                                                 gate_info_repo=self.gates,
                                                                                 label=self.active_input.get_label() +
                                                                                       str(inst_num),
                                                                                 canvas=self.screen_icb,
                                                                                 center=(event.x, event.y)))
                self.selected_timer = self.gates[self.active_input.get_func()].get_active_gates()[-1]
                self.timer_prompt()  # Configure this new timer on placement
            elif isinstance(self.active_input, InputTk):
                self.gates[self.active_input.get_func()].add_active_gate(InputTk(self.active_input.get_func(),
                                                                                 gate_info_repo=self.gates,
                                                                                 label=self.active_input.get_label() +
                                                                                 str(inst_num),
                                                                                 canvas=self.screen_icb,
                                                                                 center=(event.x, event.y),
                                                                                 out=self.active_input.out,
                                                                                 # If output gate, make it smaller to fit with border
                                                                                 dims=(self.img_width - 5,
                                                                                       self.img_height - 5) if
                                                                                 is_output_gate(self.active_input) else
                                                                                 (0, 0)))
            last_input = self.gates[self.active_input.get_func()].get_active_gates()[-1]
            self.active_input_img_index = last_input.get_id()
            # Add checkbox entry to entry menu if gate is a power source
            if is_power_gate(last_input):
                self.is_edit_table.add_entry(last_input)

    def save(self) -> None:
        """Save the current circuit to a file, if this is the first save, prompt for file name"""
        if self.filename == "":  # If the program has not been saved before, prompt for filename
            log_msg(INFO, "No save file has been specified.")
            self.save_as()

        log_msg(INFO, "Saving diagram to: " + self.filename)
        with open(self.filename, 'w') as save_file:
            self.deselect_active_gates()
            self.reset()
            gates = []

            for func in self.gates.keys():  # Create one list out of all gates
                for gate in self.gates[func].get_active_gates():
                    gates.append(gate)

            for idx, gate in enumerate(gates):
                # For each gate, write the gate and its enumeration, which is used as its id
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
                            in_fmt += str(other_gate[1]) + "|"
                            break
                in_fmt = in_fmt[:-1] + ']'

                # For every output, find the gate in the master list and add its id number to the list,
                # to reconstruct later
                out_fmt = "[" if len(out_gates) > 0 else "[]"
                for out_gate in out_gates:
                    for other_gate in gates:
                        if other_gate[0] == out_gate:
                            out_fmt += str(other_gate[1]) + "|"
                            break
                out_fmt = out_fmt[:-1] + ']'

                print('{0},{1},{2}'.format(cnt, in_fmt, out_fmt), file=save_file)

    def save_as(self):
        """Create save file prompt and set self.filename to this file"""
        # using with statement
        self.filename = fd.asksaveasfilename(initialfile=self.filename, initialdir=self.save_path,
                                             filetypes=[("Circuit Diagram", "*" + self.file_type)])

    def open(self):
        """"Load circuit from file"""
        self.filename = fd.askopenfilename(initialdir=self.save_path,
                                           filetypes=[("Circuit Diagram", "*" + self.file_type)])

        if self.filename == "":
            return

        log_msg(INFO, "Loading diagram: " + os.path.abspath(self.filename))
        with open(self.filename, 'r') as load_file:
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
                gate_func = self.gates[line_list[0]]  # get_logic_func_from_name(line_list[0])
                # Strip parenthesis and space from center str, then split
                gate_inst = len(self.gates[gate_func].get_active_gates()) + 1
                position_x = int(line_list[1].strip("("))
                position_y = int(line_list[2].strip(") "))
                gate_out = int(line_list[3])
                gate_center = (position_x, position_y)
                gate = None
                if gate_func == logic_clock:  # If this input is clock, it has a different format
                    # line_list[3]: Default Value
                    # line_list[4]: Update Rate
                    # line_list[5]: gate number
                    gate = ClockTk(gate_info_repo=self.gates, update_rate=float(line_list[4]),
                                   label="Clock #" + str(gate_inst),
                                   canvas=self.screen_icb, center=gate_center, default_state=int(line_list[5]))
                else:  # Otherwise all the other gates have the same format
                    gate = InputTk(func=gate_func, gate_info_repo=self.gates,
                                   label=capitalize(gate_func.__name__ + " #" + str(gate_inst)),
                                   canvas=self.screen_icb, center=gate_center, out=gate_out,
                                   dims=(95, 45) if gate_func == output else (0, 0))
                    if is_power_gate(gate):
                        self.is_edit_table.add_entry(gate)
                        gate.set_label("Power #" + str(gate_inst))
                gates.append((gate, idx))
                self.gates[gate_func].add_active_gate(gate)

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

        # Destroy Gates
        for func in self.gates.keys():
            for gate in self.gates[func].get_active_gates():
                gate.delete()
            self.gates[func].active_gates = []

        # Reset all reference to gates
        self.icb_is_gate_active = False
        self.set_active_fn_none()
        # Clear Canvas
        self.screen_icb.delete('all')
        self.filename = ""

    def about(self):
        pass

    def help(self) -> None:
        self.help_window = Toplevel(self)
        self.help_window.title("Help")
        self.help_window.resizable(False, False)
        # self.help_window.geometry("800x600")

        self.help_window.wait_visibility()
        self.help_window.grab_set()
        self.help_window.transient(self)

        scrollable_frame = ScrollableFrame(self.help_window, this_font=self.active_font, width=800, height=600)
        scrollable_frame.grid(row=0, column=0, padx=(0, 20), sticky='news')

        # shortcut_labelframe = LabelFrame(scrollable_frame, font=self.active_font, text="Shortcuts")
        # shortcut_labelframe.grid(row=0, column=0, sticky='new')

        desc_labelframe = LabelFrame(scrollable_frame.frame, font=self.active_font, text="Gate Descriptions")
        desc_labelframe.grid(row=1, column=0, sticky='news', padx=(10, 0), pady=(5, 5))

        power_desc = PictureDescription(desc_labelframe, img=self.gates[power]["image"], desc_text=self.gates[power]["desc"],
                                        text_width=30, text_height=6, this_font=self.active_font)
        power_desc.grid(row=0, column=0)

        not_desc = PictureDescription(desc_labelframe, img=self.gates[logic_not]["image"], desc_text=self.gates[logic_not]["desc"],
                                      text_width=30, text_height=6, this_font=self.active_font)
        not_desc.grid(row=0, column=1)

        and_desc = PictureDescription(desc_labelframe, img=self.gates[logic_and]["image"], desc_text=self.gates[logic_and]["desc"],
                                      text_width=30, text_height=6, this_font=self.active_font)
        and_desc.grid(row=1, column=0)

        nand_desc = PictureDescription(desc_labelframe, img=self.gates[logic_nand]["image"], desc_text=self.gates[logic_nand]["desc"],
                                       text_width=30, text_height=6, this_font=self.active_font)
        nand_desc.grid(row=1, column=1)

        or_desc = PictureDescription(desc_labelframe, img=self.gates[logic_or]["image"], desc_text=self.gates[logic_or]["desc"],
                                     text_width=30, text_height=6, this_font=self.active_font)
        or_desc.grid(row=2, column=0)

        xor_desc = PictureDescription(desc_labelframe, img=self.gates[logic_xor]["image"], desc_text=self.gates[logic_xor]["desc"],
                                      text_width=30, text_height=6, this_font=self.active_font)
        xor_desc.grid(row=2, column=1)

        output_desc = PictureDescription(desc_labelframe, img=self.gates[output]["image"], desc_text=self.gates[output]["desc"],
                                         text_width=30, text_height=6, this_font=self.active_font)
        output_desc.grid(row=3, column=0)

        clock_desc = PictureDescription(desc_labelframe, img=self.gates[logic_clock]["image"], desc_text=self.gates[logic_clock]["desc"],
                                        text_width=30, text_height=6, this_font=self.active_font)
        clock_desc.grid(row=3, column=1)

        button_frame = Frame(self.help_window)
        button_frame.grid(row=2, column=0, sticky='news')
        done_button = Button(button_frame, text="Done", font=self.active_font, command=self.close_help)
        done_button.grid(row=0, column=0)

    def close_help(self) -> None:
        # Reset popup state
        self.help_window.grab_release()
        self.help_window.destroy()
        self.help_window.update()

    def pause(self, event: Event):
        """Pauses all clocks"""
        log_msg(INFO, "Pausing Clocks.")
        ClockTk.clocks_paused = True
        for timer in self.gates[logic_clock].get_active_gates():
            timer.pause()

    def play(self, event: Optional[Event] = None):
        """Starts all clocks"""
        log_msg(INFO, "Starting Clocks.")
        ClockTk.clocks_paused = False
        for timer in self.gates[logic_clock].get_active_gates():
            timer.start()

    def reset(self, event: Optional[Event] = None):
        """Resets the clocks in the program"""
        log_msg(INFO, "Resetting Clocks.")
        ClockTk.clocks_paused = True
        for timer in self.gates[logic_clock].get_active_gates():
            timer.stop()

    def toggle_play_pause(self, event: Optional[Event] = None):
        """Toggle the clocks"""
        if not ClockTk.clocks_paused:
            """Pauses all timers"""
            self.pause(event)
        else:
            """Starts all timers"""
            self.play(event)

    def set_active_fn_none(self) -> None:
        """Set when a gate button is clear"""
        self.deselect_active_gates()
        self.icb_is_gate_active = False
        self.screen_icb.delete(self.active_input_img_index)

    def set_active_fn_output(self) -> None:
        self.icb_is_gate_active = True
        self.active_input = InputTk(output, self.gates, label="Output #", canvas=self.screen_icb, out=TRUE)

    def set_active_fn_power(self) -> None:
        self.icb_is_gate_active = True
        self.active_input = InputTk(power, self.gates, label="Power #", canvas=self.screen_icb, out=TRUE)

    def set_active_fn_and(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_and, self.gates, label="And Gate #", canvas=self.screen_icb)

    def set_active_fn_nand(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_nand, self.gates, label="Nand Gate #", canvas=self.screen_icb)

    def set_active_fn_xor(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_xor, self.gates, label="Xor Gate #", canvas=self.screen_icb)

    def set_active_fn_not(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_not, self.gates, label="Not Gate #", canvas=self.screen_icb)

    def set_active_fn_or(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = InputTk(logic_or, self.gates, label="Or Gate #", canvas=self.screen_icb)

    def set_active_fn_clock(self) -> None:
        self.deselect_active_gates()
        self.icb_is_gate_active = True
        self.active_input = ClockTk(self.gates, self.default_update_rate, label="Clock #", canvas=self.screen_icb)

    def gui_build_input_selection_menu(self) -> None:
        """Build the side pane: the power table and gate buttons"""
        self.bordered_frame = Frame(self, background='black', width=self.input_selection_screen_width,
                                    height=self.height)
        self.bordered_frame.grid(row=0, column=1)
        self.bordered_frame.grid_propagate(False)

        self.screen_is = Frame(self.bordered_frame, background='white',
                               width=self.input_selection_screen_width - self.border_width, height=self.height)
        self.screen_is.grid(padx=(self.border_width, 0), sticky="nsew", )
        self.screen_is.grid_propagate(False)

        # Add gate buttons #############################################################################################
        self.is_button_frame = LabelFrame(self.screen_is, bg="white", font=self.active_font, text="Logic Gates")
        self.is_button_frame.grid(column=0, row=0, sticky='w', padx=(10, 0), pady=(10, 0))
        # self.is_button_frame.grid_propagate(False)

        for (i, func) in enumerate(self.gates.keys()):
            labeled_button_frame = Frame(self.is_button_frame, background='white')
            labeled_button_frame.grid(column=0, row=i, padx=(0, 5), sticky="e")
            if i == len(self.gates) - 1:
                labeled_button_frame.grid_configure(pady=(0, 5))

            if self.gates[func]["func"] not in (output, power):
                # Strip logic_ from each logic gate name
                label_text = capitalize(self.gates[func]["name"][6:]) + " Gate:"
            else:
                label_text = capitalize(self.gates[func]["name"]) + " Gate:"

            button_label = Label(labeled_button_frame, text=label_text, background='white',
                                 font=reconfig_font(self.active_font, offset=-2, weight="bold"))
            button_label.grid(column=0, row=0, padx=(0, 3), sticky='w')

            is_border_frame = Frame(labeled_button_frame, highlightbackground="black",
                                    highlightthickness=1, bd=0)
            is_border_frame.grid(row=0, column=1, sticky='e')
            is_border_frame.propagate(True)

            is_button = Button(is_border_frame, image=self.gates[func]["image"], bg="white", relief="flat",
                               command=self.gates[func]["callback"])
            is_button.grid(sticky='e')

            self.is_buttons.append((is_button, button_label))

        self.update_idletasks()

        # Add table to this side pane
        self.is_edit_table = CheckbuttonTable(self.screen_is, self.screen_icb, self.active_font, text='Power Gates')
        self.is_edit_table.grid(row=1, column=0, sticky='ns', padx=(10, 0))
        self.is_edit_table.grid_propagate(False)

    def gui_build_icb(self) -> None:
        """Builds the canvas for the gates to exist on and create all the key bindings"""
        self.screen_icb = Canvas(self, width=self.width - self.input_selection_screen_width, height=self.height,
                                 background=self.background_color.get(), highlightthickness=0)
        self.screen_icb.grid(row=0, column=0, sticky="NESW")
        self.screen_icb.grid_propagate(False)
        self.screen_icb.bind('<Motion>', self.motion_cb)
        self.screen_icb.bind('<Button-1>', self.left_click_cb)
        self.screen_icb.bind('<B1-Motion>', self.click_and_drag_cb)
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
        # Force the canvas to stay focused, keybindings only take effect when this widget has focus
        self.screen_icb.focus_force()

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
        self.gui_build_input_selection_menu()
        self.gui_build_icb()

    def gui_reconfig_dimensions(self):
        """Updates the width and height of the application"""
        self.bordered_frame.config(height=self.height)
        self.screen_is.config(height=self.height)
        self.screen_icb.config(width=self.width - self.input_selection_screen_width, height=self.height)
        self.is_edit_table.config_dims(height=self.height - self.is_button_frame.winfo_height() - 30,
                                       width=self.input_selection_screen_width - 30)
        self.geometry(str(self.width) + "x" + str(self.height))

    def toggle_line_colors(self) -> None:
        InputTk.line_colors_on = not InputTk.line_colors_on
        for func in self.gates.keys():
            for gate in self.gates[func].get_active_gates():
                gate.update_line_colors()

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
        # Resolution Preferences #######################################################################################
        res_frame = Frame(self.preference_toplevel)
        res_frame.pack(side=TOP, expand=True, fill=BOTH)
        res_label = Label(res_frame, text=" Set Resolution:", font=self.active_font)
        res_label.pack(side=LEFT, padx=(5, 0), pady=(10, 5))

        self.res_width_var = StringVar(value=str(self.winfo_width()))
        self.res_width_entry = Entry(res_frame, textvariable=self.res_width_var, font=self.active_font, width=4)
        self.res_width_entry.pack(side=LEFT, padx=(5, 0), pady=(0, 0))

        res_sep_label = Label(res_frame, text="x", font=self.active_font)
        res_sep_label.pack(side=LEFT, padx=(5, 5), pady=(0, 0))

        self.res_height_var = StringVar(value=str(self.winfo_height()))
        self.res_height_entry = Entry(res_frame, textvariable=self.res_height_var, font=self.active_font, width=4)
        self.res_height_entry.pack(side=LEFT, padx=(0, 0), pady=(0, 0))
        # Color Preferences ############################################################################################
        color_frame = Frame(self.preference_toplevel)
        color_frame.pack(side=TOP, expand=True, fill=BOTH, padx=(0, 0), pady=(0, 5))

        self.color_labelentry = LabeledEntry(master=color_frame, entry_width=7,
                                             label_text="Canvas color (name or #XXXXXX):",
                                             entry_text=self.background_color.get(), widget_font=self.active_font)
        self.color_labelentry.pack(side=LEFT, padx=(10, 0), pady=(5, 5))
        # Toggle Line Colors ###########################################################################################
        line_colors_frame = Frame(self.preference_toplevel)
        line_colors_frame.pack(side=TOP, expand=True, fill=BOTH, padx=(12, 0), pady=(0, 5))

        line_colors_label = Label(line_colors_frame, text="Enable Line Colors:", font=self.active_font)
        line_colors_label.pack(side=LEFT)

        self.line_colors_checkbox = Checkbutton(line_colors_frame,
                                                command=self.toggle_line_colors, font=self.active_font)
        self.line_colors_checkbox.select()
        self.line_colors_checkbox.pack(side=LEFT)
        # Font Preferences #############################################################################################
        font_frame = Frame(self.preference_toplevel)
        font_frame.pack(side=TOP, padx=(15, 15), pady=(0, 5))
        # Font Family ##################################################################################################
        font_family_frame = Frame(font_frame)
        font_family_frame.pack(side=LEFT)
        font_family_label = Label(font_family_frame, text="Font Family", font=self.active_font)
        font_family_label.pack(side=TOP)
        self.font_family_listbox = Listbox(font_family_frame, font=self.active_font, selectmode=SINGLE,
                                           exportselection=False)

        for family in self.font_families:
            self.font_family_listbox.insert(END, family)

        self.font_family_listbox.pack(side=LEFT, fill=BOTH)

        font_family_scrollbar = Scrollbar(font_family_frame)
        font_family_scrollbar.pack(side=RIGHT, fill=BOTH)

        self.font_family_listbox.config(yscrollcommand=font_family_scrollbar.set)
        font_family_scrollbar.config(command=self.font_family_listbox.yview)
        # Font Size ####################################################################################################
        font_sizes = ['10', '11', '12', '13', '14']
        font_size_frame = Frame(font_frame)
        font_size_frame.pack(side=RIGHT, fill=BOTH)
        font_size_label = Label(font_size_frame, text="Font Size", font=self.active_font)
        font_size_label.pack(side=TOP)
        self.font_size_listbox = Listbox(font_size_frame, font=self.active_font, height=len(font_sizes),
                                         selectmode=SINGLE, exportselection=False)

        for font_size in font_sizes:
            self.font_size_listbox.insert(END, font_size)

        self.font_size_listbox.pack(side=LEFT, expand=True, fill=BOTH)
        font_size_scrollbar = Scrollbar(font_size_frame)
        font_size_scrollbar.pack(side=RIGHT, fill=BOTH)

        self.font_size_listbox.config(yscrollcommand=font_size_scrollbar.set)
        font_size_scrollbar.config(command=self.font_size_listbox.yview)
        ################################################################################################################
        preference_button_frame = Frame(self.preference_toplevel)
        preference_button_frame.pack(side=BOTTOM, expand=True, fill=BOTH, pady=(15, 5))
        preference_done_button = Button(preference_button_frame, text="Done",
                                        command=self.close_preference_prompt,
                                        font=self.active_font)
        # self.preference_done_button.grid(row=3)
        preference_done_button.pack()
        self.wait_window(self.preference_toplevel)

    def close_preference_prompt(self) -> None:
        # Update settings...
        width, height = int(self.res_width_var.get()), int(self.res_height_var.get())
        if width >= 800 and height >= 600:
            self.width = int(self.res_width_entry.get())
            self.height = int(self.res_height_entry.get())
            self.gui_reconfig_dimensions()
        else:
            log_msg(WARNING, "Resolution must be at least 800x600")

        self.background_color = self.color_labelentry
        self.screen_icb.config(background=self.background_color.get())

        # Set active font
        # If a font family was selected by the list box, get as a list and use as an index to get the font family
        family = self.font_family_listbox.curselection()
        if family != ():
            self.font_family = self.font_family_listbox.get(family[0])

        size = self.font_size_listbox.curselection()
        if size != ():
            self.font_size = int(self.font_size_listbox.get(size[0]))

        if family != () or size != ():  # If either font family/size change, update app font and rebuild app
            self.update_font(self.font_family, self.font_size)

        self.save_preferences()

        # Reset popup state
        self.preference_toplevel.grab_release()
        self.preference_toplevel.destroy()
        self.preference_toplevel.update()

    def save_preferences(self) -> None:
        doc = tomlkit.document()
        settings = tomlkit.table()
        settings.add("Width", self.width)
        settings.add("Height", self.height)
        settings.add("Background", self.background_color.get())
        settings.add("Font", [self.active_font["family"], self.active_font["size"],
                              self.active_font["weight"], self.active_font["slant"]])
        settings.add("Colors", InputTk.line_colors_on)
        doc["Settings"] = settings
        with open(self.preference_file_name, mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(doc, fp)
            log_msg(INFO, "Saved settings to: " + self.preference_file_name)

    def load_preferences(self) -> None:
        if not os.path.exists(self.preference_file_name):
            return

        with open(self.preference_file_name, mode="rt", encoding="utf-8") as fp:
            document = tomlkit.load(fp)
            self.width = document["Settings"]["Width"]
            self.height = document["Settings"]["Height"]
            self.background_color.set(document["Settings"]["Background"])
            InputTk.line_colors_on = document["Settings"]["Colors"]
            fonts_attrs = document["Settings"]["Font"]
            self.active_font = font.Font(family=fonts_attrs[0], size=fonts_attrs[1],
                                         weight=fonts_attrs[2], slant=fonts_attrs[3])

            self.gui_reconfig_dimensions()
            self.screen_icb.config(background=self.background_color.get())
            self.update_font(fonts_attrs[0], fonts_attrs[1])
            log_msg(INFO, "Loaded settings from: " + self.preference_file_name)

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

        timer_labelframe = LabelFrame(self.timer_popup, text="Set Clock Properties", font=self.font_top)
        timer_labelframe.grid(padx=(5, 5), pady=(0, 5))

        entry_frame = Frame(timer_labelframe)
        entry_frame.grid(row=0, column=0, padx=(10, 10), pady=(5, 10))

        timer_entry_label = Label(entry_frame, text="Timer Update Rate (seconds):", font=self.active_font)
        timer_entry_label.grid(row=0, column=0, padx=(0, 5), pady=(0, 0), sticky=W)
        self.timer_entry = Entry(entry_frame, textvariable=self.timer_entry_strvar, width=5, font=self.active_font)
        self.timer_entry.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        cb_frame = Frame(timer_labelframe)
        cb_frame.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))
        timer_state_label = Label(cb_frame, text="Set Timer State (Default On):", font=self.active_font)
        timer_state_label.grid(row=0, column=0, padx=(0, 5))
        self.timer_state_cb = Checkbutton(cb_frame, variable=self.timer_state_intvar, font=self.active_font)
        self.timer_state_cb.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        timer_done_button = Button(timer_labelframe, text="Done", command=self.close_timer_prompt,
                                   font=self.active_font)
        timer_done_button.grid(row=2, column=0)
        self.wait_window(self.timer_popup)

    def close_timer_prompt(self):
        # Update timer settings
        self.selected_timer.set_rate(float(self.timer_entry_strvar.get()))
        self.selected_timer.set_output(self.timer_state_intvar.get())
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

        prompt_label = Label(self.screen_exit_prompt, text=msg, font=self.active_font)
        prompt_label.pack(padx=(15, 15), pady=(15, 15))

        prompt_button_confirm = Button(self.screen_exit_prompt, text="Yes", command=callback,
                                       font=self.active_font)
        prompt_button_confirm.pack(side=LEFT, padx=(55, 5), pady=(10, 20))

        prompt_button_cancel = Button(self.screen_exit_prompt, text="Cancel", command=self.close_exit_prompt,
                                      font=self.active_font)
        prompt_button_cancel.pack(side=RIGHT, padx=(5, 55), pady=(10, 20))
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
        self.load_preferences()
        self.mainloop()


if __name__ == "__main__":
    app = Application()
    app.run()

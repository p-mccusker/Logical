########################################################################################################################
# File: circuit.py
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
from tkinter import filedialog as fd
import sys
import os
from tk_widgets import *
import tomlkit


def capitalize(string: str) -> str:

    return string[0].upper() + string[1:]


def point_in_rect(x, y, tl: (int, int), br: (int, int)):
    """Return True if x, """
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


class Application(Tk):
    img_width = 100
    img_height = 50
    max_selectable_gates = 100
    border_width = 3  # Width of border separating canvas from the right pane
    input_selection_screen_width = None  # Width of the right pane
    bg_colors = ["white", "black", "red", "green", "blue", "cyan", "yellow", "magenta"]
    # Fonts #####################
    font_family = "Helvetica"
    font_size = 12
    active_font = None
    font_top = None
    # Preference Dirs ###########
    user_home_dir = os.path.expanduser('~')
    preference_file_name = "logical.toml"

    def __init__(self, width: int = 1600, height: int = 900):
        super().__init__()

        if os.name == "nt":  # If current platform is Windows...
            self.preference_path = os.path.join(self.user_home_dir, "Documents", "logical")
            self.save_path = os.path.join(self.preference_path, "circuits")
        else:  # Else assume this is linux
            self.preference_path = os.path.join(self.user_home_dir, ".config", "logical")
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

        # Parse command line arguments
        for i, arg in enumerate(sys.argv):
            if arg == '-w':
                width = int(sys.argv[i+1])
                if width < 800:
                    log_msg(ERROR, "Width must be >= 800", ValueError)

            if arg == '-h':
                height = int(sys.argv[i + 1])
                if height < 600:
                    log_msg(ERROR, sys.argv[i + 1], ": height must be an integer >", ValueError)

        self.width = width
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

        # Dictionary to hold the input gates, where the gate type is the key and the value is the list of gates
        self.inputs = {}
        for func in INPUT_GATES:
            self.inputs[func] = []

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
        self.tmp_filename = "tmp" + self.file_type

        #############################
        # Preference Vars ###########
        self.font_families = list(font.families())

        #############################

    def update_font(self, family: str, size: int) -> None:
        print("update_font")
        self.font_family = family
        self.font_size = size
        self.active_font = font.Font(family=self.font_family, size=self.font_size, weight=font.NORMAL,
                                     slant=font.ROMAN)
        self.font_top = font.Font(family=self.font_family, size=self.font_size - 1, weight=font.NORMAL,
                                  slant=font.ROMAN)
        print(self.active_font)

        self.save_temp()
        self.reset_gui()
        self.open_temp()

    def reset_gui(self) -> None:
        self.clear()

        self.screen_is.grid_forget()
        self.screen_is.update()

        self.is_edit_table.clear()
        self.is_edit_table.grid_forget()
        self.is_edit_table.destroy()
        self.is_edit_table.update()

        self.bordered_frame.grid_forget()
        self.bordered_frame.update()

        self.screen_is.grid_forget()
        self.screen_is.update()

        self.is_button_frame.grid_forget()
        self.is_button_frame.update()

        for (btn, frm) in self.is_buttons:
            frm.grid_forget()
            frm.update()
            btn.grid_forget()
            btn.update()

        self.reset(None)
        self.update()

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

        print("Saving:", self.filename)
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
            # save_file.close()

    def save_as(self):
        """Create save file prompt and set self.filename to this file"""
        # using with statement
        self.filename = fd.asksaveasfilename(initialfile=self.filename,
                                             filetypes=[("Circuit Diagram", "*" + self.file_type)])

    def save_temp(self):
        """Writes the current configuration to a file when performing an action that requires a rebuild of the app,
        such as changing the current font"""
        org_save_filename = self.filename
        self.filename = "tmp" + self.file_type
        self.save()
        self.filename = org_save_filename

    def open(self):
        """"Load circuit from file"""
        open_filename = ""  # If open called from menu, ask for prompt, if it has been called to open a temp file,
        # use that name
        if self.open_filename == "":
            self.filename = fd.askopenfilename(filetypes=[("Circuit Diagram", "*" + self.file_type)])
            open_filename = self.filename
        else:
            open_filename = self.open_filename

        if open_filename == "":
            return

        load_file = open(open_filename, 'r')
        if load_file is None:
            raise FileNotFoundError("Unable to open: " + open_filename)

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
                gate = InputTk(func=gate_func, label=capitalize(gate_func.__name__ + " #" + str(gate_inst)), canvas=self.screen_icb,
                               center=gate_center, out=gate_out, dims=(95, 45) if gate_func == output else (0, 0))
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

        load_file.close()

    def open_temp(self):
        """Loads the temp file saved on program rebuild and deletes it"""
        print("open_temp")
        self.open_filename = "tmp" + self.file_type
        self.open()

        os.remove(self.open_filename)
        self.open_filename = ""

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
        ClockTk.clocks_paused = True
        for clock in self.inputs[logic_clock]:
            clock.pause()

    def play(self, event: Optional[Event] = None):
        """Starts all clocks"""
        print("play")
        ClockTk.clocks_paused = False
        for clock in self.inputs[logic_clock]:
            clock.start()

    def reset(self, event: Optional[Event] = None):
        """Resets the clocks in the program"""
        ClockTk.clocks_paused = True
        for clock in self.inputs[logic_clock]:
            clock.stop()

    def toggle_play_pause(self, event: Optional[Event] = None):
        """Toggle the clocks"""
        if not ClockTk.clocks_paused:
            """Pauses all timers"""
            ClockTk.clocks_paused = True
            for clock in self.inputs[logic_clock]:
                clock.pause()
        else:
            """Starts all timers"""
            ClockTk.clocks_paused = False
            for clock in self.inputs[logic_clock]:
                clock.start()

    def set_active_fn_none(self) -> None:
        """Set when a gate button is clear"""
        self.deselect_active_gates()
        self.icb_is_gate_active = False
        self.screen_icb.delete(self.active_input_img_index)

    def set_active_fn_output(self) -> None:
        self.icb_is_gate_active = True
        self.active_input = InputTk(output, label="Output #", canvas=self.screen_icb, out=TRUE)

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
        print(self.width, self.input_selection_screen_width, self.width - self.input_selection_screen_width)
        self.screen_icb = Canvas(self, width=self.width - self.input_selection_screen_width, height=self.height,
                                 background=self.background_color.get(), highlightthickness=0)
        self.screen_icb.grid(row=0, column=0, sticky="NESW")
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

    def gui_build_input_selection_menu(self) -> None:
        """Build the side pane: the power table and gate buttons"""
        self.bordered_frame = Frame(self, background='black',  height=self.height)
        self.bordered_frame.grid(row=0, column=1, sticky='nsew')
        self.bordered_frame.grid_propagate(True)

        self.screen_is = Frame(self.bordered_frame, background='red', )
        self.screen_is.grid(row=0, column=0, padx=(self.border_width, 0), sticky="nsew",)
        self.screen_is.grid_propagate(True)

        # Add table to this side pane
        table_padding = {"padx": (10, 10), "pady": (5, 0)}
        self.is_edit_table = CheckbuttonTable(self.screen_is, "Edit Inputs", self.screen_icb,
                                             this_font=self.active_font,
                                             background="white")
                                             # width=self.input_selection_screen_width - self.border_width)
        self.is_edit_table.grid(column=0, row=0, sticky="nws", **table_padding)
        # Add gate buttons #############################################################################################
        self.is_button_frame = Frame(self.screen_is, bg="cyan", )
        self.is_button_frame.grid(column=0, row=1, sticky='ns', padx=(10, 10), pady=(10, 0))
        # self.is_button_frame.grid_propagate(False)

        # Create list of all function that are to be bound to buttons
        logic_funcs_cbs = [self.set_active_fn_output, self.set_active_fn_power, self.set_active_fn_not,
                           self.set_active_fn_and, self.set_active_fn_nand, self.set_active_fn_or,
                           self.set_active_fn_xor, self.set_active_fn_clock]

        for i in range(len(INPUT_GATES)):
            image = PhotoImage(file=get_input_img_file(INPUT_GATES[i]))
            self.imgs[i] = image
            self.is_border_frame = Frame(self.is_button_frame, highlightbackground="black",
                                         highlightthickness=1, bd=0)
            # self.is_border_frame.propagate(False)
            self.is_border_frame.grid(row=i, sticky="ns", )#padx=(15, 0))

            self.is_button = Button(self.is_border_frame, image=self.imgs[i], bg="white", relief="flat",
                                    command=logic_funcs_cbs[i])
            self.is_button.grid(sticky='ns')

            self.is_buttons.append((self.is_button, self.is_border_frame))

        self.update_idletasks()
        self.input_selection_screen_width = self.bordered_frame.winfo_reqwidth()

        print(self.bordered_frame.winfo_reqwidth(), self.bordered_frame.winfo_reqheight(),
              self.bordered_frame.winfo_width(), self.bordered_frame.winfo_height())

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
        self.screen_is.config(height=self.height)
        self.screen_icb.config(width=self.width-self.input_selection_screen_width, height=self.height)
        self.geometry(str(self.width) + "x" + str(self.height))

    def toggle_line_colors(self) -> None:
        InputTk.line_colors_on = not InputTk.line_colors_on
        for func in self.inputs.keys():
            for gate in self.inputs[func]:
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
        # Needs work

        width, height = int(self.res_width_var.get()), int(self.res_height_var.get())
        if width >= 800 and height >= 600:
            self.width = int(self.res_width_entry.get())
            self.height = int(self.res_height_entry.get())
            self.gui_reconfig_dimensions()
        else:
            print("[WARNING]: Resolution must be at least 800x600")

        self.background_color = self.color_labelentry
        self.screen_icb.config(background=self.background_color.get())

        # Set active font
        # If a font family was selected by the list box, get as a list and use as an index to get the font family
        family = self.font_family_listbox.curselection()
        print(family)
        if family != ():
            self.font_family = self.font_family_listbox.get(family[0])

        size = self.font_size_listbox.curselection()
        print(family, size)
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
        settings.add("Font", [self.active_font.cget("family"), self.active_font.cget("size")])
                              # self.active_font.cget("weight"), self.active_font.cget("slant")])
        settings.add("Colors", InputTk.line_colors_on)
        doc["Settings"] = settings
        with open(os.path.join(self.preference_path, self.preference_file_name), mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(doc, fp)
            log_msg(INFO, "Saved settings to: " + os.path.join(self.preference_path, self.preference_file_name))

    def load_preferences(self) -> None:
        load_file = os.path.join(self.preference_path, self.preference_file_name)
        if not os.path.exists(load_file):
            return

        with open(os.path.join(self.preference_path, self.preference_file_name), mode="rt", encoding="utf-8") as fp:
            document = tomlkit.load(fp)
            self.width = document["Settings"]["Width"]
            self.height = document["Settings"]["Height"]
            self.background_color.set(document["Settings"]["Background"])
            InputTk.line_colors_on = document["Settings"]["Colors"]
            fonts_attrs = document["Settings"]["Font"]

            self.gui_reconfig_dimensions()
            self.screen_icb.config(background=self.background_color.get())
            self.update_font(fonts_attrs[0], fonts_attrs[1])


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

        self.timer_entry_label = Label(entry_frame, text="Timer Update Rate (seconds):", font=self.active_font)
        self.timer_entry_label.grid(row=0, column=0, padx=(0, 5), pady=(0, 0), sticky=W)
        self.timer_entry = Entry(entry_frame, textvariable=self.timer_entry_strvar, width=5, font=self.active_font)
        self.timer_entry.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        cb_frame = Frame(self.timer_labelframe)
        cb_frame.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))
        self.timer_state_label = Label(cb_frame, text="Set Timer State (Default On):", font=self.active_font)
        self.timer_state_label.grid(row=0, column=0, padx=(0, 5))
        self.timer_state_cb = Checkbutton(cb_frame, variable=self.timer_state_intvar, font=self.active_font)
        self.timer_state_cb.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        self.timer_done_button = Button(self.timer_labelframe, text="Done", command=self.close_timer_prompt,
                                        font=self.active_font)
        self.timer_done_button.grid(row=2, column=0)
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

        self.prompt_label = Label(self.screen_exit_prompt, text=msg, font=self.active_font)
        self.prompt_label.pack(padx=(15, 15), pady=(15, 15))

        self.prompt_button_confirm = Button(self.screen_exit_prompt, text="Yes", command=callback,
                                            font=self.active_font)
        self.prompt_button_confirm.pack(side=LEFT, padx=(55, 5), pady=(10, 20))

        self.prompt_button_cancel = Button(self.screen_exit_prompt, text="Cancel", command=self.close_exit_prompt,
                                           font=self.active_font)
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
        # self.load_preferences()
        self.mainloop()


if __name__ == "__main__":
    app = Application()
    app.run()


"""    def gui_build_input_selection_menu(self) -> None:
       Build the side pane: the power table and gate buttons
        self.bordered_frame = Frame(self, background='black', width=self.input_selection_screen_width, height=self.height)
        self.bordered_frame.grid(row=0, column=1)
        self.bordered_frame.grid_propagate(True)

        self.screen_is = Frame(self.bordered_frame, background='white',
                               width=self.input_selection_screen_width - self.border_width, height=self.height)
        self.screen_is.grid(padx=(self.border_width, 0), sticky="nse",)
        self.screen_is.grid_propagate(False)

        self.geometry(str(self.width + self.input_selection_screen_width) + "x" + str(self.height))

        # Add table to this side pane
        table_padding = {"padx": (10, 0), "pady": (5, 0)}
        self.is_edit_table = CheckbuttonTable(self.screen_is, "Edit Inputs", self.screen_icb,
                                             this_font=self.active_font,
                                             background="white")
                                             # width=self.input_selection_screen_width - self.border_width)
        self.is_edit_table.grid(column=0, row=0, sticky="ns", **table_padding)
        # Add gate buttons #############################################################################################
        self.is_button_frame = Frame(self.screen_is, bg="white", )
        self.is_button_frame.grid(column=0, row=1, sticky='nesw', padx=(20, 0), pady=(10, 0))
        # self.is_button_frame.grid_propagate(False)

        # Create list of all function that are to be bound to buttons
        logic_funcs_cbs = [self.set_active_fn_output, self.set_active_fn_power, self.set_active_fn_not,
                           self.set_active_fn_and, self.set_active_fn_nand, self.set_active_fn_or,
                           self.set_active_fn_xor, self.set_active_fn_clock]

        for i in range(len(INPUT_GATES)):
            image = PhotoImage(file=get_input_img_file(INPUT_GATES[i]))
            self.imgs[i] = image
            self.is_border_frame = Frame(self.is_button_frame, highlightbackground="black",
                                         highlightthickness=1, bd=0)
            # self.is_border_frame.propagate(False)
            self.is_border_frame.grid(row=i, sticky="ns", )#padx=(15, 0))

            self.is_button = Button(self.is_border_frame, image=self.imgs[i], bg="white", relief="flat",
                                    command=logic_funcs_cbs[i])
            self.is_button.grid(sticky='ns')

            self.is_buttons.append((self.is_button, self.is_border_frame))
"""
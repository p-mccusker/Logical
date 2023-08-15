########################################################################################################################
# File: logical.py
# Author: Peter McCusker
# License:
# Date: 01/04/2023
# Description:
########################################################################################################################
# TODO:
#   - Scrolling/Resizing for canvas
#   - Zoom In/Out
#   - Proper resizing of side pane on font changes
########################################################################################################################
from enum import *
import tomlkit

from tk_widgets import *
from graphical_gate import *


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


class CanvasWidgets:
    def __init__(self):
        self.screen_icb = None  # Canvas gates are placed on
        self.icb_menubar = None  # Top Menu (File, Edit, Help...)
        self.icb_is_gate_active = False  # If True, shows input gate as cursor is dragged around
        self.icb_selected_gates = []  # Holds references to all currently selected gates when performing operations
        self.icb_click_drag_gate = None  # The gate currently being moved by the mouse


class InputSelectionWidgets:
    def __init__(self):
        self.bordered_frame = None  # Border Frame to separate canvas and the right pane
        self.screen_is = None  # Separate Window to select which gate input to place
        self.is_buttons = {}  # Holds the buttons for each gate
        self.is_edit_table = None  # Table to toggle inputs on/off
        self.is_button_frame = None  # LabelFrame to hold the buttons and their labels


class TimerWidgets:
    def __init__(self, default_update_rate: int):
        self.timer_popup = None  # Toplevel popup window for window
        self.selected_timer = None  # The timer that is currently being modified
        self.timer_state_cb = None  # Checkbox to toggle the timer's default state
        self.timer_state_intvar = IntVar(value=TRUE)  # Value of the default state checkbox
        self.timer_entry = None  # Entry for timer toggle rate
        self.timer_entry_strvar = StringVar(value=str(default_update_rate))  # Value of the timer update rate


class FileWidgets:
    def __init__(self):
        self.filename = ""
        self.file_separator = "<--CONNECTIONS-->"
        self.file_type = ".cir"
        self.open_filename = ""
        self.preference_path = ""
        self.save_path = ""
        self.tmp_save_filename = "tmp" + self.filename


class PreferenceWidgets:
    def __init__(self):
        self.preference_toplevel = None
        self.res_width_var = None
        self.res_width_entry = None
        self.res_height_var = None
        self.res_height_entry = None
        self.color_labelentry = None
        self.line_colors_checkbox = None
        self.font_family_listbox = None
        self.font_size_listbox = None
        self.background_color = StringVar(value="white")
        self.font_families = [*set(list(families()))]
        self.font_families.sort()
        self.font_family = None


class CustomCircuitWidgets:
    def __init__(self, circuit_action_width: int):
        self.screen_circuit = None
        self.circuit_frame = None
        self.circuit_pi = None
        self.circuit_buttons = []
        self.circuit_button = None
        self.circuit_border_frame = None
        self.custom_circuit_button = None
        self.custom_circuit_pis = []
        self.new_circuit_pi = None
        self.new_circuit_button = None
        self.circuit_input_lbframe = None
        self.circuit_output_lbframe = None
        self.active_circuit = None
        self.circuits = []
        self.circuit_mode_gates = []
        self.active_circuit_input_gate = None
        self.active_circuit_output_gate = None
        self.circuit_action_width = circuit_action_width
        self.circuit_action_frame = None
        self.circuit_prompt = None
        self.circuit_io_window = None
        self.radio_vars = None
        self.circuit_context_menu = None
        self.circuit_inputs_var = None
        self.circuit_outputs_var = None
        self.circuit_name_entry = None
        self.circuit_image_entry = None
        self.cir_inp_names = None
        self.cir_out_names = None
        self.circuit_image_entry = None
        self.cir_labelframe = None
        self.circuit_context_in_index = -1
        self.circuit_context_out_index = -1
        self.circuit_scrollbar_height = 13


class HelpWindowWidgets:
    def __init__(self):
        self.help_window = None


class ApplicationModes(Enum):
    REGULAR = 0
    CUSTOM_CIRCUIT = 1


class Application(Tk):
    img_width = 75
    img_height = 50
    max_selectable_gates = 100
    border_width = 3  # Width of border separating canvas from the right pane
    input_selection_screen_width = 225  # Width of the right pane
    circuit_screen_height = 130
    # Fonts #####################
    font_family = "Helvetica"
    font_size = 12
    active_font = None
    font_top = None
    # Preference Dirs ###########
    user_home_dir = os.path.expanduser('~')
    preference_file_name = "logical.toml"
    # Application Modes #########
    mode = ApplicationModes.REGULAR
    min_win_height = 600
    min_win_width = 800

    def __init__(self, width: int = 1280, height: int = 720):
        super().__init__()
        # Parse command line arguments
        for i, arg in enumerate(sys.argv):
            if arg == '-w':
                width = int(sys.argv[i + 1])
                if width < 800:
                    log_msg(ERROR, sys.argv[i + 1] + "Width must be >= 800", ValueError)

            if arg == '-h':
                height = int(sys.argv[i + 1])
                if height < 600:
                    log_msg(ERROR, sys.argv[i + 1] + ": Height must be >= 600", ValueError)

        self.width = width
        self.height = height
        self.x = self.width / 2
        self.y = self.height / 2
        self.icon = PhotoImage(file=join_folder_file(IMG_FOLDER, "icon.png"))

        # List to hold references to the Photoimages of the input gates so that Tkinter doesn't garbage collect
        # prematurely
        self.imgs = []
        # Dictionary to hold the input gates, where the gate type is the key and the value is the list of gates
        self.gates = GatesInfoRepo()
        self.build_gate_repo()

        if platform.system() == "Windows":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)

        self.default_update_rate = 2  # Default Update for a new clock in seconds, default to 2s

        self.active_input = None  # The input object to be placed when the user clicks the mouse
        self.active_input_pi = None  # Photoimage for active gate
        self.active_input_pi_fn = ""
        self.active_input_img_index = 0  # Canvas image index of active gate
        # Fonts #####################
        self.active_font = Font(family=Application.font_family, size=Application.font_size, weight=NORMAL,
                                slant=ROMAN)
        self.font_top = Font(family=Application.font_family, size=Application.font_size - 1, weight=NORMAL,
                             slant=ROMAN)
        #############################
        # ICB Widgets ###############
        self.widgets_canvas = CanvasWidgets()
        #############################
        # Prompt Widgets ############
        self.screen_exit_prompt = None  # Toplevel popup window for prompt
        #############################
        # Input Selection Widgets ###
        self.widgets_input_selection = InputSelectionWidgets()
        #############################
        # Custom Circuit Widgets ####
        self.widgets_custom_circuit = CustomCircuitWidgets(circuit_action_width=175)
        #############################
        # Timer Window Widgets ######
        self.widgets_timer = TimerWidgets(self.default_update_rate)
        #############################
        # Saving/Loading Vars #######
        self.widgets_file = FileWidgets()
        #############################
        # Preference Vars ###########
        self.widgets_preferences = PreferenceWidgets()
        #############################
        # Help Vars #################
        self.help_window = None
        #############################
        self.title("Logical")
        self.geometry(str(self.width) + "x" + str(self.height))
        self.minsize(self.min_win_width, self.min_win_height)
        # self.resizable(False, False)
        self.config(background=self.widgets_preferences.background_color.get())
        self.iconphoto(True, self.icon)
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.init_file_paths()

    def build_gate_repo(self):
        """Compiles repository for gates, the active ones, their names, and descriptions.  If adding new logic gates,
        register them here"""
        self.gates.register_gate(power, name=power.__name__,
                                 desc="This power source is either powered or not. It takes no inputs.",
                                 callback=FunctionCallback(self.set_active_logic_fn, power),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "power.png"))
        self.gates.register_gate(logic_not, name=logic_not.__name__,
                                 desc="The NOT gate inverts what it receives as input. It requires one input.",
                                 callback=FunctionCallback(self.set_active_logic_fn, logic_not),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "not.png"))
        self.gates.register_gate(logic_and, name=logic_and.__name__,
                                 desc="The AND gate outputs power only if all of its inputs are powered as well. "
                                      "It requires at least two inputs.",
                                 callback=FunctionCallback(self.set_active_logic_fn, logic_and),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "and.png"))
        self.gates.register_gate(logic_nand, name=logic_nand.__name__,
                                 desc="The NAND gate outputs power if not every input is powered. "
                                      "It requires at least two inputs.",
                                 callback=FunctionCallback(self.set_active_logic_fn, logic_nand),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "nand.png"))
        self.gates.register_gate(logic_or, name=logic_or.__name__,
                                 desc="The OR gate outputs power if at least one input is powered. "
                                      "It requires at least two inputs.",
                                 callback=FunctionCallback(self.set_active_logic_fn, logic_or),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "or.png"))
        self.gates.register_gate(logic_xor, name=logic_xor.__name__,
                                 desc="The XOR gate outputs power if at least one, but not all, inputs are powered. "
                                      "It requires at least two inputs",
                                 callback=FunctionCallback(self.set_active_logic_fn, logic_xor),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "xor.png"))
        self.gates.register_gate(output, name=output.__name__,
                                 desc="The output gate has the same output as its input. This gate requires one input "
                                      "and has no outputs.",
                                 callback=FunctionCallback(self.set_active_logic_fn, output),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "output.png"))
        self.gates.register_gate(logic_clock, name=logic_clock.__name__,
                                 desc="This clock turns on/off at a constant rate. "
                                      "It has no inputs.",
                                 callback=FunctionCallback(self.set_active_logic_fn, logic_clock),
                                 image_file=join_folder_file(GATE_IMG_FOLDER, "clock.png"))

    def update_font(self, family: str, size: int) -> None:
        """Updates font across all widgets"""
        self.font_family = family
        self.font_size = size
        self.active_font = Font(family=self.font_family, size=self.font_size, weight=NORMAL,
                                slant=ROMAN)
        self.font_top = Font(family=self.font_family, size=self.font_size - 1, weight=NORMAL,
                             slant=ROMAN)

        self.gui_build_top_menu()
        is_wid = self.widgets_input_selection

        is_wid.is_edit_table.set_font(self.active_font)
        is_wid.is_edit_table.set_focus_widget(self.widgets_canvas.screen_icb)
        is_wid.is_button_frame.config(font=self.active_font)
        for func in is_wid.is_buttons.keys():
            (btn, label) = is_wid.is_buttons[func]
            label.config(font=reconfig_font(self.active_font, offset=-2, weight='bold'))

        cir_wid = self.widgets_custom_circuit
        cir_wid.new_circuit_button.set_font(self.active_font)
        for labeled_button in cir_wid.circuit_buttons:
            labeled_button.set_font(self.active_font)

        for labeled_button in cir_wid.circuit_buttons:
            labeled_button.set_font(self.active_font)

        for circuit in cir_wid.circuits:
            for placed_circuit in self.gates[circuit.get_label()].get_active_gates():
                placed_circuit.set_font(self.active_font)

    def init_file_paths(self) -> None:
        """Creates filesystem directory for Logical"""
        file_wid = self.widgets_file
        if platform.system() == "Windows":  # If current platform is Windows...
            file_wid.preference_path = os.path.join(self.user_home_dir, "logical")
            file_wid.save_path = os.path.join(file_wid.preference_path, "circuits")
        elif platform.system() == "Linux":  # Else assume this is linux
            file_wid.preference_path = os.path.join(self.user_home_dir, ".config", "logical")
            file_wid.save_path = os.path.join(file_wid.preference_path, "circuits")
        else:  # If on Mac or some other OS, then just write settings to directory in user home
            file_wid.preference_path = os.path.join(self.user_home_dir, "logical")
            file_wid.save_path = os.path.join(file_wid.preference_path, "circuits")

        log_msg(INFO, "Preference Path: " + file_wid.preference_path)
        log_msg(INFO, "Circuit Save Path: " + file_wid.save_path)

        old_mask = os.umask(0)
        if not os.path.exists(file_wid.preference_path):
            os.mkdir(file_wid.preference_path, 0o744)
            os.chmod(file_wid.preference_path, 0o744)
        if not os.path.exists(file_wid.save_path):
            os.mkdir(file_wid.save_path, 0o744)
            os.chmod(file_wid.save_path, 0o744)
        os.umask(old_mask)

        self.preference_file_name = os.path.join(file_wid.preference_path, self.preference_file_name)
        file_wid.tmp_save_filename = os.path.join(file_wid.save_path, file_wid.tmp_save_filename)

    def reset_gui(self) -> None:
        """Resets the gui on a significant change, such as a font change"""
        self.clear()
        self.gui_build_all()

    def get_gate_list(self) -> list:
        """Return all active """
        if self.mode == ApplicationModes.REGULAR:
            gate_list = []
            for func in self.gates.keys():
                gate_list += self.gates[func].get_active_gates()
            return gate_list
        elif self.mode == ApplicationModes.CUSTOM_CIRCUIT:
            return self.widgets_custom_circuit.circuit_mode_gates

    def input_gates_intersect(self, event: Event) -> (bool, Optional[GraphicalGate]):
        """Checks if a new gate would intersect an existing gate if it was placed at (event.x, event.y) on the canvas,
         if they do, return true and the intersecting gate, otherwise return False, None"""
        img1_center_x, img1_center_y = event.x, event.y
        center_x_offset, center_y_offset = (Application.img_width / 2), (Application.img_height / 2)
        # Get Top-Left Coordinates of gate to be placed
        img1_tl_x, img1_tl_y = int(img1_center_x - center_x_offset), int(img1_center_y - center_y_offset)
        # Get Bottom-Right Coordinates of gate to be placed
        img1_br_x, img1_br_y = int(img1_center_x + center_x_offset), int(img1_center_y + center_y_offset)
        # Loop through all placed input gates to check if the new gate intersects with any placed gate

        for gate in self.get_gate_list():
            item = gate if not isinstance(gate, tuple) else gate[0]
            if do_overlap((img1_tl_x, img1_tl_y), (img1_br_x, img1_br_y),
                          item.top_left(), item.bottom_right()):
                return True, gate
        return False, None

    def intersects_input_gate(self, event: Event) -> (bool, list[GraphicalGate]):
        """Checks if the coordinate (event.x, event.y) intersects any existing gate(s) on canvas,
        if so, return true and the list of all gates which were intersected (in the case of overlapping gates),
        otherwise return False, []"""
        intersected_gates = []
        intersects = False
        for item in self.get_gate_list():
            gate = item if not isinstance(item, tuple) else item[0]
            if point_in_rect(event.x, event.y, gate.top_left(), gate.bottom_right()):  # If event is within gate...
                intersects = True
                intersected_gates.append(item)

        return intersects, intersected_gates

    def deselect_active_gates(self) -> None:
        """Removes border around gates and clear selected gates"""
        can_wid = self.widgets_canvas
        for gate in can_wid.icb_selected_gates:
            first = gate if not isinstance(gate, tuple) else gate[0]
            first.remove_rect()
        can_wid.icb_selected_gates.clear()
        can_wid.icb_click_drag_gate = None
        self.widgets_custom_circuit.active_circuit_input_gate = None
        self.widgets_custom_circuit.active_circuit_output_gate = None

    def left_click_cb(self, event: Event) -> None:
        """If user selected a gate button, place the gate on the canvas, otherwise (de)select the gate"""
        if 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            can_wid = self.widgets_canvas
            if can_wid.icb_is_gate_active:  # If user pressed a gate button...
                self.place_gate(event)
            else:
                self.deselect_active_gates()
                intersect, gates = self.intersects_input_gate(event)
                if intersect:  # If mouse click intersects any gate(s) select the first one
                    first_gate = gates[0] if not isinstance(gates[0], tuple) else gates[0][0]
                    can_wid.icb_selected_gates.append(gates[0])
                    first_gate.add_rect()

    def click_and_drag_cb(self, event: Event) -> None:
        """Moves a gate around on the canvas while the left mouse button is clicked and held"""
        can_wid = self.widgets_canvas
        if can_wid.icb_is_gate_active or len(can_wid.icb_selected_gates) != 1:
            # If user selected a gate button, then leave
            return

        if can_wid.icb_click_drag_gate is not None:  # if a gate is currently being drug around, keep using it
            can_wid.icb_click_drag_gate.move(event.x, event.y)
            return

        intersects, gates = self.intersects_input_gate(event)
        if not intersects:
            return

        first_gate = gates[0] if not isinstance(gates[0], tuple) else gates[0][0]
        self.deselect_active_gates()
        if point_in_rect(event.x, event.y, first_gate.top_left(), first_gate.bottom_right()):
            can_wid.icb_click_drag_gate = first_gate
            can_wid.icb_click_drag_gate.add_rect()
            can_wid.icb_selected_gates.append(gates[0])
            can_wid.icb_click_drag_gate.move(event.x, event.y)

    def connect_gates(self, event: Event) -> None:
        """Clears a gate button press if present.  If not, select two gates and connect them"""
        if 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            can_wid = self.widgets_canvas
            cir_wid = self.widgets_custom_circuit
            if can_wid.icb_is_gate_active:  # Right-clicking clears the gate that a user selects with a button
                self.set_active_logic_fn(None)
                # self.deselect_active_gates()
                return

            intersects, gates = self.intersects_input_gate(event)
            if not intersects:
                return

            dest_gate = gates[0] if not isinstance(gates[0], tuple) else gates[0][0]
            dest_test = None if not isinstance(gates[0], tuple) else gates[0][1]

            if len(can_wid.icb_selected_gates) == 0:
                dest_gate.add_rect()
                can_wid.icb_selected_gates.append(gates[0])

            elif len(can_wid.icb_selected_gates) == 1 and can_wid.icb_selected_gates[0] != dest_gate:
                src_gate = can_wid.icb_selected_gates[0]
                src_test = None if not isinstance(can_wid.icb_selected_gates[0], tuple) else can_wid.icb_selected_gates[0][1]
                # Gate is already selected and the second gate is different from the first
                if isinstance(src_gate, LogicGate) and isinstance(dest_gate, LogicGate):
                    # If both src and dest gates are LogicGates
                    connect_lgate_to_lgate(src_gate, dest_gate)
                    if src_test is not None and dest_test is not None:
                        connect_bg_to_bg(src_test, dest_test)
                elif isinstance(src_gate, LogicGate) and isinstance(dest_gate, Circuit):
                    # If src is LogicGate and dest is circuit
                    self.circuit_io_prompt('in', dest_gate)
                    if cir_wid.active_circuit_input_gate is not None:
                        connect_lgate_to_circuit(src_gate, dest_gate, cir_wid.active_circuit_input_gate)
                elif isinstance(src_gate, Circuit) and isinstance(dest_gate, LogicGate):
                    # Src is circuit, dest is LogicGate
                    self.circuit_io_prompt('out', src_gate)
                    if cir_wid.active_circuit_output_gate is not None:
                        connect_circuit_to_lgate(src_gate, cir_wid.active_circuit_output_gate, dest_gate)
                else:
                    # Both src and dest are circuits
                    self.circuit_io_prompt('out', src_gate)
                    self.circuit_io_prompt('in', dest_gate)
                    print("connect_gates(): Both gates are circuits")
                    if cir_wid.active_circuit_output_gate is not None and cir_wid.active_circuit_input_gate is not None:
                        connect_circuit_to_circuit(src_gate, cir_wid.active_circuit_output_gate,
                                                   dest_gate, cir_wid.active_circuit_input_gate)

                self.deselect_active_gates()
            elif len(can_wid.icb_selected_gates) == 1 and can_wid.icb_selected_gates[0] == dest_gate:
                # Gate is already selected and the second gate is the same as the first
                if is_clock(dest_gate):
                    self.widgets_timer.selected_timer = dest_gate
                    self.timer_prompt()
                    self.deselect_active_gates()
            else:
                self.deselect_active_gates()

    def circuit_io_prompt(self, mode: Literal['in', 'out'], circuit: Circuit) -> None:
        cir_wid = self.widgets_custom_circuit
        cir_wid.circuit_io_window = Toplevel(self)
        cir_wid.circuit_io_window.title("Select Gate {0}".format("Input" if mode == 'in' else "Output"))
        cir_wid.circuit_io_window.resizable(False, False)
        cir_wid.circuit_io_window.wait_visibility()
        cir_wid.circuit_io_window.grab_set()
        cir_wid.circuit_io_window.transient(self)

        options_dict = circuit.get_io_gates(mode)
        options = []
        for key in options_dict.keys():
            options.append((key, options_dict[key]))

        radio_frame = LabelFrame(cir_wid.circuit_io_window, text="{0} Gates".format("Input" if mode == 'in' else "Output"),
                                 font=self.active_font)
        radio_frame.grid(row=0, column=0, sticky='news', padx=(10, 10), pady=(10, 10))
        cir_wid.radio_vars = [IntVar(value=1)]

        none_radio = Radiobutton(radio_frame, text="None", font=self.active_font, variable=cir_wid.radio_vars[0],
                                 command=FunctionCallback(self.set_current_io_gate, circuit, mode, "",
                                                          cir_wid.radio_vars[0]))
        none_radio.grid(row=0, column=0, sticky='nsw')

        for (index, (name, gate)) in enumerate(options):
            cir_wid.radio_vars.append(IntVar(value=0))
            radio = Radiobutton(radio_frame, text=name, font=self.active_font, variable=cir_wid.radio_vars[-1],
                                command=FunctionCallback(self.set_current_io_gate, circuit, mode, name,
                                                         cir_wid.radio_vars[-1]))
            radio.grid(row=index + 1, column=0, sticky='nsw')

        done_button = Button(cir_wid.circuit_io_window, text="Done", font=self.active_font,
                             command=self.confirm_circuit_io)
        done_button.grid(padx=(10, 10), pady=(5, 5))

        self.wait_window(cir_wid.circuit_io_window)

    def set_current_io_gate(self, circuit: Circuit, mode: str, name: str, var: IntVar) -> None:
        cir_wid = self.widgets_custom_circuit
        for radio_var in cir_wid.radio_vars:
            if radio_var != var:
                radio_var.set(0)

        if mode == 'in':
            if name == "":
                cir_wid.active_circuit_input_gate = None
                return
            cir_wid.active_circuit_input_gate = circuit.get_input(name)
        elif mode == 'out':
            if name == "":
                cir_wid.active_circuit_output_gate = None
                return
            cir_wid.active_circuit_output_gate = circuit.get_output(name)

    def confirm_circuit_io(self) -> None:
        cir_wid = self.widgets_custom_circuit
        cir_wid.circuit_io_window.grab_release()
        cir_wid.circuit_io_window.destroy()
        cir_wid.circuit_io_window.update()

    def draw_gate_connection(self) -> None:
        can_wid = self.widgets_canvas
        if len(can_wid.icb_selected_gates) == 2 and can_wid.icb_selected_gates[0] != can_wid.icb_selected_gates[1]:
            src = can_wid.icb_selected_gates[0] if not isinstance(can_wid.icb_selected_gates[0], tuple) else can_wid.icb_selected_gates[0][0]
            dest = can_wid.icb_selected_gates[1] if not isinstance(can_wid.icb_selected_gates[1], tuple) else can_wid.icb_selected_gates[1][0]
            src_test  = None if not isinstance(can_wid.icb_selected_gates[0], tuple) else can_wid.icb_selected_gates[0][1]
            dest_test = None if not isinstance(can_wid.icb_selected_gates[1], tuple) else can_wid.icb_selected_gates[1][1]
            connect_lgate_to_lgate(src, dest)
            if src_test and dest_test:
                connect_bg_to_bg(src_test, dest_test)

            self.deselect_active_gates()

    def do_circuit_context_menu(self, event: Event) -> None:
        can_wid = self.widgets_canvas
        try:
            if can_wid.icb_is_gate_active:  # Right-clicking clears the gate that a user selects with a button
                self.set_active_logic_fn(None)
                self.deselect_active_gates()
                return

            intersects, gates = self.intersects_input_gate(event)
            if not intersects:
                return

            first_gate = gates[0] if not isinstance(gates[0], tuple) else gates[0][0]

            if len(can_wid.icb_selected_gates) == 0:
                first_gate.add_rect()
                can_wid.icb_selected_gates.append(gates[0])
            elif len(can_wid.icb_selected_gates) == 1 and can_wid.icb_selected_gates[0] != first_gate:
                # Gate is already selected and the second gate is different from the first
                first_gate.add_rect()
                can_wid.icb_selected_gates.append(gates[0])

            self.widgets_custom_circuit.circuit_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            pass

    def multi_select_cb(self, event: Event) -> None:
        """Selects multiple gates to be deleted"""
        can_wid = self.widgets_canvas
        if can_wid.icb_is_gate_active:
            return

        intersects, gates = self.intersects_input_gate(event)

        if not intersects:
            return

        first_gate = gates[0] if not isinstance(gates[0], tuple) else gates[0][0]
        if len(can_wid.icb_selected_gates) < self.max_selectable_gates:
            first_gate.add_rect()
            can_wid.icb_selected_gates.append(gates[0])
        else:  # Deselect first gate and add select this new gate
            first_gate = can_wid.icb_selected_gates[0] if not isinstance(can_wid.icb_selected_gates[0], tuple) else can_wid.icb_selected_gates[0][0]
            first_gate.remove_rect()
            can_wid.icb_selected_gates = can_wid.icb_selected_gates[1:]
            can_wid.icb_selected_gates.append(gates[0])

    def motion_cb(self, event: Event) -> None:
        """Move the image of the selected gate with the mouse"""
        can_wid = self.widgets_canvas
        if can_wid.icb_is_gate_active and 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            self.active_input_pi = PhotoImage(file=self.active_input_pi_fn)
            self.active_input_img_index = can_wid.screen_icb.create_image(event.x, event.y, image=self.active_input_pi)
            self.active_input.set_id(self.active_input_img_index)

    def delete_cb(self, event: Event) -> None:
        """Delete all selected gates from the canvas"""
        can_wid = self.widgets_canvas
        for i in range(len(can_wid.icb_selected_gates)):
            gate = can_wid.icb_selected_gates[i] if not isinstance(can_wid.icb_selected_gates[i], tuple) else \
            can_wid.icb_selected_gates[i][0]

            if self.mode == ApplicationModes.REGULAR:
                self.gates[self.gates.proper_key(gate)].remove(gate)

                if is_power_gate(gate):  # Remove entries from the power table
                    self.widgets_input_selection.is_edit_table.del_gate_entry(gate)

            elif self.mode == ApplicationModes.CUSTOM_CIRCUIT:
                self.widgets_custom_circuit.circuit_mode_gates.remove(can_wid.icb_selected_gates[i])
                self.active_circuit.remove(can_wid.icb_selected_gates[i][1])

            gate.delete()

        self.deselect_active_gates()

    def remove_connection_cb(self, event: Event) -> None:
        """Removed the connection between 2 gates"""
        can_wid = self.widgets_canvas
        cir_wid = self.widgets_custom_circuit
        if not can_wid.icb_is_gate_active:
            if len(can_wid.icb_selected_gates) == 2 and can_wid.icb_selected_gates[0] != can_wid.icb_selected_gates[1]:
                g1 = can_wid.icb_selected_gates[0] if not isinstance(can_wid.icb_selected_gates[0], tuple) else \
                can_wid.icb_selected_gates[0][0]
                g2 = can_wid.icb_selected_gates[1] if not isinstance(can_wid.icb_selected_gates[1], tuple) else \
                can_wid.icb_selected_gates[1][0]
                g1_test = None if not isinstance(can_wid.icb_selected_gates[0], tuple) else can_wid.icb_selected_gates[0][1]
                g2_test = None if not isinstance(can_wid.icb_selected_gates[1], tuple) else can_wid.icb_selected_gates[1][1]

                if isinstance(g1, LogicGate) and isinstance(g2, LogicGate):
                    disconnect_lgate_to_lgate(g1, g2)
                elif isinstance(g1, Circuit) and isinstance(g2, LogicGate):
                    if is_parent(g1, g2):
                        self.circuit_io_prompt('out', g1)
                        if cir_wid.active_circuit_output_gate is None:
                            return
                        disconnect_circuit_to_lgate(g1, cir_wid.active_circuit_output_gate, g2)
                    elif is_parent(g2, g1):
                        self.circuit_io_prompt('in', g1)
                        if cir_wid.active_circuit_input_gate is None:
                            return
                        disconnect_circuit_to_lgate(g1, cir_wid.active_circuit_input_gate, g2)
                    else:
                        return

                elif isinstance(g1, LogicGate) and isinstance(g2, Circuit):
                    if is_parent(g1, g2):
                        self.circuit_io_prompt('in', g2)
                        if cir_wid.active_circuit_input_gate is None:
                            return
                        disconnect_circuit_to_lgate(g2, cir_wid.active_circuit_input_gate, g1)
                    elif is_parent(g2, g1):
                        self.circuit_io_prompt('out', g2)
                        if cir_wid.active_circuit_output_gate is None:
                            return
                        disconnect_circuit_to_lgate(g2, cir_wid.active_circuit_output_gate, g1)
                    else:
                        return

                elif isinstance(g1, Circuit) and isinstance(g2, Circuit):
                    if is_parent(g1, g2):
                        self.circuit_io_prompt('out', g1)
                        self.circuit_io_prompt('in', g2)
                        if cir_wid.active_circuit_output_gate and cir_wid.active_circuit_input_gate:
                            disconnect_circuit_to_circuit(g1, cir_wid.active_circuit_output_gate,
                                                          g2, cir_wid.active_circuit_input_gate)
                    elif is_parent(g2, g1):
                        self.circuit_io_prompt('out', g2)
                        self.circuit_io_prompt('in', g1)
                        if cir_wid.active_circuit_output_gate and cir_wid.active_circuit_input_gate:
                            disconnect_circuit_to_circuit(g2, cir_wid.active_circuit_output_gate,
                                                          g1, cir_wid.active_circuit_input_gate)
                    #else:
                    #    print("Not connected:", g1, g2)

                if g1_test and g2_test:
                    disconnect_bg_to_bg(g1_test, g2_test)

                self.deselect_active_gates()
            else:
                log_msg(WARNING, "You can only disconnect two gates!")

    def place_gate(self, event: Event) -> None:
        """Places a gate on the canvas after pressing a gate button"""
        if self.widgets_canvas.icb_is_gate_active and 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            if self.input_gates_intersect(event)[0]:
                return
            if self.mode == ApplicationModes.REGULAR:
                self.place_gate_regular(event)
            elif self.mode == ApplicationModes.CUSTOM_CIRCUIT:
                self.place_gate_circuit(event)

    def place_gate_regular(self, event: Event) -> None:
        gate_info = self.gates[self.gates.proper_key(self.active_input)]
        new_gate = None
        if is_clock(self.active_input):
            new_gate = ClockTk.construct_copy(self.active_input, (event.x, event.y))
        elif is_output_gate(self.active_input):
            new_gate = OutputGate.construct_copy(self.active_input, (event.x, event.y))
        elif isinstance(self.active_input, LogicGate):
            new_gate = LogicGate.construct_copy(self.active_input, (event.x, event.y))
        elif is_circuit(self.active_input):
            new_gate = Circuit.construct_copy(self.active_input, (event.x, event.y))

        self.gates.add_gate(new_gate)

        if is_clock(self.active_input):
            self.widgets_timer.selected_timer = gate_info.get_active_gates()[-1]
            self.timer_prompt()  # Configure this new timer on placement

        last_input = gate_info.get_active_gates()[-1]
        self.active_input_img_index = last_input.get_id()
        # Add checkbox entry to entry menu if gate is a power source
        if is_power_gate(new_gate):
            self.widgets_input_selection.is_edit_table.add_entry(new_gate)

    def place_gate_circuit(self, event: Event) -> None:
        gate = LogicGate.construct_copy(self.active_input, (event.x, event.y))
        test_gate = BaseGate(gate.get_func(), new_gate_label(gate.get_label()))
        self.active_circuit.add_inner_gate(test_gate)
        self.widgets_custom_circuit.circuit_mode_gates.append((gate, test_gate))
        self.active_input_img_index = gate.get_id()

    def save(self, event: Optional[Event] = None) -> None:
        self.save_diagram()

        for circuit in self.widgets_custom_circuit.circuits:
            self.save_circuit(circuit)

    def save_diagram(self) -> None:
        """Save the current circuit to a file, if this is the first save, prompt for file name"""
        file_wid = self.widgets_file
        if file_wid.filename == "":  # If the program has not been saved before, prompt for filename
            log_msg(INFO, "No save file has been specified.")
            self.save_as()
            if file_wid.filename is None:
                return

        log_msg(INFO, "Saving diagram to: " + file_wid.filename)

        doc = tomlkit.document()

        gate_info = tomlkit.table()
        gates = self.get_gate_list()
        gate_info.add("Total", len(gates))

        for idx, gate in enumerate(gates):
            # For each gate, write the gate and its enumeration, which is used as its id
            gate_table = tomlkit.inline_table().indent(1)
            gate_table.add("Function", gate.get_func().__name__)
            gate_table.add("Center", gate.get_center())
            if is_clock(gate):
                gate_table.add("Default_State", gate.default_state)
                gate_table.add("Rate", gate.get_rate())
            else:
                gate_table.add("Output", gate.out.get())
                gate_table.add("Custom_Label", gate.get_label() if is_power_gate(gate) else "")

            gate_table.add("Gate_ID", idx)
            gate_info[str(idx)] = gate_table
            gates[idx] = (gate, idx)

        doc["Gates"] = gate_info

        connection_table = tomlkit.table()

        for (gate, cnt) in gates:
            in_gates = gate.get_input_gates()
            out_gates = gate.get_output_gates()
            gate_con_table = tomlkit.inline_table().indent(1)

            gate_inputs = tomlkit.array()
            for in_gate in in_gates:
                for other_gate in gates:
                    if other_gate[0] == in_gate:
                        gate_inputs.append(other_gate[1])
                        break
            gate_con_table.add("Inputs", gate_inputs)

            # For every output, find the gate in the master list and add its id number to the list,
            # to reconstruct later
            gate_outputs = tomlkit.array()
            if out_gates:
                for out_gate in out_gates:
                    for other_gate in gates:
                        if other_gate[0] == out_gate:
                            gate_outputs.append(other_gate[1])
                            break
            gate_con_table.add("Outputs", gate_outputs)

            connection_table[str(cnt)] = gate_con_table

        doc["Connections"] = connection_table

        with open(file_wid.filename, mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(doc, fp)

    def save_circuit(self, circuit: Circuit) -> None:
        pass

    def save_as(self):
        """Create save file prompt and set self.filename to this file"""
        file_wid = self.widgets_file
        file_wid.filename = fd.asksaveasfilename(initialfile=file_wid.filename, initialdir=file_wid.save_path,
                                             filetypes=[("Circuit Diagram", "*" + file_wid.file_type)])
        if len(file_wid.filename) == 0:
            file_wid.filename = ""
        elif len(file_wid.filename) < 4 or (len(file_wid.filename) > 4 and file_wid.filename[-4:] != file_wid.file_type):
            file_wid.filename += file_wid.file_type

    def save_temp(self) -> None:
        file_wid = self.widgets_file
        tmp = file_wid.filename
        file_wid.filename = file_wid.tmp_save_filename
        self.save()
        file_wid.filename = tmp

    def open(self, event: Optional[Event] = None) -> None:
        """Load circuit from file.  Eventually use tomlkit to create nicely formatted file."""
        file_wid = self.widgets_file
        can_wid = self.widgets_canvas
        if file_wid.filename != file_wid.tmp_save_filename:
            file_wid.filename = fd.askopenfilename(initialdir=file_wid.save_path,
                                               filetypes=[("Circuit Diagram", "*" + file_wid.file_type)])
        if file_wid.filename == "":
            return

        log_msg(INFO, "Loading diagram: " + os.path.abspath(file_wid.filename))

        with open(file_wid.filename, mode="rt", encoding="utf-8") as fp:
            self.clear()
            document = tomlkit.load(fp)
            gates = []

            for idx in range(int(document["Gates"]["Total"])):  # Load every gate into the canvas
                gate_func = get_logic_func_from_name(document["Gates"][str(idx)]["Function"])
                gate_inst = str(len(self.gates[gate_func].get_active_gates()) + 1)
                gate_center = document["Gates"][str(idx)]["Center"]
                image_file = self.gates[gate_func]["image_file"]

                if gate_func == logic_clock:  # If this input is clock, it has a different format
                    rate = document["Gates"][str(idx)]["Rate"]
                    state = document["Gates"][str(idx)]["Default_State"]
                    gate = ClockTk(image_file=image_file, update_rate=rate, label="Clock #" + gate_inst,
                                   canvas=can_wid.screen_icb, center=gate_center, default_state=state)
                elif gate_func == output:
                    gate_out = document["Gates"][str(idx)]["Output"]
                    gate_label = capitalize(gate_func.__name__ + " #" + gate_inst)
                    gate = OutputGate(image_file=image_file, label=gate_label, canvas=can_wid.screen_icb,
                                      center=gate_center, out=gate_out)
                else:
                    gate_out = document["Gates"][str(idx)]["Output"]
                    if gate_func == power:  # If power gate has a custom label...
                        gate_label = document["Gates"][str(idx)]["Custom_Label"]
                    else:
                        gate_label = capitalize(gate_func.__name__ + " #" + gate_inst)

                    gate = LogicGate(func=gate_func, image_file=image_file,
                                     label=gate_label, canvas=can_wid.screen_icb, center=gate_center, out=gate_out)
                    if is_power_gate(gate):
                        # Add power gate to appropriate table
                        self.widgets_input_selection.is_edit_table.add_entry(gate)

                gates.append((gate, idx))
                self.gates[gate_func].add_active_gate(gate)

            for idx in range(int(document["Gates"]["Total"])):  # Load connection info for every gate
                current_gate = None
                for (gate, num) in gates:
                    if num == idx:
                        current_gate = gate
                        break

                # Read gate inputs
                # Find input gates based on gate num
                inputs_id_list = document["Connections"][str(idx)]["Inputs"]
                outputs_id_list = document["Connections"][str(idx)]["Outputs"]

                # Get list of input and output gates using gate ids
                for input_id in inputs_id_list:
                    for (gate, num) in gates:
                        if num == input_id:
                            connect_lgate_to_lgate(gate, current_gate)
                            break

                for output_id in outputs_id_list:
                    for (gate, num) in gates:
                        if num == output_id:
                            connect_lgate_to_lgate(current_gate, gate)
                            break

    def open_temp(self) -> None:
        file_tmp = self.widgets_file
        tmp = file_tmp.filename
        file_tmp.filename = file_tmp.tmp_save_filename
        self.open()
        file_tmp.filename = tmp
        os.remove(file_tmp.tmp_save_filename)

    def clear(self) -> None:
        """Clear the canvas, clear all entries from the power table, and delete all gates"""
        self.deselect_active_gates()
        self.reset()
        self.widgets_input_selection.is_edit_table.clear()

        # Destroy Gates
        for func in self.gates.keys():
            for gate in self.gates[func].get_active_gates():
                gate.delete()
            self.gates[func].active_gates = []

        cir_wid = self.widgets_custom_circuit
        can_wid = self.widgets_canvas
        for gate in cir_wid.circuit_mode_gates:
            gate[0].delete()

        cir_wid.circuit_mode_gates.clear()
        # Reset all reference to gates
        can_wid.icb_is_gate_active = False
        self.set_active_logic_fn(None)
        # Clear Canvas
        can_wid.screen_icb.delete('all')
        self.widgets_file.filename = ""

    def help(self) -> None:
        """Opens help window"""
        self.help_window = Toplevel(self)
        self.help_window.title("Help")
        self.help_window.resizable(False, False)

        win_x = self.winfo_rootx()  # + self.width // 3
        win_y = self.winfo_rooty()
        self.help_window.geometry(f'+{win_x}+{win_y}')

        self.help_window.wait_visibility()
        self.help_window.grab_set()
        self.help_window.transient(self)

        help_window_width = 770
        help_window_height = 600
        scrollable_frame = ScrollableVFrame(self.help_window, this_font=self.active_font, width=help_window_width,
                                           height=help_window_height)
        scrollable_frame.grid(padx=(10, 10), pady=(10, 10), sticky='news')

        # Shortcut Entries #############################################################################################
        shortcut_labelframe = LabelFrame(scrollable_frame.frame, font=self.active_font, text="Shortcuts")
        shortcut_labelframe.grid(column=0, row=0, sticky='news', pady=(0, 5))
        shortcut_entry_width = 17
        drag_gate_shortcut = LabeledEntry(shortcut_labelframe, label_text="Select Gate:", entry_text="Left Click",
                                          entry_width=shortcut_entry_width, widget_font=self.active_font, disabled=True)
        drag_gate_shortcut.grid(row=0, column=0, sticky='nse', pady=(0, 5))

        multi_gate_shortcut = LabeledEntry(shortcut_labelframe, label_text="Multi-Select Gate:",
                                           entry_width=shortcut_entry_width,
                                           entry_text="Ctrl + Left Click", widget_font=self.active_font, disabled=True)
        multi_gate_shortcut.grid(row=1, column=0, sticky='nse', pady=(0, 5))

        connect_gate_shortcut = LabeledEntry(shortcut_labelframe, label_text="Connect Gate:", entry_text="Right Click",
                                             entry_width=shortcut_entry_width,
                                             widget_font=self.active_font, disabled=True)
        connect_gate_shortcut.grid(row=2, column=0, sticky='nse', pady=(0, 5))

        clear_gate_image_shortcut = LabeledEntry(shortcut_labelframe, label_text="Clear Button Press:",
                                                 entry_text="Right Click", entry_width=shortcut_entry_width,
                                                 widget_font=self.active_font, disabled=True)
        clear_gate_image_shortcut.grid(row=3, column=0, sticky='nse', pady=(0, 5))

        delete_gate_shortcut = LabeledEntry(shortcut_labelframe, label_text="Delete Gate:", entry_text="Backspace",
                                            entry_width=shortcut_entry_width,
                                            widget_font=self.active_font, disabled=True)
        delete_gate_shortcut.grid(row=4, column=0, sticky='nse', pady=(0, 5))

        clear_connection_shortcut = LabeledEntry(shortcut_labelframe, label_text="Clear Connection:", entry_text="c",
                                                 entry_width=shortcut_entry_width,
                                                 widget_font=self.active_font, disabled=True)
        clear_connection_shortcut.grid(row=5, column=0, sticky='nse', pady=(0, 5))

        start_clocks_shortcut = LabeledEntry(shortcut_labelframe, label_text="Start Clocks:", entry_text="p",
                                             entry_width=shortcut_entry_width,
                                             widget_font=self.active_font, disabled=True)
        start_clocks_shortcut.grid(row=0, column=1, sticky='nse', pady=(0, 5))

        stop_clocks_shortcut = LabeledEntry(shortcut_labelframe, label_text="Stop Clocks:", entry_text="t",
                                            entry_width=shortcut_entry_width,
                                            widget_font=self.active_font, disabled=True)
        stop_clocks_shortcut.grid(row=1, column=1, sticky='nse', pady=(0, 5))

        toggle_clocks_shortcut = LabeledEntry(shortcut_labelframe, label_text="Toggle Clocks:", entry_text="Space",
                                              entry_width=shortcut_entry_width,
                                              widget_font=self.active_font, disabled=True)
        toggle_clocks_shortcut.grid(row=2, column=1, sticky='nse', pady=(0, 5))

        reset_clocks_shortcut = LabeledEntry(shortcut_labelframe, label_text="Reset Clocks:", entry_text="r",
                                             entry_width=shortcut_entry_width,
                                             widget_font=self.active_font, disabled=True)
        reset_clocks_shortcut.grid(row=3, column=1, sticky='nse', pady=(0, 5))

        save_shortcut = LabeledEntry(shortcut_labelframe, label_text="Save:", entry_text="Ctrl + s",
                                     entry_width=shortcut_entry_width,
                                     widget_font=self.active_font, disabled=True)
        save_shortcut.grid(row=4, column=1, sticky='nse', pady=(0, 5))
        save_shortcut = LabeledEntry(shortcut_labelframe, label_text="Open:", entry_text="Ctrl + o",
                                     entry_width=shortcut_entry_width,
                                     widget_font=self.active_font, disabled=True)
        save_shortcut.grid(row=5, column=1, sticky='nse', pady=(0, 5))
        ################################################################################################################
        # Line Colors ############################################################################################
        line_color_labelframe = LabelFrame(scrollable_frame.frame, font=self.active_font, text="Line Colors")
        line_color_labelframe.grid(row=1, column=0, sticky='news', pady=(0, 5))

        powered_label = LabeledEntry(line_color_labelframe, label_text="Green",
                                     entry_text="This line is receiving power", widget_font=self.active_font,
                                     entry_width=25, entry_height=2, label_background="green", disabled=True)
        powered_label.grid(row=0, column=0, padx=(5, 10), pady=(5, 5))

        unpowered_label = LabeledEntry(line_color_labelframe, label_text=" Red ",
                                       entry_text="This line is not receiving power", widget_font=self.active_font,
                                       entry_width=25, entry_height=2,
                                       label_background="red", disabled=True)
        unpowered_label.grid(row=0, column=1, padx=(5, 5), pady=(5, 5))
        missing_power_label = LabeledEntry(line_color_labelframe, label_text="Black",
                                           entry_text="This line is missing an input and is neither on or off.",
                                           widget_font=self.active_font, entry_width=30, entry_height=2,
                                           label_background="black", label_foreground='white', disabled=True)
        missing_power_label.grid(row=1, columnspan=2, padx=(0, 0), pady=(0, 5))

        # Gate Descriptions ############################################################################################
        desc_labelframe = LabelFrame(scrollable_frame.frame, font=self.active_font, text="Gate Descriptions")
        desc_labelframe.grid(row=2, column=0, sticky='news', padx=(0, 0), pady=(5, 5))
        desc_height = 5
        desc_width = 24
        power_desc = PictureDescription(desc_labelframe, img=self.gates[power]["image"],
                                        desc_text=self.gates[power]["desc"],
                                        text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        power_desc.grid(row=0, column=0)

        not_desc = PictureDescription(desc_labelframe, img=self.gates[logic_not]["image"],
                                      desc_text=self.gates[logic_not]["desc"],
                                      text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        not_desc.grid(row=0, column=1)

        and_desc = PictureDescription(desc_labelframe, img=self.gates[logic_and]["image"],
                                      desc_text=self.gates[logic_and]["desc"],
                                      text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        and_desc.grid(row=1, column=0)

        nand_desc = PictureDescription(desc_labelframe, img=self.gates[logic_nand]["image"],
                                       desc_text=self.gates[logic_nand]["desc"],
                                       text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        nand_desc.grid(row=1, column=1)

        or_desc = PictureDescription(desc_labelframe, img=self.gates[logic_or]["image"],
                                     desc_text=self.gates[logic_or]["desc"],
                                     text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        or_desc.grid(row=2, column=0)

        xor_desc = PictureDescription(desc_labelframe, img=self.gates[logic_xor]["image"],
                                      desc_text=self.gates[logic_xor]["desc"],
                                      text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        xor_desc.grid(row=2, column=1)

        output_desc = PictureDescription(desc_labelframe, img=self.gates[output]["image"],
                                         desc_text=self.gates[output]["desc"],
                                         text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        output_desc.grid(row=3, column=0)

        clock_desc = PictureDescription(desc_labelframe, img=self.gates[logic_clock]["image"],
                                        desc_text=self.gates[logic_clock]["desc"],
                                        text_width=desc_width, text_height=desc_height, this_font=self.active_font, scrollbar_on=False)
        clock_desc.grid(row=3, column=1, padx=(25, 0))
        # self.update_idletasks()

        done_button = Button(self.help_window, text="Done", font=self.active_font, command=self.close_help)
        done_button.grid(columnspan=3, sticky='ew')
        self.wait_window(self.help_window)

    def close_help(self) -> None:
        # Reset popup state
        self.help_window.grab_release()
        self.help_window.destroy()
        self.help_window.update()

    def pause(self, event: Event) -> None:
        """Pauses all clocks"""
        log_msg(INFO, "Pausing Clocks.")
        ClockTk.clocks_paused = True
        for timer in self.gates[logic_clock].get_active_gates():
            timer.pause()

    def play(self, event: Optional[Event] = None) -> None:
        """Starts all clocks"""
        log_msg(INFO, "Starting Clocks.")
        ClockTk.clocks_paused = False
        for timer in self.gates[logic_clock].get_active_gates():
            timer.start()

    def reset(self, event: Optional[Event] = None) -> None:
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

    def set_active_logic_fn(self, fn: Optional[Callable]) -> None:
        can_wid = self.widgets_canvas

        if fn is None:
            """Set when a gate button is clear"""
            self.deselect_active_gates()
            can_wid.icb_is_gate_active = False
            can_wid.screen_icb.delete(self.active_input_img_index)
            return

        self.deselect_active_gates()
        can_wid.icb_is_gate_active = True

        if fn == logic_clock:
            self.active_input = ClockTk(self.gates[logic_clock]["image_file"], self.default_update_rate,
                                        label="Clock #", canvas=can_wid.screen_icb)
        elif fn == output:
            self.active_input = OutputGate(self.gates.attr(output, "image_file"), label="Output #",
                                           canvas=can_wid.screen_icb)
        else:
            self.active_input = LogicGate(fn, self.gates[fn]["image_file"], label=capitalize(fn.__name__ + " #"),
                                          canvas=can_wid.screen_icb)
            if fn == power:
                self.active_input.set_output(TRUE)
                self.active_input.set_label("Input #")
        self.active_input_pi_fn = self.gates[fn]["image_file"]

    def set_active_fn_custom_circuit(self, index: int) -> None:
        cir_wid = self.widgets_custom_circuit
        can_wid = self.widgets_canvas
        if index < len(cir_wid.circuits):
            self.deselect_active_gates()
            can_wid.icb_is_gate_active = True
            circuit = cir_wid.circuits[index]
            self.active_input = Circuit.construct_copy(circuit, (NULL, NULL))
            self.active_input.delete_text()
            self.active_input_pi_fn = circuit.get_image_file()

    def configure_widgets(self) -> None:
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # is_wid.is_edit_table.config()
    def gui_build_input_selection_menu(self) -> None:
        """Build the side pane: the power table and gate buttons"""
        is_wid = self.widgets_input_selection
        actual_frame_width = self.input_selection_screen_width - self.border_width
        print(actual_frame_width)
        is_wid.bordered_frame = Frame(self, background='black', width=self.input_selection_screen_width,
                                      height=self.height)
        is_wid.bordered_frame.grid(row=0, column=1, rowspan=2, sticky='nwse')
        is_wid.bordered_frame.grid_rowconfigure(0, weight=1)
        is_wid.bordered_frame.grid_propagate(False)

        # i = Frame(f, background='white', width=196, height=600)
        # i.grid(sticky='nesw', padx=(4, 0))
        # i.grid_rowconfigure(1, weight=1)
        is_wid.screen_is = Frame(is_wid.bordered_frame, background='white', width=actual_frame_width, height=self.height)
        is_wid.screen_is.grid(padx=(self.border_width, 0), sticky="nsew")
        is_wid.screen_is.grid_rowconfigure(1, weight=1)

        ## Add gate buttons #############################################################################################
        is_wid.is_button_frame = LabelFrame(is_wid.screen_is, bg="white", font=self.active_font, text="Logic Gates")
        is_wid.is_button_frame.grid(row=0, column=0, sticky='nwes', padx=(10, 0), pady=(10, 0))

        for (i, func) in enumerate(self.gates.keys()):
            if not isinstance(func, Callable):
                continue
            labeled_button_frame = Frame(is_wid.is_button_frame, background='white')
            labeled_button_frame.grid(column=0, row=i, padx=(0, 5), sticky="e")
            if i == len(self.gates) - 1:
                labeled_button_frame.grid_configure(pady=(0, 5))

            label_text = ""
            if func not in (output, power, logic_clock):
                # Strip logic_ from each logic gate name
                label_text = capitalize(self.gates.attr(func, "name")[6:]) + " Gate:"
            elif func == power:
                label_text = "Input:"
            elif func == output:
                label_text = "Output:"
            elif func == logic_clock:
                label_text = "Clock:"

            button_label = Label(labeled_button_frame, text=label_text, background='white',
                                 font=reconfig_font(self.active_font, offset=-2, weight="bold"))
            button_label.grid(column=0, row=0, padx=(0, 3), sticky='w')

            is_border_frame = Frame(labeled_button_frame, highlightbackground="black",
                                    highlightthickness=1, bd=0)
            is_border_frame.grid(row=0, column=1, sticky='e')
            is_border_frame.propagate(True)

            is_button = Button(is_border_frame, image=self.gates.attr(func, "image"), bg="white", relief="flat",
                               command=self.gates.attr(func, "callback"))
            is_button.grid(sticky='e')

            is_wid.is_buttons[func] = (is_button, button_label)

        # Add table to this side pane
        is_wid.is_edit_table = CheckbuttonTable(is_wid.screen_is, self.widgets_canvas.screen_icb,
                                                self.active_font, text='Inputs')
        is_wid.is_edit_table.grid(row=1, column=0, sticky='news', padx=(10, 10))
        # is_wid.is_edit_table.grid_propagate(False)

        # self.update_idletasks()

    def gui_build_icb(self) -> None:
        """Builds the canvas for the gates to exist on and create all the key bindings"""

        can_wid = self.widgets_canvas
        can_wid.screen_icb = ResizingCanvas(self, bb_width=self.width - self.input_selection_screen_width,
                                            bb_height=self.height - self.circuit_screen_height,
                                            scroll_width=self.width - self.input_selection_screen_width,
                                            scroll_height=self.height - self.circuit_screen_height,
                                            color='red')#self.widgets_preferences.background_color.get())
        can_wid.screen_icb.grid(row=0, column=0, sticky="news")
        # can_wid.screen_icb.grid_propagate(False)
        # Set key bindings
        can_wid.screen_icb.bind('<Motion>', self.motion_cb)
        can_wid.screen_icb.bind('<Button-1>', self.left_click_cb)
        can_wid.screen_icb.bind('<B1-Motion>', self.click_and_drag_cb)
        can_wid.screen_icb.bind('<Button-3>', self.connect_gates)
        can_wid.screen_icb.bind('<KeyRelease-BackSpace>', self.delete_cb)
        can_wid.screen_icb.bind('<Control-Button-1>', self.multi_select_cb)
        can_wid.screen_icb.bind('<Control-s>', self.save)
        can_wid.screen_icb.bind('<Control-o>', self.save)
        can_wid.screen_icb.bind('<c>', self.remove_connection_cb)
        can_wid.screen_icb.bind('<r>', self.reset)
        can_wid.screen_icb.bind('<p>', self.play)
        can_wid.screen_icb.bind('<t>', self.pause)
        can_wid.screen_icb.bind('<space>', self.toggle_play_pause)
        # Force the canvas to stay focused, keybindings only take effect when this widget has focus
        can_wid.screen_icb.focus_force()
        LineRepository.set_canvas(can_wid.screen_icb)

    def gui_build_context_menu(self) -> None:
        """Builds the menu which appears when right-clicking in the circuit building mod"""
        cir_wid = self.widgets_custom_circuit
        cir_wid.circuit_context_menu = Popup(self, tearoff=0, menu_mode=True, font=self.active_font)
        cir_wid.circuit_context_menu.add_command(label="Connect", command=self.draw_gate_connection)
        cir_wid.circuit_context_menu.add_separator()
        cir_wid.circuit_context_menu.add_command(label="Set as Circuit Input", state='disabled')
        cir_wid.circuit_context_in_index = 2
        cir_wid.circuit_context_menu.add_command(label="Set as Circuit Output", state='disabled')
        cir_wid.circuit_context_out_index = 3
        cir_wid.input_label_names = []
        cir_wid.output_label_names = []

    def gui_build_circuit_pane(self) -> None:
        """Creates the custom circuit pane"""
        cir_wid = self.widgets_custom_circuit
        pref_wid = self.widgets_preferences

        cir_wid.circuit_border_frame = Frame(self, background='black',
                                          width=self.width - self.input_selection_screen_width,
                                          height=self.circuit_screen_height)
        cir_wid.circuit_border_frame.grid(row=1, column=0, sticky='news')
        cir_wid.circuit_border_frame.grid_columnconfigure(0, weight=1)
        cir_wid.circuit_border_frame.grid_rowconfigure(0, weight=1)
        cir_wid.circuit_border_frame.grid_propagate(False)

        cir_wid.screen_circuit = ScrollableHFrame(cir_wid.circuit_border_frame, this_font=self.active_font,
                                                  bg_color=pref_wid.background_color.get(),
                                                  width=self.width - self.input_selection_screen_width,
                                                  height=self.circuit_screen_height - self.border_width - cir_wid.circuit_scrollbar_height)
        cir_wid.screen_circuit.grid(row=0, column=0, sticky='news', padx=(0, 0), pady=(self.border_width, 0))
        # cir_wid.circuit_border_frame.grid_propagate(False)

        cir_wid.new_circuit_pi = PhotoImage(file=join_folder_file(CIRCUIT_IMG_FOLDER, "add_new_circuit.png"))
        cir_wid.new_circuit_button = LabeledButton(cir_wid.screen_circuit.frame, label_direction=S,
                                                   button_content=cir_wid.new_circuit_pi,
                                                   cmd=self.gui_enter_circuit_builder, label_text="Add New Circuit",
                                                   this_font=self.active_font, background='white')
        cir_wid.new_circuit_button.grid(row=0, column=len(cir_wid.circuit_buttons), sticky='nw', padx=(5, 0),
                                        pady=(10, 0))

        for (i, button) in enumerate(cir_wid.circuit_buttons):
            button.grid_configure(column=i, row=0)

    def set_button_state_for_circuit_builder(self, state: str) -> None:
        """Disables invalid buttons when entering circuit building mode"""
        cir_wid = self.widgets_custom_circuit
        for func in [power, logic_clock, output]:
            (btn, frame) = self.widgets_input_selection.is_buttons[func]
            btn.configure(state=state)
        for cir_btn in cir_wid.circuit_buttons:
            cir_btn.buttonconfig(state=state)
        cir_wid.new_circuit_button.buttonconfig(state=state)

    def gui_enter_circuit_builder(self) -> None:
        """Switches program to circuit building mode"""
        self.save_temp()
        self.clear()

        self.gui_build_context_menu()
        self.set_button_state_for_circuit_builder('disabled')

        self.mode = ApplicationModes.CUSTOM_CIRCUIT
        can_wid = self.widgets_canvas
        self.active_circuit = Circuit(image_file=join_folder_file(CIRCUIT_IMG_FOLDER, "blank_circuit.png"),
                                      canvas=can_wid.screen_icb, font=self.active_font)

        can_wid.screen_icb.bind('<Button-3>', self.do_circuit_context_menu)
        self.custom_circuit_window()

    def gui_close_circuit_builder(self) -> None:
        self.clear()
        self.mode = ApplicationModes.REGULAR
        cir_wid = self.widgets_custom_circuit
        cir_wid.active_circuit.delete_text()
        cir_wid.active_circuit = None
        self.open_temp()
        self.set_button_state_for_circuit_builder('active')

        self.widgets_canvas.screen_icb.bind('<Button-3>', self.connect_gates)
        cir_wid.circuit_context_menu.destroy()
        cir_wid.circuit_context_menu = None

    def custom_circuit_window(self) -> None:
        cir_wid = self.widgets_custom_circuit
        cir_wid.circuit_prompt = Toplevel(self)
        cir_wid.circuit_prompt.resizable(False, False)
        cir_wid.circuit_prompt.geometry("+{0}+{1}".format(self.winfo_rootx() + (self.width // 2), self.winfo_rooty() + 10))
        cir_wid.circuit_prompt.title("Preferences")
        cir_wid.circuit_prompt.protocol("WM_DELETE_WINDOW", self.exit_circuit_prompt)

        cir_wid.cir_labelframe = LabelFrame(cir_wid.circuit_prompt, font=self.active_font, text="Add New Circuit")
        cir_wid.cir_labelframe.grid(sticky='news', pady=(10, 10), padx=(10, 10))

        cir_wid.circuit_name_entry = LabeledEntry(cir_wid.cir_labelframe, label_text="Circuit Name:",
                                                  entry_text="Custom Circuit",
                                                  entry_width=25, entry_height=1, widget_font=self.active_font)
        cir_wid.circuit_name_entry.grid(row=0, column=0, sticky='ns', columnspan=2)

        cir_wid.circuit_image_entry = LabeledEntry(cir_wid.cir_labelframe, label_text="Circuit Image filename:",
                                                    entry_text="blank_circuit.png",
                                                    entry_width=20, entry_height=1, widget_font=self.active_font)
        cir_wid.circuit_image_entry.grid(row=1, column=0, sticky='ns', columnspan=2)

        cir_wid.circuit_inputs_var = StringVar(value="0")
        cir_wid.circuit_inputs_var.trace("w", self.make_input_entry_list)
        cir_wid.circuit_inputs_entry = LabeledEntry(cir_wid.cir_labelframe, label_text="Num. Inputs:",
                                                    entry_var=cir_wid.circuit_inputs_var,
                                                    entry_width=2, entry_height=1, widget_font=self.active_font)
        cir_wid.circuit_inputs_entry.grid(row=2, column=0, sticky='ew')

        cir_wid.circuit_outputs_var = StringVar(value='0')
        cir_wid.circuit_outputs_var.trace("w", self.make_output_entry_list)
        cir_wid.circuit_outputs_entry = LabeledEntry(cir_wid.cir_labelframe, label_text="Num. Outputs:",
                                                    entry_text="0", entry_var=cir_wid.circuit_outputs_var,
                                                    entry_width=2, entry_height=1, widget_font=self.active_font)
        cir_wid.circuit_outputs_entry.grid(row=2, column=1, sticky='ew')

        button = Button(cir_wid.cir_labelframe, text="Done", font=self.active_font, command=self.confirm_circuit_prompt)
        button.grid(row=4, column=0, columnspan=2)

    def exit_circuit_prompt(self) -> None:
        self.widgets_custom_circuit.circuit_prompt.grab_release()
        self.widgets_custom_circuit.circuit_prompt.destroy()
        self.widgets_custom_circuit.circuit_prompt.update()
        self.gui_close_circuit_builder()

    def confirm_circuit_prompt(self) -> None:
        cir_wid = self.widgets_custom_circuit
        cir_wid.circuit_prompt.grab_release()
        cir_wid.circuit_prompt.destroy()
        cir_wid.circuit_prompt.update()
        self.add_new_circuit()
        cir_wid.circuits.append(cir_wid.active_circuit)
        self.gui_close_circuit_builder()

    def add_new_circuit(self) -> None:
        """Adds new circuit button and records circuit information"""
        # If no inputs or no outputs have been specified, then this is not a valid circuit
        cir_wid = self.widgets_custom_circuit
        try:
            if int(cir_wid.circuit_inputs_var.get()) == 0 or int(cir_wid.circuit_outputs_var.get()) == 0:
                self.circuit_error_prompt("Invalid Circuit! Must have >= 1 input and >= 1 output", 35, 4)
                return
        except ValueError:
            self.circuit_error_prompt("Input and Outputs must be integers.", 35, 4)
            return

        if self.circuit_io_is_undefined():
            self.circuit_error_prompt("At least one Input/Output gate is undefined. "
                                      "Associate each circuit in/out with a gate in the circuit to save the circuit.",
                                      45, 2)
            return

        cir_wid.active_circuit.set_label(cir_wid.circuit_name_entry.get())
        cir_wid.active_circuit.set_image_file(join_folder_file(CIRCUIT_IMG_FOLDER, cir_wid.circuit_image_entry.get()))
        for (i, entry) in enumerate(cir_wid.cir_inp_names):
            # If input name entry is blank or the same as another entry, just give it a stock name
            if entry.get() == "" or (i < len(cir_wid.cir_inp_names) and entry.get() in cir_wid.cir_inp_names[i + 1:]):
                label = str(i)
            else:
                label = entry.get()

        for (i, entry) in enumerate(cir_wid.cir_out_names):
            # If output name entry is blank or the same as another entry, just give it a stock name
            if entry.get() == "" or (i < len(cir_wid.cir_out_names) and entry.get() in cir_wid.cir_out_names[i + 1:]):
                label = str(i)
            else:
                label = entry.get()

        cir_wid.circuit_pi = PhotoImage(file=join_folder_file(CIRCUIT_IMG_FOLDER, cir_wid.circuit_image_entry.get()))
        cir_wid.custom_circuit_pis.append(cir_wid.circuit_pi)
        cir_wid.custom_circuit_button = LabeledButton(cir_wid.screen_circuit.frame, label_direction=S,
                                                      button_content=cir_wid.circuit_pi,
                                                      cmd=FunctionCallback(self.set_active_fn_custom_circuit,
                                                                           len(cir_wid.circuit_buttons)),
                                                      label_text=cir_wid.active_circuit.get_label(),
                                                      this_font=self.active_font, background='white')

        cir_wid.custom_circuit_button.grid(row=0, column=len(cir_wid.circuit_buttons), sticky='nw', padx=(5, 0), pady=(10, 0))
        cir_wid.circuit_buttons.append(cir_wid.custom_circuit_button)
        cir_wid.new_circuit_button.grid_configure(column=len(cir_wid.circuit_buttons))

        self.gates.register_circuit(cir_wid.active_circuit,
                                    callback=FunctionCallback(self.set_active_fn_custom_circuit,
                                                              len(cir_wid.circuit_buttons)),
                                    image_file=join_folder_file(CIRCUIT_IMG_FOLDER, cir_wid.circuit_image_entry.get()))

    def make_input_entry_list(self, *args) -> None:
        cir_wid = self.widgets_custom_circuit
        if cir_wid.circuit_input_lbframe is not None:
            cir_wid.circuit_input_lbframe.destroy()

        cir_wid.circuit_input_lbframe = LabelFrame(cir_wid.cir_labelframe, font=self.active_font, text="Circuit Inputs")
        cir_wid.circuit_input_lbframe.grid(row=3, column=0, sticky='news')
        cir_wid.cir_inp_names = []
        try:
            row = int(cir_wid.circuit_inputs_var.get())
            for i in range(row):
                entry = LabeledEntry(cir_wid.circuit_input_lbframe, label_text="Input " + str(i), entry_text="",
                                     entry_width=12, entry_height=1, widget_font=self.active_font)
                entry.grid(row=i, column=0, sticky='news')
                cir_wid.cir_inp_names.append(entry)
                circuit_confirm_output_names = Button(cir_wid.circuit_input_lbframe, text="Confirm",
                                                      font=self.active_font,
                                                      command=self.confirm_in_gate_names)
                circuit_confirm_output_names.grid(sticky='ns', columnspan=2)

        except ValueError:
            return

    def make_output_entry_list(self, *args) -> None:
        cir_wid = self.widgets_custom_circuit
        if cir_wid.circuit_output_lbframe is not None:
            cir_wid.circuit_output_lbframe.destroy()

        cir_wid.circuit_output_lbframe = LabelFrame(cir_wid.cir_labelframe, font=self.active_font, text="Circuit Outputs")
        cir_wid.circuit_output_lbframe.grid(row=3, column=1, sticky='news')
        cir_wid.cir_out_names = []
        try:
            row = int(cir_wid.circuit_outputs_var.get())
            for i in range(row):
                entry = LabeledEntry(cir_wid.circuit_output_lbframe, label_text="Output " + str(i), entry_text="",
                                     entry_width=12, entry_height=1, widget_font=self.active_font)
                entry.grid(row=i, column=1, sticky='news')
                cir_wid.cir_out_names.append(entry)
            circuit_confirm_output_names = Button(cir_wid.circuit_output_lbframe, text="Confirm", font=self.active_font,
                                                  command=self.confirm_out_gate_names)
            circuit_confirm_output_names.grid(sticky='ns', columnspan=2)
        except ValueError:
            return

    def confirm_in_gate_names(self) -> None:
        """Adds the Circuit input cascade to the context window while in the circuit builder mode"""
        cir_wid = self.widgets_custom_circuit
        cir_wid.circuit_context_menu.delete(cir_wid.circuit_context_in_index)
        if cir_wid.circuit_context_in_index < cir_wid.circuit_context_out_index:
            cir_wid.circuit_context_out_index -= 1

        cir_wid.active_circuit.reset_inputs()
        for label in cir_wid.cir_inp_names:
            cir_wid.active_circuit.set_circuit_input(label.get())

        cir_wid.circuit_context_menu.add_cascade(label='Set as Circuit Input',
                                              menu=make_sub_menu(cir_wid.circuit_context_menu,
                                                                 [label.get() for label in cir_wid.cir_inp_names],
                                                                 [FunctionCallback(self.associate_label_and_gate, "in",
                                                                                   label.get()) for label in
                                                                  cir_wid.cir_inp_names],
                                                                 font=self.active_font))
        cir_wid.circuit_context_in_index = cir_wid.circuit_context_menu.index("end")

    def confirm_out_gate_names(self) -> None:
        """Adds the Circuit output cascade to the context window while in the circuit builder mode"""
        cir_wid = self.widgets_custom_circuit
        cir_wid.circuit_context_menu.delete(cir_wid.circuit_context_out_index)
        if cir_wid.circuit_context_out_index < cir_wid.circuit_context_in_index:
            cir_wid.circuit_context_in_index -= 1

        cir_wid.active_circuit.reset_outputs()
        for label in cir_wid.cir_out_names:
            cir_wid.active_circuit.set_circuit_output(label.get())

        cir_wid.circuit_context_menu.add_cascade(label='Set as Circuit Output',
                                              menu=make_sub_menu(cir_wid.circuit_context_menu,
                                                                 [label.get() for label in cir_wid.cir_out_names],
                                                                 [FunctionCallback(self.associate_label_and_gate, "out",
                                                                                   label.get()) for label in
                                                                  cir_wid.cir_out_names],
                                                                 font=self.active_font))
        cir_wid.circuit_context_out_index = cir_wid.circuit_context_menu.index("end")

    def associate_label_and_gate(self, mode: Literal["in", "out"], label: str) -> None:
        """Sets the BaseGate to the appropriate label"""
        can_wid = self.widgets_canvas
        cir_wid = self.widgets_custom_circuit
        if len(can_wid.icb_selected_gates) > 0:
            if mode == "in":
                cir_wid.active_circuit.set_circuit_input(label, can_wid.icb_selected_gates[-1][1])
            elif mode == "out":
                cir_wid.active_circuit.set_circuit_output(label, can_wid.icb_selected_gates[-1][1])
        else:
            log_msg(INFO, "No gates selected for i/o")

    def circuit_io_is_undefined(self) -> bool:
        """Returns if any circiut input or output slot is undefined"""
        cir_wid = self.widgets_custom_circuit
        for connection in cir_wid.active_circuit.connections:
            for gate_label in cir_wid.active_circuit.connections[connection]:
                if cir_wid.active_circuit.connections[connection][gate_label] is None:
                    return True
        return False

    def circuit_error_prompt(self, msg: str, chars_wide: int, chars_high: int) -> None:
        self.circuit_error = Toplevel(self)
        # self.circuit_error.resizable(False, False)
        # Make window modal, meaning actions won't take effect while this window is open
        self.circuit_error.wait_visibility()
        self.circuit_error.grab_set()
        self.circuit_error.transient(self)

        self.circuit_error.title("Error")
        frame = Frame(self.circuit_error)
        frame.grid()
        label = Text(frame, font=self.active_font, wrap=WORD, width=chars_wide, height=chars_high)
        label.insert(INSERT, msg)
        label.grid()
        btn = Button(frame, text="Done", font=self.active_font, command=self.exit_circuit_error)
        btn.grid()

    def exit_circuit_error(self) -> None:
        self.circuit_error.grab_release()
        self.circuit_error.destroy()
        self.circuit_error.update()

    def gui_build_top_menu(self) -> None:
        """Build the top menu bar"""
        can_wid = self.widgets_canvas
        can_wid.icb_menubar = Menu(self)
        file_menu = Menu(can_wid.icb_menubar, tearoff=0)
        edit_menu = Menu(can_wid.icb_menubar, tearoff=0)
        help_menu = Menu(can_wid.icb_menubar, tearoff=0)

        file_menu.add_command(label="Open...", command=self.open, font=self.font_top)
        file_menu.add_command(label="Save", command=self.save, font=self.font_top)
        file_menu.add_command(label="Save as...", command=self.save_as, font=self.font_top)
        file_menu.add_command(label="Preferences", command=self.preference_prompt, font=self.font_top)
        file_menu.add_command(label="Clear", command=self.clear, font=self.font_top)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit, font=self.font_top)

        can_wid.icb_menubar.add_cascade(label="File", menu=file_menu, font=self.font_top)

        edit_menu.add_command(label="Play", command=self.play, font=self.font_top)
        edit_menu.add_command(label="Pause", command=self.pause, font=self.font_top)
        edit_menu.add_command(label="Toggle", command=self.toggle_play_pause, font=self.font_top)
        edit_menu.add_command(label="Reset", command=self.reset, font=self.font_top)
        can_wid.icb_menubar.add_cascade(label="Run", menu=edit_menu, font=self.font_top)

        help_menu.add_command(label="Help", command=self.help, font=self.font_top)

        can_wid.icb_menubar.add_cascade(label="Help", menu=help_menu, font=self.font_top)

        self.config(menu=can_wid.icb_menubar)

    def on_resize(self, event: Event) -> None:
        print("on_resize({0} {1})".format(event.width, event.height))

        # self.widgets_input_selection.bordered_frame.config(width=self.input_selection_screen_width, height=event.height)
        # self.widgets_input_selection.screen_is.config(width=self.input_selection_screen_width - self.border_width, height=event.height)
        # self.widgets_canvas.screen_icb.config(width=event.width - self.input_selection_screen_width,
        #                                       height=event.height)
        cir_wid = self.widgets_custom_circuit
        self.widgets_custom_circuit.screen_circuit.resize(width=self.width - self.input_selection_screen_width,
                                                          height=self.circuit_screen_height - self.border_width - cir_wid.circuit_scrollbar_height)

        # self.update_idletasks()

    def gui_build_all(self) -> None:
        self.gui_build_top_menu()
        self.gui_build_icb()
        self.gui_build_input_selection_menu()
        self.update_idletasks()
        self.gui_build_circuit_pane()
        self.configure_widgets()
        # self.bind('<Configure>', self.on_resize)

    def gui_reconfig_dimensions(self):
        """Updates the width and height of the application"""
        is_wid = self.widgets_input_selection
        can_wid = self.widgets_canvas
        cir_wid = self.widgets_custom_circuit

        is_wid.bordered_frame.config(height=self.height)
        is_wid.screen_is.config(height=self.height)

        can_wid.screen_icb.config(width=self.width - self.input_selection_screen_width,
                               height=self.height - self.circuit_screen_height)
        cir_wid.circuit_border_frame.config(width=self.width - self.input_selection_screen_width - self.border_width,
                                         height=self.circuit_screen_height)
        cir_wid.screen_circuit.resize(width=self.width - self.input_selection_screen_width,
                                      height=self.circuit_screen_height - self.border_width - cir_wid.circuit_scrollbar_height)

        is_wid.is_edit_table.config_dims(height=self.height - is_wid.is_button_frame.winfo_height() - 30,
                                         width=self.input_selection_screen_width - 30)
        self.geometry(str(self.width) + "x" + str(self.height))

    def toggle_line_colors(self) -> None:
        LogicGate.line_colors_on = not LogicGate.line_colors_on
        for func in self.gates.keys():
            for gate in self.gates[func].get_active_gates():
                gate.update_line_colors()

    def preference_prompt(self):
        """Builds Preference Window"""
        pref_wid = self.widgets_preferences
        pref_wid.preference_toplevel = Toplevel(self)
        pref_wid.preference_toplevel.resizable(False, False)
        pref_wid.preference_toplevel.title("Preferences")
        # Make window modal, meaning actions won't take effect while this window is open
        pref_wid.preference_toplevel.wait_visibility()
        pref_wid.preference_toplevel.grab_set()
        pref_wid.preference_toplevel.transient(self)
        # Resolution Preferences #######################################################################################
        res_frame = Frame(pref_wid.preference_toplevel)
        res_frame.pack(side=TOP, expand=True, fill=BOTH)
        res_label = Label(res_frame, text=" Set Resolution:", font=self.active_font)
        res_label.pack(side=LEFT, padx=(5, 0), pady=(10, 5))

        pref_wid.res_width_var = StringVar(value=str(self.winfo_width()))
        pref_wid.res_width_entry = Entry(res_frame, textvariable=pref_wid.res_width_var, font=self.active_font, width=4)
        pref_wid.res_width_entry.pack(side=LEFT, padx=(5, 0), pady=(0, 0))

        res_sep_label = Label(res_frame, text="x", font=self.active_font)
        res_sep_label.pack(side=LEFT, padx=(5, 5), pady=(0, 0))

        pref_wid.res_height_var = StringVar(value=str(self.winfo_height()))
        pref_wid.res_height_entry = Entry(res_frame, textvariable=pref_wid.res_height_var, font=self.active_font, width=4)
        pref_wid.res_height_entry.pack(side=LEFT, padx=(0, 0), pady=(0, 0))
        # Color Preferences ############################################################################################
        color_frame = Frame(pref_wid.preference_toplevel)
        color_frame.pack(side=TOP, expand=True, fill=BOTH, padx=(0, 0), pady=(0, 5))

        pref_wid.color_labelentry = LabeledEntry(master=color_frame, entry_width=7,
                                                 label_text="Canvas color (name or #XXXXXX):",
                                                 entry_text=pref_wid.background_color.get(), widget_font=self.active_font)
        pref_wid.color_labelentry.pack(side=LEFT, padx=(10, 0), pady=(5, 5))
        # Toggle Line Colors ###########################################################################################
        line_colors_frame = Frame(pref_wid.preference_toplevel)
        line_colors_frame.pack(side=TOP, expand=True, fill=BOTH, padx=(12, 0), pady=(0, 5))

        line_colors_label = Label(line_colors_frame, text="Enable Line Colors:", font=self.active_font)
        line_colors_label.pack(side=LEFT)

        pref_wid.line_colors_checkbox = Checkbutton(line_colors_frame, command=self.toggle_line_colors,
                                                    font=self.active_font)
        if LogicGate.line_colors_on:
            pref_wid.line_colors_checkbox.select()
        pref_wid.line_colors_checkbox.pack(side=LEFT)
        # Font Preferences #############################################################################################
        font_frame = Frame(pref_wid.preference_toplevel)
        font_frame.pack(side=TOP, padx=(15, 15), pady=(0, 5))
        # Font Family ##################################################################################################
        font_family_frame = Frame(font_frame)
        font_family_frame.pack(side=LEFT)
        font_family_label = Label(font_family_frame, text="Font Family", font=self.active_font)
        font_family_label.pack(side=TOP)
        pref_wid.font_family_listbox = Listbox(font_family_frame, font=self.active_font, selectmode=SINGLE,
                                               exportselection=False)

        for family in pref_wid.font_families:
            pref_wid.font_family_listbox.insert(END, family)

        pref_wid.font_family_listbox.pack(side=LEFT, fill=BOTH)

        font_family_scrollbar = Scrollbar(font_family_frame)
        font_family_scrollbar.pack(side=RIGHT, fill=BOTH)

        pref_wid.font_family_listbox.config(yscrollcommand=font_family_scrollbar.set)
        font_family_scrollbar.config(command=pref_wid.font_family_listbox.yview)
        # Font Size ####################################################################################################
        font_sizes = ['10', '11', '12', '13', '14', '15', '16']
        font_size_frame = Frame(font_frame)
        font_size_frame.pack(side=RIGHT, fill=BOTH)
        font_size_label = Label(font_size_frame, text="Font Size", font=self.active_font)
        font_size_label.pack(side=TOP)
        pref_wid.font_size_listbox = Listbox(font_size_frame, font=self.active_font, height=len(font_sizes),
                                             selectmode=SINGLE, exportselection=False)

        for font_size in font_sizes:
            pref_wid.font_size_listbox.insert(END, font_size)

        pref_wid.font_size_listbox.pack(side=LEFT, expand=True, fill=BOTH)
        font_size_scrollbar = Scrollbar(font_size_frame)
        font_size_scrollbar.pack(side=RIGHT, fill=BOTH)

        pref_wid.font_size_listbox.config(yscrollcommand=font_size_scrollbar.set)
        font_size_scrollbar.config(command=pref_wid.font_size_listbox.yview)
        ################################################################################################################
        preference_button_frame = Frame(pref_wid.preference_toplevel)
        preference_button_frame.pack(side=BOTTOM, expand=True, fill=BOTH, pady=(15, 5))
        preference_done_button = Button(preference_button_frame, text="Done",
                                        command=self.close_preference_prompt,
                                        font=self.active_font)
        # self.preference_done_button.grid(row=3)
        preference_done_button.pack()
        self.wait_window(pref_wid.preference_toplevel)

    def close_preference_prompt(self) -> None:
        # Update settings...
        pref_wid = self.widgets_preferences
        width, height = int(pref_wid.res_width_var.get()), int(pref_wid.res_height_var.get())
        if width >= 800 and height >= 600:
            self.width = int(pref_wid.res_width_entry.get())
            self.height = int(pref_wid.res_height_entry.get())
            self.gui_reconfig_dimensions()
        else:
            log_msg(WARNING, "Resolution must be at least 800x600")

        pref_wid.background_color = pref_wid.color_labelentry
        self.widgets_canvas.screen_icb.config(background=pref_wid.background_color.get())

        # Set active font
        # If a font family was selected by the list box, get as a list and use as an index to get the font family
        family = pref_wid.font_family_listbox.curselection()
        if family != ():
            pref_wid.font_family = pref_wid.font_family_listbox.get(family[0])

        size = pref_wid.font_size_listbox.curselection()
        if size != ():
            pref_wid.font_size = int(pref_wid.font_size_listbox.get(size[0]))

        if family != () or size != ():  # If either font family/size change, update app font and rebuild app
            self.update_font(pref_wid.font_family, pref_wid.font_size)

        self.save_preferences()

        # Reset popup state
        pref_wid.preference_toplevel.grab_release()
        pref_wid.preference_toplevel.destroy()
        pref_wid.preference_toplevel.update()

    def save_preferences(self) -> None:
        doc = tomlkit.document()
        settings = tomlkit.table()
        settings.add("Width", self.width)
        settings.add("Height", self.height)
        settings.add("Background", self.widgets_preferences.background_color.get())
        settings.add("Font", [self.active_font["family"], self.active_font["size"],
                              self.active_font["weight"], self.active_font["slant"]])
        settings.add("Colors", LogicGate.line_colors_on)
        doc["Settings"] = settings
        with open(self.preference_file_name, mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(doc, fp)
            log_msg(INFO, "Saved settings to: " + self.preference_file_name)

    def load_preferences(self) -> None:
        if not os.path.exists(self.preference_file_name):
            log_msg(INFO, "Using default settings")
            return

        with open(self.preference_file_name, mode="rt", encoding="utf-8") as fp:
            pref_wid = self.widgets_preferences
            document = tomlkit.load(fp)
            self.width = document["Settings"]["Width"]
            self.height = document["Settings"]["Height"]
            pref_wid.background_color.set(document["Settings"]["Background"])
            LogicGate.line_colors_on = document["Settings"]["Colors"]
            fonts_attrs = document["Settings"]["Font"]
            self.active_font = Font(family=fonts_attrs[0], size=fonts_attrs[1],
                                    weight=fonts_attrs[2], slant=fonts_attrs[3])

            self.gui_reconfig_dimensions()
            self.widgets_canvas.screen_icb.config(background=self.widgets_preferences.background_color.get())
            self.update_font(fonts_attrs[0], fonts_attrs[1])
            log_msg(INFO, "Loaded settings from: " + self.preference_file_name)

    def timer_prompt(self):
        timer_wid = self.widgets_timer
        if timer_wid.selected_timer is None:
            return

        self.reset()
        timer_wid.timer_popup = Toplevel(self)
        timer_wid.timer_popup.resizable(False, False)
        timer_wid.timer_popup.title("Editing " + timer_wid.selected_timer.get_label())
        # Make window modal, meaning actions wont take effect while this window is open
        timer_wid.timer_popup.wait_visibility()
        timer_wid.timer_popup.grab_set()
        timer_wid.timer_popup.transient(self)

        timer_wid.timer_state_intvar.set(timer_wid.selected_timer.output())
        timer_wid.timer_entry_strvar.set(str(timer_wid.selected_timer.get_rate()))

        timer_labelframe = LabelFrame(timer_wid.timer_popup, text="Set Clock Properties", font=self.font_top)
        timer_labelframe.grid(padx=(5, 5), pady=(0, 5))

        entry_frame = Frame(timer_labelframe)
        entry_frame.grid(row=0, column=0, padx=(10, 10), pady=(5, 10))

        timer_entry_label = Label(entry_frame, text="Timer Update Rate (seconds):", font=self.active_font)
        timer_entry_label.grid(row=0, column=0, padx=(0, 5), pady=(0, 0), sticky=W)
        timer_wid.timer_entry = Entry(entry_frame, textvariable=timer_wid.timer_entry_strvar, width=5, font=self.active_font)
        timer_wid.timer_entry.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        cb_frame = Frame(timer_labelframe)
        cb_frame.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))
        timer_state_label = Label(cb_frame, text="Set Timer State (Default On):", font=self.active_font)
        timer_state_label.grid(row=0, column=0, padx=(0, 5))
        timer_wid.timer_state_cb = Checkbutton(cb_frame, variable=timer_wid.timer_state_intvar, font=self.active_font)
        timer_wid.timer_state_cb.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky=W)

        timer_done_button = Button(timer_labelframe, text="Done", command=self.close_timer_prompt,
                                   font=self.active_font)
        timer_done_button.grid(row=2, column=0)
        self.wait_window(timer_wid.timer_popup)

    def close_timer_prompt(self):
        # Update timer settings
        timer_wid = self.widgets_timer
        timer_wid.selected_timer.set_rate(float(timer_wid.timer_entry_strvar.get()))
        timer_wid.selected_timer.set_output(timer_wid.timer_state_intvar.get())
        # Reset popup state
        timer_wid.selected_timer = None
        timer_wid.timer_state_intvar = IntVar(value=True)
        timer_wid.timer_entry_strvar.set(str(self.default_update_rate))

        timer_wid.timer_popup.grab_release()
        timer_wid.timer_popup.destroy()
        timer_wid.timer_popup.update()

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
        sys.exit(0)

    def run(self) -> None:
        self.gui_build_all()
        self.load_preferences()
        self.mainloop()


class CheckbuttonTable1(LabelFrame):
    """Scrollable LabelFrame which stores entries corresponding to each power gate. Each entry has a checkbox that,
    when clicked, toggles the output of the gate. Can also be right-clicked to change the name of the gate."""

    def __init__(self, parent, return_focus_to: Widget, this_font: Font, *args, **kwargs):
        LabelFrame.__init__(self, master=parent, background='white', font=this_font, *args,  **kwargs)
        self.canvas = ResizingCanvas(self, ,highlightthickness=0, background='white')
        self.frame = Frame(self.canvas, background='white')
        self.vsb = Scrollbar(self, orient="vertical", command=self.canvas.yview())
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.checkbox_padding = {"padx": (10, 0), "pady": (5, 5)}  # The padding applied to each entry
        self.return_focus_to = return_focus_to
        self.entries = []  # List holding list of TableCheckbuttons

        self.this_font = this_font
        self.null = True

        self.vsb.grid(row=0, column=1, sticky='nse', pady=(0, 0))
        self.canvas.grid(row=0, column=0, sticky='nws', padx=(0, 0))

        self.canvas.create_window((1, 1), window=self.frame, anchor="nw", tags="self.frame")
        self.frame.bind("<Configure>", self.on_frame_configure)

        self.empty_text_label = Label(self.frame, bg="white", text="No Inputs...", font=this_font)
        self.empty_text_label.grid(row=0, column=0, sticky='')

    def config_dims(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        self.config(width=width, height=height)
        self.canvas.config(width=self.winfo_reqwidth(), height=self.winfo_reqheight() - 25)
        self.frame.config(width=self.winfo_reqwidth() - 20, height=self.winfo_reqheight())

    def add_entry(self, gate) -> None:
        if self.null:
            self.empty_text_label.grid_forget()
            self.null = False
        tbl_entry = TableCheckbutton(self.frame, gate, self.return_focus_to,
                                     this_font=reconfig_font(self.this_font, offset=-2), popup_font=self.this_font,
                                     checkbutton_padding=self.checkbox_padding)
        tbl_entry.grid(row=len(self.entries), sticky='')
        self.entries.append(tbl_entry)

    def del_entry(self, row: int) -> None:
        """Removes a gate entry from the table"""
        if abs(row) > len(self.entries):
            return
        row = abs(row)
        entry = self.entries[row]
        entry.grid_forget()
        entry.destroy()
        self.entries.remove(entry)

        for (i, entry) in enumerate(self.entries):
            entry.grid_configure(row=i)

        if len(self.entries) == 0:
            self.empty_text_label.grid()
            self.null = True

    def get_row(self, row: int) -> Optional[int]:
        """Returns checkbox value at row"""
        if abs(row) > len(self.entries):
            return None
        return self.entries[row].get()

    def del_gate_entry(self, gate) -> None:
        """Deletes the entry matching gate"""
        for i in range(len(self.entries)):
            if self.entries[i].gate == gate:
                self.del_entry(i)
                return

    def set_focus_widget(self, widget: Widget):
        """Sets the Widget that should receive input focus after the checkbox is clicked."""
        # By default, after clicking a checkbox, it would recieve focus from tk and cause the keyboard shortcuts
        # to not work
        self.return_focus_to = widget
        for entry in self.entries:
            entry.set_focus_widget(widget)

    def clear(self) -> None:
        """Deletes all entries"""
        for entry in self.entries:
            entry.grid_forget()
            entry.destroy()

        self.entries.clear()

        self.empty_text_label.grid()
        self.null = True

    def set_font(self, new_font: Font) -> None:
        """Updates the font of the widget and the font of the entries"""
        self.config(font=new_font)
        self.this_font = new_font
        self.empty_text_label.config(font=new_font)
        for entry in self.entries:
            entry.set_font(reconfig_font(self.this_font, offset=-2))

        self.update_idletasks()

    def on_frame_configure(self, event: Event) -> None:
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.config(width=self.winfo_reqwidth() - 25)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))




if __name__ == "__main__":
    # app = Application()
    # app.run()
    tk = Tk()
    tk.geometry("800x600")
    tk.minsize(800, 600)
#
    tk.rowconfigure(0, weight=1)
    # tk.rowconfigure(1, weight=0)
    # tk.columnconfigure(0, weight=1)
    # tk.columnconfigure(1, weight=0)


    cbt = CheckbuttonTable1(tk, None, ("Calibri", 14), background='white')
    cbt.grid(row=0, column=0, sticky=news)

    rc = ScrollableHFrame(tk, this_font=("Calibri", 14), bg_color='red', width=800, height=600)
    rc.grid(row=0, column=0, sticky='news')
    rc.grid_rowconfigure(0, weight=1)
    rc.grid_rowconfigure(1, weight=1)
    rc.grid_columnconfigure(0, weight=1)
    rc.grid_propagate(False)

    tk.mainloop()

#
    #c = ResizingCanvas(tk, color='red', bb_width=600, bb_height=400, scroll_width=3000, scroll_height=2000)
    #c.grid(row=0, column=0, sticky='news')
#
    #f = Frame(tk, background='black', width=200, height=600)
    #f.grid(row=0, column=1, sticky='nesw', rowspan=2)
    #f.grid_rowconfigure(0, weight=1)
    #f.grid_propagate(False)
#
    #i = Frame(f, background='white', width = 196, height = 600)
    #i.grid(sticky='nesw', padx=(4, 0))
    #i.grid_rowconfigure(1, weight=1)
#
    #lb = LabelFrame(i, width=196, height=300, background='pink', text="buttons")
    #lb.grid(row=0, column=0)
#
    #rb = LabelFrame(i, width=196, height=300, background='cyan', text="Table")
    #rb.grid(row=1, column=0, sticky='news')
#
    #b = Frame(tk, background='blue', width=600, height=200)
    #b.grid(row=1, column=0, sticky='nesw')
    #b.grid_propagate(False)
#
    #sg = Sizegrip(tk)
    #sg.grid(row=1, column=1, sticky=SE)
#
    #p1 = PhotoImage(file="images/gates/and.png")
    #input_id1 = c.create_image(500, 500, image=p1)
    #p2 = PhotoImage(file="images/gates/and.png")
    #input_id2 = c.create_image(3000, 3000, image=p2)
    #c.resize_scroll_region(1, 1)
#
    #tk.after(500, None)
#
    ## c.condense()
#
#
    #tk.mainloop()



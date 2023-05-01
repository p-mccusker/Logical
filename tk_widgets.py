########################################################################################################################
# File: tk_widgets.py
# Author: Peter McCusker
# License:
# Date: 01/04/2023
# Description: Defines Tk widgets to be used in the circuit application
########################################################################################################################
import tkinter
from tkinter import scrolledtext

from logic_gate import *


def get_widget_bottom_y(widget: Widget) -> int:
    """Returns the bottom y coordinate of widget"""
    return widget.winfo_rooty() + widget.winfo_reqheight()


def get_widget_bottom_x(widget: Widget) -> int:
    """Returns the bottom y coordinate of widget"""
    return widget.winfo_rootx() + widget.winfo_reqwidth()


def reconfig_font(this_font: font.Font, offset: int, weight: Optional[str] = None,
                  slant: Optional[str] = None) -> font.Font:
    """Creates a new font based off this_font with options modified"""
    return font.Font(family=this_font["family"],
                     size=this_font["size"] + offset,
                     weight=this_font["weight"] if weight is None else weight,
                     slant=this_font["slant"] if slant is None else slant)


class Popup(Menu):
    """Two types of nested menu item invoking. 'click&drag' - click
    and hold the menu item, move pointer to sub-menu item. Release the
    button when it is over the sub-menu item. 'click&move' - click the
    menu item (sub-menu appears), click the sub-menu item.

    Controlled by *menumode* keyword arguemnt. 0 - click&move, 1 -
    click&drag"""
    menu_mode_default = 0

    def __init__(self, *args, menu_mode=None, **kwargs):
        super(Popup, self).__init__(*args, **kwargs)
        menu_mode = self.menu_mode_default if menu_mode is None else menu_mode
        if menu_mode:
            self.bind('<FocusOut>', self.on_focus_out)
        else:
            self.bind('<Enter>', self.on_enter)
        self.bind('<Escape>', self.on_focus_out)

    def on_enter(self, event):
        self.focus_set()

    def post(self, *args, **kwargs):
        super(Popup, self).post(*args, **kwargs)
        self.focus_set()

    def on_focus_out(self, event=None):
        self.unpost()


def make_sub_menu(parent: Menu, labels: list[str], callbacks: list[Callable] = None, **kwargs) -> Popup:
    sub = Popup(parent, tearoff=0, **kwargs)
    for (label1, cb) in zip(labels, callbacks):
        sub.add_command(label=label1, command=cb, )
    return sub


class PictureDescription(Frame):
    def __init__(self, *args, img: PhotoImage, desc_text: str, text_width: int, text_height: int, this_font: font.Font,
                 scrollbar_on: bool = True, **kwargs):
        Frame.__init__(self, *args, **kwargs)
        self.img = img
        self.img_label = Label(self, image=self.img)
        self.this_font = this_font
        self.img_label.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky='nsw')
        self.scrollbar_on = scrollbar_on
        if scrollbar_on:
            self.description = scrolledtext.ScrolledText(self, wrap=tkinter.WORD, width=text_width, height=text_height,
                                                         font=self.this_font)
        else:
            self.description = tkinter.Text(self, wrap=tkinter.WORD, width=text_width, height=text_height,
                                            font=self.this_font)
        self.description.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky='nse')
        self.description.insert(tkinter.INSERT, desc_text)
        self.description.configure(state='disabled')

    def set_font(self, new_font: font.Font) -> None:
        self.this_font = new_font
        self.description.config(font=self.this_font)


class LabeledEntry(Frame):
    """Widget containing a label to the left of a entry"""

    def __init__(self, *arg, label_text: str = "", entry_text: str = "", entry_var: Optional[StringVar] = None,
                 entry_width: Optional[int] = None, entry_height: int = 1,
                 widget_font: Optional[str | font.Font] = None,
                 label_background: Optional[str] = None, label_foreground: Optional[str] = None,
                 disabled: bool = False, **kwargs):
        Frame.__init__(self, *arg, **kwargs)
        self.label = Label(self, text=label_text, background=label_background, foreground=label_foreground)
        self.label.grid(row=0, column=0, sticky='news')
        self.entry_var = StringVar(value=entry_text) if entry_var is None else entry_var
        if not disabled:
            self.entry = Entry(self, textvariable=self.entry_var, background='white', width=entry_width)
        else:
            self.entry = tkinter.Text(self, font=widget_font, background='white', width=20, wrap=tkinter.WORD,
                                      height=entry_height)
            self.entry.insert(tkinter.INSERT, entry_text)
            self.entry.configure(state='disabled')

        if entry_width is not None:
            self.entry.config(width=entry_width)

        if widget_font is not None:
            self.entry.config(font=widget_font)
            self.label.config(font=widget_font)

        self.entry.grid(row=0, column=1)

    def set_label(self, text: str) -> None:
        self.label.config(text=text)

    def set_label_padding(self, **kwargs) -> None:
        self.label.grid(**kwargs)

    def set_entry_padding(self, **kwargs) -> None:
        self.entry.grid(**kwargs)

    def set_font(self, new_font: font.Font) -> None:
        self.entry.config(font=new_font)
        self.label.config(font=new_font)

    def get(self) -> str:
        """Returns checkbox value"""
        return self.entry_var.get()

    def strvar_trace(self, mode: str, cb: Callable) -> None:
        self.entry_var.trace(mode, cb)


class TableCheckbutton(Frame):
    """Widget with a label to the left of a checkbox. Is associated with a power gate and when clicked, toggles the
    output of this gate"""

    def __init__(self, parent: Optional[Widget], gate: LogicGate, return_focus_to: Widget, this_font: font.Font,
                 popup_font: font.Font, *args, checkbutton_padding: Optional[dict] = None, **kwargs):
        super().__init__(parent, *args, background="white", **kwargs)
        self.gate = gate
        self.return_focus_to = return_focus_to
        self.this_font = this_font
        # Popup Variables ##############
        self.popup_font = popup_font
        self.toplevel = None  # Prompt to change gate name
        self.entry_var = None
        self.popup_entry = None

        if gate is not None:  # If a gate is provided, intitalize the widget
            self.check_var = IntVar(value=gate.output())
            self.checkbutton = Checkbutton(self, variable=self.check_var, text=self.gate.get_label(),
                                           onvalue=TRUE, offvalue=FALSE, width=15, command=self.click_cb,
                                           background='white', font=this_font)
            self.checkbutton.bind("<Button-3>", self.right_click_cb)
            self.has_default_name = True
            if checkbutton_padding is not None:
                self.checkbutton.grid(row=0, column=0, sticky="w", **checkbutton_padding)
            else:
                self.checkbutton.grid(row=0, column=0, sticky="w")
        else:  # Else create a minimal widget
            self.checkbutton = Label(self.master)
            self.grid()
            self.check_var = None

    def click_cb(self):
        """Toggles output of gate and returns focus to the icb"""
        self.return_focus_to.focus_force()
        self.gate.set_output(self.check_var.get())

    def right_click_cb(self, event: Event):
        """Opens a popup prompt to edit the name of this power gate"""
        self.toplevel = Toplevel(self)
        self.toplevel.title(self.gate.get_label())
        self.toplevel.resizable(False, False)
        self.toplevel.wait_visibility()
        self.toplevel.grab_set()

        # self.toplevel.transient(self.tk)
        labelframe = LabelFrame(self.toplevel, font=self.popup_font, text="Rename: " + self.gate.get_label())
        labelframe.grid(row=0, column=0, padx=(5, 5), pady=(5, 5))
        label = Label(labelframe, font=self.popup_font, text="Set power gate name:")
        label.grid(row=0, column=0, sticky='ew', padx=(5, 5))
        self.entry_var = StringVar(value=self.gate.get_label())
        self.popup_entry = Entry(labelframe, width=10, font=self.popup_font, textvariable=self.entry_var)
        self.popup_entry.grid(row=0, column=1, sticky='ew')

        button_frame = Frame(labelframe)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 10))
        cancel_button = Button(button_frame, font=self.popup_font, text="Cancel", command=self.cancel_close_cb)
        confirm_button = Button(button_frame, font=self.popup_font, text="Done", command=self.done_close_cb)
        cancel_button.grid(row=0, column=0, padx=(10, 20))
        confirm_button.grid(row=0, column=1, padx=(0, 10))

    def cancel_close_cb(self):
        self.toplevel.grab_release()
        self.toplevel.destroy()
        self.toplevel.update()

    def done_close_cb(self):
        self.update_text(self.popup_entry.get())
        self.has_default_name = False
        self.cancel_close_cb()

    def update_text(self, text: str) -> None:
        self.gate.set_label(text)
        self.checkbutton.config(text=self.gate.get_label())

    def get(self) -> int:
        return self.check_var.get()

    def set_font(self, new_font: font.Font) -> None:
        self.checkbutton.config(font=new_font)

    def set_focus_widget(self, widget: Widget):
        self.return_focus_to = widget


class CheckbuttonTable(LabelFrame):
    """Scrollable LabelFrame which stores entries corresponding to each power gate. Each entry has a checkbox that,
    when clicked, toggles the output of the gate. Can also be right-clicked to change the name of the gate."""

    def __init__(self, parent, return_focus_to: Widget, this_font: font.Font, *args, **kwargs):
        LabelFrame.__init__(self, master=parent, background='white', font=this_font, *args, **kwargs)
        self.canvas = Canvas(self, highlightthickness=0, background='white')
        self.frame = Frame(self.canvas, background='white')
        self.vsb = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.checkbox_padding = {"padx": (10, 0), "pady": (5, 5)}  # The padding applied to each entry
        self.return_focus_to = return_focus_to
        self.entries = []  # List holding list of TableCheckbutton

        self.this_font = this_font
        self.null = True

        self.vsb.grid(row=0, column=1, sticky='nse', pady=(0, 0))
        self.canvas.grid(row=0, column=0, sticky='nws', padx=(0, 0))

        self.canvas.create_window((1, 1), window=self.frame, anchor="nw", tags="self.frame")
        self.frame.bind("<Configure>", self.on_frame_configure)

        self.empty_text_label = Label(self.frame, bg="white", text="No Power Gates...", font=this_font)
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

    def del_gate_entry(self, gate: LogicGate) -> None:
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

    def set_font(self, new_font: font.Font) -> None:
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


class ScrollableFrame(Frame):

    def __init__(self, *args, this_font: font.Font, bg_color: Optional[str] = None, **kwargs):
        Frame.__init__(self, *args, **kwargs)
        self.canvas = Canvas(self, highlightthickness=0, width=740, height=560)
                             # scrollregion=(0, 0, self.winfo_reqwidth(), self.winfo_reqheight()))
        self.frame = Frame(self.canvas)
        self.this_font = this_font
        self.scrollbar = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky='nse', pady=(0, 0))
        self.canvas.grid(row=0, column=0, sticky='nws', padx=(0, 0))

        if bg_color is not None:
            self.config(background=bg_color)
            self.canvas.config(background=bg_color)
            self.frame.config(background=bg_color)

        self.canvas.create_window((0, 0), window=self.frame, anchor="nw", tags="self.frame")
        self.frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class LabeledButton(Frame):

    def __init__(self, *args, label_direction: Literal['n', 's', 'e', 'w'], button_content: Union[PhotoImage | str],
                 cmd: Callable, label_text: str, button_sticky: str = "", label_sticky: str = "",
                 background: Optional[str] = None, this_font: Optional[font.Font] = None,  **kwargs):
        Frame.__init__(self, *args, **kwargs)
        self.this_font = this_font
        self.label = Label(self, font=self.this_font, text=label_text)
        self.button = Button(self, font=self.this_font, command=cmd)

        if label_direction == tkinter.N:
            self.label.grid(row=0, column=0, sticky=label_sticky)
            self.button.grid(row=1, column=0, sticky=button_sticky)
        elif label_direction == tkinter.S:
            self.label.grid(row=1, column=0, sticky=label_sticky)
            self.button.grid(row=0, column=0, sticky=button_sticky)
        elif label_direction == tkinter.E:
            self.label.grid(row=0, column=1, sticky=label_sticky)
            self.button.grid(row=0, column=0, sticky=button_sticky)
        elif label_direction == tkinter.W:
            self.label.grid(row=0, column=0, sticky=label_sticky)
            self.button.grid(row=1, column=1, sticky=button_sticky)
        else:
            self.label.grid()
            self.button.grid()

        if background is not None:
            self.config(background=background)
            self.label.config(background=background)
            self.button.config(background=background)

        if isinstance(button_content, str):
            self.button.config(text=button_content)
        elif isinstance(button_content, PhotoImage):
            self.button.config(image=button_content)

    def set_font(self, new_font: font.Font) -> None:
        """Updates the font of the widget and the font of the entries"""
        self.this_font = new_font
        self.label.config(font=new_font)
        self.button.config(font=new_font)

    def buttonconfig(self, **kwargs) -> None:
        self.button.configure(**kwargs)

    def labelconfig(self, **kwargs) -> None:
        self.label.configure(**kwargs)
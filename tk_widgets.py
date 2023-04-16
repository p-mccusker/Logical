########################################################################################################################
# File: tk_widgets.py
# Author: Peter McCusker
# License:
# Date: 01/04/2023
# Description: Defines Tk widgets to be used in the circuit application
########################################################################################################################
import tkinter
import tkinter.font as font
from tkinter import scrolledtext
from logic_gate import *


def get_widget_bottom_y(widget: Widget) -> int:
    """Returns the bottom y coordinate of widget"""
    return widget.winfo_rooty() + widget.winfo_reqheight()


def get_widget_bottom_x(widget: Widget) -> int:
    """Returns the bottom y coordinate of widget"""
    return widget.winfo_rootx() + widget.winfo_reqwidth()


def reconfig_font(this_font: font.Font, offset: int, weight: Optional[str] = None,
                  slant:  Optional[str] = None) -> font.Font:
    """Creates a new font based off this_font with options modified"""
    return font.Font(family=this_font["family"],
                     size=this_font["size"] + offset,
                     weight=this_font["weight"] if weight is None else weight,
                     slant=this_font["slant"] if slant is None else slant)


class PictureDescription(Frame):
    def __init__(self, img: PhotoImage, desc_text: str, text_width: int, text_height: int, this_font: font.Font,  *args, **kwargs):
        Frame.__init__(self, *args, **kwargs)
        self.img = img
        self.img_label = Label(self, image=self.img)
        self.this_font = this_font
        self.img_label.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky='nsw')
        self.description = scrolledtext.ScrolledText(self, wrap=tkinter.WORD, width=text_width, height=text_height,
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
                 entry_width: Optional[int] = None, widget_font: Optional[str | font.Font] = None, **kwargs):
        Frame.__init__(self, *arg, **kwargs)
        self.label = Label(self, text=label_text)
        self.label.grid(row=0, column=0)
        self.entry_var = StringVar(value=entry_text) if entry_var is None else entry_var
        self.entry = Entry(self, textvariable=self.entry_var, background='white')

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


class TableCheckbutton(Frame):
    """Widget with a label to the left of a checkbox. Is associated with a power gate and when clicked, toggles the
    output of this gate"""
    def __init__(self, parent: Optional[Widget], gate: InputTk, return_focus_to: Widget, this_font: font.Font,
                 popup_font: font.Font, *args, checkbutton_padding: Optional[dict] = None, **kwargs):
        super().__init__(parent, *args, background="white", **kwargs)
        self.gate = gate
        self.return_focus_to = return_focus_to
        self.this_font = this_font
        self.popup_font = popup_font

        if gate is not None:  # If a gate is provided, intitalize the widget
            self.check_var = IntVar(value=gate.output())
            self.checkbutton = Checkbutton(self, variable=self.check_var, text=self.gate.get_label(),
                                           onvalue=TRUE, offvalue=FALSE, width=10, command=self.click_cb,
                                           background='white', font=this_font)
            self.checkbutton.bind("<Button-3>", self.right_click_cb)
            self.has_default_name = True
            if checkbutton_padding is not None:
                self.checkbutton.grid(row=0, column=0, **checkbutton_padding)
            else:
                self.checkbutton.grid(row=0, column=0)
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
        self.canvas = Canvas(self, highlightthickness=0, background='white', width=self.winfo_reqwidth(),
                             height=self.winfo_reqheight() - 25)
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
        self.empty_text_label.grid(row=0, column=0, sticky='we')

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
        tbl_entry.grid(row=len(self.entries), sticky='ensw')
        self.entries.append(tbl_entry)

    def del_entry(self, row: int) -> None:
        """Removes a gate entry from the table"""
        if abs(row) > len(self.entries):
            return
        entry = self.entries[row]
        entry.grid_forget()
        entry.destroy()
        self.entries.remove(entry)

        # Subtract one from each checkbutton label number
        for (i, entry) in enumerate(self.entries):
            if entry.has_default_name:  # If the gate's name hasn't been set yet, then update its number
                cutoff_index = entry.gate.get_label().find('#')
                stripped_label = entry.gate.get_label()[:cutoff_index+1]
                self.entries[i].update_text(stripped_label + str(i+1))

        if len(self.entries) == 0:
            self.empty_text_label.grid()
            self.null = True

    def get_row(self, row: int) -> Optional[int]:
        """Returns checkbox value at row"""
        if abs(row) > len(self.entries):
            return None
        return self.entries[row].get()

    def del_gate_entry(self, gate: InputTk) -> None:
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

    def set_font(self, new_font: font.Font):
        """Updates the font of the widget and the font of the entries"""
        self.config(font=new_font)
        self.this_font = new_font
        self.empty_text_label.config(font=new_font)
        for entry in self.entries:
            entry.set_font(reconfig_font(self.this_font, offset=-2))

        self.update_idletasks()

    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.config(width=self.winfo_reqwidth() - 20)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

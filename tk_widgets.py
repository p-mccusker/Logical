import tkinter.font as font
from logic_gate import *


class TableCheckbutton(Frame):
    def __init__(self, parent: Optional[Widget], gate, return_focus_to: Widget, this_font: font.Font, *args,
                 checkbutton_padding: Optional[dict] = None,
                 **kwargs):  # Maybe add padding option for label
        super().__init__(parent, *args, background="white", **kwargs)
        self.gate = gate
        self.return_focus_to = return_focus_to
        if gate is not None:
            self.check_var = IntVar(value=gate.output())
            self.checkbutton = Checkbutton(self, variable=self.check_var, text=self.gate.get_label(),
                                           onvalue=TRUE, offvalue=FALSE, width=10, command=self.click_cb,
                                           background='white', font=this_font)
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

    def set_font(self, font: font.Font) -> None:
        self.checkbutton.config(font=font)

    def set_focus_widget(self, widget: Widget):
        self.return_focus_to = widget


class CheckbuttonTable(LabelFrame):
    def __init__(self, parent, title: str, return_focus_to: Widget, this_font: font.Font, *args,  **kwargs):
        super().__init__(parent, *args, text=title, font=this_font, **kwargs)
        self.checkbox_padding = {"padx": (10, 5), "pady": (5, 5)}
        self.return_focus_to = return_focus_to
        self.entries = []  # List holding list of TableCheckbutton
        self.empty_text_label = Label(self, bg="white", text="No inputs...",
                                      font=this_font)
        self.font_sz = this_font.cget("size")
        self.font_family = this_font.cget("family")
        self.font_weight = this_font.cget("weight")
        self.font_slant = this_font.cget("slant")
        self.entry_font = font.Font(family=self.font_family, size=self.font_sz - 2, weight=self.font_weight,
                                    slant=self.font_slant)
        self.empty_text_label.grid()
        self.null = True

    def add_entry(self, gate) -> None:
        if self.null:
            self.empty_text_label.grid_forget()
            self.null = False
        tbl_entry = TableCheckbutton(self, gate, self.return_focus_to, checkbutton_padding=self.checkbox_padding,
                                     this_font=self.entry_font)
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

    def set_focus_widget(self, widget: Widget):
        self.return_focus_to = widget
        for entry in self.entries:
            entry.set_focus_widget(widget)

    def clear(self) -> None:
        for entry in self.entries:
            entry.grid_forget()
            entry.destroy()

        self.entries.clear()

        self.empty_text_label.grid()
        self.null = True

    def set_font(self, new_font: font.Font):
        self.font_sz = new_font.cget("size")
        self.font_family = new_font.cget("family")
        self.font_weight = new_font.cget("weight")
        self.font_slant = new_font.cget("slant")
        self.entry_font = font.Font(family=self.font_family, size=self.font_sz-2, weight=self.font_weight,
                                    slant=self.font_slant)
        self.config(font=new_font)
        self.empty_text_label.config(font=new_font)
        for entry in self.entries:
            entry.set_font(self.entry_font)


class LabeledEntry(Frame):
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

    def set_font(self, font: font.Font) -> None:
        self.entry.config(font=font)
        self.label.config(font=font)

    def get(self) -> str:
        return self.entry_var.get()


import tkinter as tk


class HectorButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        # Extract optional parameters for focus colors
        self.background = kwargs.get("background", None)
        self.foreground = kwargs.get("foreground", None)

        # Initialize the parent class
        super().__init__(master, **kwargs)

        # Bind focus and unfocus events
        self.bind("<FocusIn>", self.on_focus)
        self.bind("<FocusOut>", self.on_unfocus)

    def on_focus(self, event):
        # Change colors on focus
        self.configure(bg=self.foreground, fg=self.background)

        # Bind Enter key to trigger the button command
        self.bind("<Return>", self.execute_command)

    def on_unfocus(self, event):
        # Revert to normal colors on unfocus
        self.configure(bg=self.background, fg=self.foreground)

        # Unbind Enter key
        self.unbind("<Return>")

    def execute_command(self, event):
        # Trigger the button's command
        if self["command"]:
            self.invoke()

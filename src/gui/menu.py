import tkinter as tk
import tkinter.font as tkFont


class MenuItem:
    def __init__(self, label, command=None, submenu=None, icon=None, highlight_icon=None, shortcut=None,
                 shortcut_label=None,
                 underline_index=-1):
        """
        Create a menu item with optional parameters.

        :param label: Text displayed on the menu item.
        :param command: Function to execute when the item is clicked.
        :param submenu: List of additional submenu items (type MenuItem).
        :param icon: Icon image (if any)
        :param highlight_icon: Icon image (if any)
        :param shortcut: Keyboard shortcut for this item.
        :param shortcut_label: Keyboard shortcut label for this item.
        :param underline_index: Index of the character in the label to underline.
        """
        self.label = label
        self.command = command
        self.submenu = submenu if submenu else []
        self.icon = icon
        self.highlight_icon = highlight_icon
        self.shortcut = shortcut
        self.shortcut_label = shortcut_label
        self.underline_index = underline_index


class _SubmenuButton:
    def __init__ (self, item: MenuItem, outer_frame: tk.Frame, icon_label: tk.Label, text_label: tk.Label, shortcut_label: tk.Label):
        self.item = item
        self.outer_frame = outer_frame
        self.icon_label = icon_label
        self.text_label = text_label
        self.shortcut_label = shortcut_label


class SimpleMenu:
    def __init__(self, root, menu_items, background="lightgray", foreground="black", icon_size=(16, 16)):
        self.root = root
        self.menu_frame = tk.Frame(root, bg=background)
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)

        self.menu_buttons = []
        self.accelerators = {}
        self.shortcuts = {}
        self.active_submenu = None
        self.current_submenu_index = -1
        self.current_main_menu_index = -1
        self.background = background
        self.foreground = foreground
        self.icon_size = icon_size
        self.menu_items = menu_items

        for index, item in enumerate(menu_items):
            label = item.label
            underline_index = item.underline_index
            command = item.command
            submenu = item.submenu
            shortcut = item.shortcut

            # Create a button for the main menu item
            button = tk.Button(self.menu_frame,
                               text=label,
                               compound=tk.LEFT,
                               image=item.icon,
                               bg=background,
                               fg=foreground,
                               relief=tk.FLAT,
                               highlightthickness=0,
                               font=tkFont.Font(family="Courier New", size=9),
                               padx=2,
                               pady=2
                               )
            # Bind focus events
            button.bind("<Enter>",
                        lambda e, i=item, btn=button: btn.configure(foreground=background, background=foreground,
                                                                    image=i.highlight_icon))
            button.bind("<FocusIn>",
                        lambda e, i=item, btn=button: btn.configure(foreground=background, background=foreground,
                                                                    image=i.highlight_icon))
            button.bind("<Leave>",
                        lambda e, i=item, btn=button: btn.configure(foreground=foreground, background=background,
                                                                    image=i.icon))
            button.bind("<FocusOut>",
                        lambda e, i=item, btn=button: btn.configure(foreground=foreground, background=background,
                                                                    image=i.icon))

            button.config(command=lambda cmd=command, sub=submenu, idx=index, btn=button: self._handle_menu(cmd, sub, btn, idx))
            button.pack(side=tk.LEFT, padx=5)

            # Set underline and Alt + key shortcut
            if underline_index != -1:
                button.config(underline=underline_index)
                key = label[underline_index].lower()
                self.accelerators[key] = (submenu, command, index, button)

            if shortcut:
                self.shortcuts[shortcut] = lambda e, cmd=command: self._execute_command(cmd)
            if item.submenu is not None:
                for submenu_item in item.submenu:
                    if submenu_item.shortcut:
                        self.shortcuts[submenu_item.shortcut] = lambda e, cmd=submenu_item.command: self._execute_command(
                            cmd)

            self.menu_buttons.append(button)

    def bind_events(self):
        # Bind Alt + keys
        for i, key in enumerate(self.accelerators):
            self.root.bind(
                f"<Alt-{key}>",
                lambda e, sub=self.accelerators[key][0], cmd=self.accelerators[key][1],
                       idx=self.accelerators[key][2], btn=self.accelerators[key][3]: self._handle_menu(cmd, sub, btn, idx)
            )
        # Bind shortcuts
        for i, shortcut in enumerate(self.shortcuts):
            self.root.bind(shortcut, self.shortcuts[shortcut])
        # Bind click outside menu and ESC to close submenu
        self.root.bind("<Button-1>", self._close_all_menus)
        self.root.bind("<Escape>", self._close_all_menus)
        self.root.bind("<FocusOut>", self._on_focus_loss)
        # Bind keys for navigation
        self.root.bind("<Up>", self._navigate_submenu_up)
        self.root.bind("<Down>", self._navigate_submenu_down)
        self.root.bind("<Left>", self._navigate_main_menu_left)
        self.root.bind("<Right>", self._navigate_main_menu_right)
        self.root.bind("<Return>", self._execute_selected_command)

    def _on_focus_loss(self, event):
        if event.widget is self.root:
            # check which widget getting the focus
            w = self.root.tk.call('focus')
            if not w:
                self._close_all_menus()

    def _execute_command(self, command):
        if command:
            self._close_all_menus()
            command()

    def _handle_menu(self, command, submenu, button, index):
        self._execute_command(command)
        if submenu:
            self.current_main_menu_index = index
            print(index)
            self.menu_buttons[index].focus_set()
            self._show_submenu(submenu, button)

    def _show_submenu(self, submenu_items, button):
        self._close_submenu()

        submenu = tk.Toplevel(self.root)
        submenu.overrideredirect(True)
        submenu.transient(self.root)

        # Get the position of the button and set submenu under it
        button_x = button.winfo_rootx()
        button_y = button.winfo_rooty() + button.winfo_height()
        max_label_length = len(max(submenu_items, key=lambda i: len(i.label)).label)
        width = max_label_length * 11
        has_icon = False
        has_shortcut = False
        if any(map(lambda i: i.icon, submenu_items)):
            width += 20
            has_icon = True
        if any(map(lambda i: i.shortcut_label, submenu_items)):
            max_shortcut_label_length = len(max(submenu_items, key=lambda i: len(i.shortcut_label)).shortcut_label)
            width += max_shortcut_label_length * 10
            has_shortcut = True
        submenu.geometry(f"{width}x{len(submenu_items) * 24}+{button_x}+{button_y}")
        submenu.config(bg=self.background, bd=1, relief=tk.SOLID)  # Set background of submenu to match main menu

        self.submenu_buttons = []
        for item in submenu_items:
            item_frame = tk.Frame(submenu, bg=self.background)
            item_frame.pack(fill=tk.X)
            icon_label = None
            shortcut_label = None
            if has_icon:
                if item.icon:
                    icon_label = tk.Label(item_frame, image=item.icon, text="", compound=tk.LEFT, bg=self.background,
                                          width=18)
                else:
                    icon_label = tk.Label(item_frame, bg=self.background, width=2)
                icon_label.pack(side=tk.LEFT, padx=(2, 0))
            text_label = tk.Label(item_frame, text=item.label, bg=self.background, fg=self.foreground, anchor="w",
                                  padx=(10 if not has_icon else (5)), font=tkFont.Font(family="Courier New", size=9))
            text_label.pack(side=tk.LEFT, expand=True, fill=tk.X, pady=(4, 0))
            if has_shortcut:
                shortcut_label = tk.Label(item_frame, text=item.shortcut_label if item.shortcut_label else "",
                                          bg=self.background,
                                          fg=self.foreground, anchor="e", padx=10,
                                          font=tkFont.Font(family="Courier New", size=9))
                shortcut_label.pack(side=tk.RIGHT, pady=(4, 0))
            item_frame.bind("<Enter>", lambda e, frame=item_frame, i=item, il=icon_label, tl=text_label,
                                          sl=shortcut_label: self._on_submenu_focus(e, frame, i, il, tl, sl))
            item_frame.bind("<Leave>", lambda e, frame=item_frame, i=item, il=icon_label, tl=text_label,
                                              sl=shortcut_label: self._on_submenu_focus_loss(e, frame, i, il, tl, sl))
            self.submenu_buttons.append(_SubmenuButton(item, item_frame, icon_label, text_label, shortcut_label))

        self.active_submenu = submenu
        self.current_submenu_index = -1  # Reset submenu index

    def _on_submenu_focus(self, event, frame: tk.Frame, item: MenuItem, image_label: tk.Label, text_label: tk.Label, shortcut_label:tk.Label):
        frame.configure(background=self.foreground)
        text_label.configure(background=self.foreground, foreground=self.background)
        if image_label is not None:
            image_label.configure(background=self.foreground, foreground=self.background, image= item.highlight_icon if item.highlight_icon is not None else item.icon )
        if shortcut_label is not None:
            shortcut_label.configure(background=self.foreground, foreground=self.background)

    def _on_submenu_focus_loss(self, event, frame: tk.Frame, item: MenuItem, image_label: tk.Label, text_label: tk.Label, shortcut_label:tk.Label):
        frame.configure(background=self.background)
        text_label.configure(background=self.background, foreground=self.foreground)
        if image_label is not None:
            image_label.configure(background=self.background, foreground=self.foreground, image=item.icon)
        if shortcut_label is not None:
            shortcut_label.configure(background=self.background, foreground=self.foreground)

    def _close_submenu(self, event=None):
        if self.active_submenu:
            self.active_submenu.destroy()
            self.active_submenu = None
            self.current_submenu_index = -1

    def _close_all_menus(self, event=None):
        if self.current_main_menu_index > -1:
            self.root.focus_set()
            self._close_submenu()
            self.current_submenu_index = -1
            self.current_main_menu_index = -1

    def _navigate_submenu_up(self, event=None):
        if self.active_submenu and self.submenu_buttons:
            self._unhighlight_submenu_item()
            if self.current_submenu_index <= 0:
                self.current_submenu_index = -1
                self.menu_buttons[self.current_main_menu_index].focus_set()
            else:
                self.current_submenu_index = (self.current_submenu_index - 1) % len(self.submenu_buttons)
            self._highlight_submenu_item()

    def _navigate_submenu_down(self, event=None):
        if self.active_submenu and self.submenu_buttons:
            self._unhighlight_submenu_item()
            self.current_submenu_index = (self.current_submenu_index + 1) % len(self.submenu_buttons)
            self._highlight_submenu_item()

    def _unhighlight_submenu_item(self):
        if self.current_submenu_index > -1:
            dto = self.submenu_buttons[self.current_submenu_index]
            self._on_submenu_focus_loss(None, dto.outer_frame, dto.item, dto.icon_label, dto.text_label, dto.shortcut_label)

    def _highlight_submenu_item(self):
        if self.current_submenu_index > -1:
            dto = self.submenu_buttons[self.current_submenu_index]
            self._on_submenu_focus(None, dto.outer_frame, dto.item, dto.icon_label, dto.text_label, dto.shortcut_label)

    def _navigate_main_menu_left(self, event=None):
        if self.current_submenu_index > -1 or self.current_main_menu_index <= -1:
            return  # Prevent navigating if submenu is active
        self.current_main_menu_index = (self.current_main_menu_index - 1) % len(self.menu_buttons)
        self._focus_main_menu_item()

    def _navigate_main_menu_right(self, event=None):
        if self.current_submenu_index > -1 or self.current_main_menu_index <= -1:
            return  # Prevent navigating if submenu is active
        self.current_main_menu_index = (self.current_main_menu_index + 1) % len(self.menu_buttons)
        self._focus_main_menu_item()

    def _focus_main_menu_item(self):
        if 0 <= self.current_main_menu_index < len(self.menu_buttons):
            self.menu_buttons[self.current_main_menu_index].focus_set()
            submenu = self.accelerators.get(self.menu_buttons[self.current_main_menu_index].cget("text")[0].lower())
            if submenu:
                self._show_submenu(submenu[0], self.menu_buttons[self.current_main_menu_index])

    def _activate_main_menu(self, index):
        self.current_main_menu_index = index
        self._focus_main_menu_item()
        self.menu_buttons[index].invoke()

    def _execute_selected_command(self, event=None):
        if self.active_submenu and self.current_submenu_index != -1:
            selected_button = self.submenu_buttons[self.current_submenu_index]
            self._close_all_menus()
            selected_button.item.command()

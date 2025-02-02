import platform
import tkinter as tk
import tkinter.font as tkFont
from functools import partial
from tkinter import ttk

from src.const.colors import GREY
from src.const.fonts import HELVETICA_FONT_NAME, TEXT_SIZE_MENU
from src.gui.gui_utils import GuiUtils
from src.utils import Utils


# DEFINITION OF SINGLE MENU ITEM.
# EVERY ITEM CAN HAVE SUBITEMS BUT ONLY ONE SUBMENU LEVEL IS SUPPORTED FOR NOW
class MenuItem:
    def __init__(
            self,
            label,
            command=None,
            submenu=None,
            icon=None,
            highlight_icon=None,
            shortcut=None,
            shortcut_label=None,
            underline_index=-1
    ):
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


class MenuSeparator(MenuItem):
    """Special menu item representing horizontal or vertical separator"""

    def __init__(self):
        super().__init__("")


class _MenuButton:
    """Popo object that collects all information about menu button"""

    def __init__(
            self,
            item: MenuItem,
            outer_frame: tk.Frame,
            icon_label: tk.Label,
            text_label: tk.Label,
            shortcut_label: tk.Label,
            parent_submenu: tk.Toplevel,
            menu_level: int,
            index: int):
        self.item = item
        self.outer_frame = outer_frame
        self.icon_label = icon_label
        self.text_label = text_label
        self.shortcut_label = shortcut_label
        self.parent_submenu = parent_submenu
        self.menu_level = menu_level
        self.index = index


class TopMenu:
    """Tkinter like widget that implements top menu"""
    def __init__(self, root, menu_items, background, foreground, icon_size=(16, 16)):
        self.root = root
        self.menu_frame = tk.Frame(root, bg=background)
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)
        # HELPER VARIABLE HOLDING ACCELERATOR KEYS
        self.accelerators = {}
        # HELPER VARIABLE HOLDING SHORTCUTS
        self.shortcuts = {}
        self.keyboard_nav_handles = {}
        self.background = background
        self.foreground = foreground
        self.icon_size = icon_size
        self.menu_items = menu_items
        # INTERNAL COLLECTION OF ALL OPENED SUBMENUS
        self.opened_submenus = []
        # INTERNAL COLLECTION OF ALL MENU BUTTONS IN ROOT AND SUBMENUS
        # ROOT MENUS ARE ON INDEX 0
        self.buttons = [[]]
        # INTERNAL INDEX OF CURRENT ITEMS. ANY MENU (INCLUDING ROOT MENU) IS REPRESENTED BY OWN INDEX
        self.current_menu_item_index = [-1]
        # CURRENT FOCUSED MENU LEVEL
        self.current_menu_level = 0
        # GENERATE TOP MENU BASED ON SUPPLIED ITEMS
        i = -1
        for item in menu_items:
            # FRAME FOR MENU ITEM
            item_frame = tk.Frame(self.menu_frame, bg=self.background)
            item_frame.pack(side=tk.LEFT, padx=5)
            # SPECIAL HANDLING FOR SEPARATOR
            if isinstance(item, MenuSeparator):
                separator = tk.Label(item_frame, text="|", background=self.background, foreground=GREY)
                separator.pack(side=tk.LEFT, padx=0)
                continue
            i += 1
            # APPEND ICON, IF APPLICABLE
            icon_label = None
            if item.icon:
                icon_label = tk.Label(item_frame,
                                      image=item.icon,
                                      text="",
                                      compound=tk.LEFT,
                                      font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU),
                                      bg=self.background,
                                      width=18
                                      )
                icon_label.pack(side=tk.LEFT, padx=(2, 0))
            # APPEND LABEL
            text_label = tk.Label(item_frame,
                                  text=item.label,
                                  bg=self.background,
                                  fg=self.foreground,
                                  font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU),
                                  underline=item.underline_index,
                                  anchor="w",
                                  )
            text_label.pack(side=tk.LEFT, expand=True, fill=tk.X, pady=(4, 0))

            button = _MenuButton(item,
                                 item_frame,
                                 icon_label,
                                 text_label,
                                 None,
                                 None,
                                 0,
                                 i
                                 )
            # BIND FOCUS AND LEAVE EVENTS
            item_frame.bind(
                "<Enter>",
                partial(
                    self._on_menu_item_focus,
                    button
                )
            )
            item_frame.bind(
                "<Leave>",
                partial(self._on_menu_item_focus_loss, button)
            )
            # BIND BUTTON_1 EVENTS
            for bindable_element in [item_frame, icon_label, text_label]:
                if bindable_element is not None:
                    bindable_element.bind("<Button-1>", partial(self._on_menu_item_event, button))

            # PREPARE ACCELERATOR, IF APPLICABLE
            if item.underline_index != -1:
                key = item.label[item.underline_index].lower()
                self.accelerators[key] = button

            # PREPARE SHORTCUT, IF APPLICABLE
            self._prepare_shortcuts_from_item(item)

            if item.submenu is not None:
                for submenu_item in item.submenu:
                    if submenu_item.shortcut:
                        self.shortcuts[submenu_item.shortcut] = partial(self._execute_command, submenu_item.command)

            self.buttons[0].append(button)

    def destroy(self):
        """Close menu frame"""
        self.menu_frame.destroy()

    def _open_submenu(self, submenu_items, button: _MenuButton, event=None):
        """Show submenu"""
        # CLOSE ANY CONFLICTING SUBMENU
        self._close_submenu(button.parent_submenu)
        # INCREASE MENU LEVEL AND PREPARE NEW VARIABLES
        self.current_menu_level += 1
        self.current_menu_item_index.append(-1)
        self.current_menu_item_index[button.menu_level] = button.index
        self.buttons.append([])
        # CREATE SUBMENU TOP LEVEL
        submenu = tk.Toplevel(self.root)
        submenu.wm_overrideredirect(True)
        # GET THE POSITION FOR SUBMENU
        if button.parent_submenu:
            button_x = button.parent_submenu.winfo_rootx() + button.parent_submenu.winfo_width() - 1
            button_y = button.outer_frame.winfo_rooty()
        else:
            button_x = button.outer_frame.winfo_rootx()
            button_y = button.outer_frame.winfo_rooty() + button.outer_frame.winfo_height()
        # COMPUTE SUBMENU DIMENSIONS
        max_label_length = len(max(submenu_items, key=lambda i: len(i.label)).label)
        width = max_label_length * 9
        has_icon = False
        has_right_suffix = False
        # CHECK IF ANY SUBMENU ITEM HAS ICON
        if any(map(lambda i: i.icon, submenu_items)):
            width += 20
            has_icon = True
        # CHECK IF ANY SUBMENU ITEM HAS SHORTCUT LABEL
        if any(map(lambda i: i.shortcut_label, submenu_items)):
            max_shortcut_label_length = len(max(submenu_items, key=lambda i: len(
                i.shortcut_label) if i.shortcut_label is not None else 0).shortcut_label)
            width += max_shortcut_label_length * 9
            has_right_suffix = True
        else:
            width += 16
        # CHECK IF ANY SUBMENU ITEM HAS OWN SUBMENU
        if any(map(lambda i: i.submenu, submenu_items)):
            has_right_suffix = True
        height = len(submenu_items) * 26
        # APPLY WINDOWS SCALING FACTOR
        if platform.system() == "Windows":
            scaling_factor = Utils.get_windows_scaling_factor()
            width = int(round(width * scaling_factor, 0))
            height = int(round(height * scaling_factor, 0))
        # SET DIMENSTION AND BACKGROUND
        submenu.wm_geometry(f"{width}x{height}+{button_x}+{button_y}")
        submenu.config(bg=self.background, bd=1, relief=tk.SOLID)
        i = -1
        for index, item in enumerate(submenu_items):
            # BUILD GUI ELEMENTS
            item_frame = tk.Frame(submenu, bg=self.background)
            item_frame.pack(fill=tk.X)
            if isinstance(item, MenuSeparator):
                separator = ttk.Separator(item_frame, orient='horizontal', style='Grey.TSeparator')
                separator.pack(fill=tk.X, padx=10, pady=10)
                continue
            i += 1
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
            if has_right_suffix:
                right_suffix = item.shortcut_label
                # MENU ITEM WITH SUBMENU SHOULD NOT HAVE SHORTCUT
                # WE WILL USE SPACE FOR ARROW CHAR INSTEAD
                if len(item.submenu) > 0:
                    right_suffix = ">"
                shortcut_label = tk.Label(item_frame, text=right_suffix if right_suffix else "",
                                          bg=self.background,
                                          fg=self.foreground, anchor="e", padx=10,
                                          font=tkFont.Font(family="Courier New", size=9))
                shortcut_label.pack(side=tk.RIGHT, pady=(4, 0))
            b = _MenuButton(
                item,
                item_frame,
                icon_label,
                text_label,
                shortcut_label,
                submenu,
                self.current_menu_level,
                i
            )
            # BIND FOCUS AND LEAVE EVENTS
            item_frame.bind(
                "<Enter>",
                partial(
                    self._on_menu_item_focus,
                    b
                )
            )
            item_frame.bind(
                "<Leave>",
                partial(self._on_menu_item_focus_loss, b)
            )
            # BIND BUTTON_1 EVENTS
            for bindable_element in [item_frame, icon_label, text_label, shortcut_label]:
                if bindable_element is not None:
                    bindable_element.bind("<Button-1>", partial(self._on_menu_item_event, b))
            self.buttons[self.current_menu_level].append(b)
        # APPEND SUBMENU TO COLLECTION
        self.opened_submenus.append(submenu)

    def _close_submenu(self, parent_submenu=None):
        """Close submenu"""
        if len(self.opened_submenus) > 0 and self.opened_submenus[-1] != parent_submenu:
            self.opened_submenus.pop().destroy()
            self.buttons.pop()
            self.current_menu_level -= 1
            self.current_menu_item_index.pop()

    def _close_all_submenus(self, event=None):
        """Close all submenus"""
        if self.current_menu_level > 0 and (event is None or not GuiUtils.is_child_of(self.menu_frame, event.widget)):
            self._unhighlight_menu_item(self.buttons[0][self.current_menu_item_index[0]])
            self.root.focus_set()
            while len(self.opened_submenus) > 0:
                self._close_submenu()
            self.current_menu_item_index = [-1]
            self.current_menu_level = 0
            self._unbind_keyboard_navigation()

    def _highlight_menu_item(self, button):
        """Change menu item appearance to focused state"""
        button.outer_frame.configure(background=self.foreground)
        button.text_label.configure(background=self.foreground, foreground=self.background)
        if button.icon_label is not None:
            button.icon_label.configure(background=self.foreground, foreground=self.background,
                                        image=button.item.highlight_icon if button.item.highlight_icon is not None else button.item.icon)
        if button.shortcut_label is not None:
            button.shortcut_label.configure(background=self.foreground, foreground=self.background)

    def _unhighlight_menu_item(self, button):
        """Change appearance of menu item to indicate normal state"""
        button.outer_frame.configure(background=self.background)
        button.text_label.configure(background=self.background, foreground=self.foreground)
        if button.icon_label is not None:
            button.icon_label.configure(background=self.background, foreground=self.foreground, image=button.item.icon)
        if button.shortcut_label is not None:
            button.shortcut_label.configure(background=self.background, foreground=self.foreground)

    def _prepare_shortcuts_from_item(self, item):
        if item.shortcut:
            self.shortcuts[item.shortcut] = partial(self._execute_command, item.command)
        # PREPARE SHORTCUTS ON SUBMENU ITEMS, IF APPLICABLE
        if item.submenu is not None:
            for submenu_item in item.submenu:
                self._prepare_shortcuts_from_item(submenu_item)

    def _bind_events(self):
        """Bind events: Accelerators, shortcuts, keyboard navigation"""
        # Bind Alt + keys
        for i, key in enumerate(self.accelerators):
            self.root.bind(
                f"<Alt-{key}>",
                partial(
                    self._on_menu_item_event,
                    self.accelerators[key]
                )
            )
        # BIND SHORTCUTS
        for i, shortcut in enumerate(self.shortcuts):
            self.root.bind(shortcut, self.shortcuts[shortcut])
        # BIND CLICK OUTSIDE MENU AND ESC TO CLOSE SUBMENU
        self.root.bind("<Button-1>", self._close_all_submenus)
        self.root.bind("<Escape>", self._close_all_submenus)
        self.root.bind("<FocusOut>", self._on_app_focus_loss)

    def _bind_keyboard_navigation(self):
        """Bind keyboard navigation events"""
        # BIND KEYS FOR NAVIGATION
        if len(self.keyboard_nav_handles) == 0:
            self.keyboard_nav_handles["<Up>"] = self.root.bind("<Up>", self._keyboard_nav_submenu_up, '+')
            self.keyboard_nav_handles["<Down>"] = self.root.bind("<Down>", self._keyboard_nav_submenu_down, '+')
            self.keyboard_nav_handles["<Left>"] = self.root.bind("<Left>", self._keyboard_nav_main_menu_left, '+')
            self.keyboard_nav_handles["<Right>"] = self.root.bind("<Right>", self._keyboard_nav_main_menu_right, '+')
            self.keyboard_nav_handles["<Return>"] = self.root.bind("<Return>", self._keyboard_nav_execute_command, '+')

    def _unbind_keyboard_navigation(self):
        """Unbind keyboard navigation events"""
        for key in self.keyboard_nav_handles:
            self.root.unbind(key, self.keyboard_nav_handles[key])
        self.keyboard_nav_handles.clear()

    def _on_app_focus_loss(self, event):
        """Callback: Application lost focus"""
        if event.widget is self.root:
            # check which widget getting the focus
            w = self.root.tk.call('focus')
            if not w:
                self.root.after(0, self._close_all_submenus)

    def _execute_command(self, command, event=None):
        """Execute command"""
        if command:
            self._close_all_submenus()
            self.root.after(0, command)

    def _on_menu_item_event(self, button, e):
        """Callback: Menu item event"""
        self._bind_keyboard_navigation()
        if button.item.command:
            self._execute_command(button.item.command, e)
        if button.item.submenu is not None and len(button.item.submenu) > 0:
            self._on_menu_item_focus(button, e)
            self._open_submenu(button.item.submenu, button, e)

    def _on_menu_item_focus(self, button: _MenuButton, event=None):
        """Callback: Menu item focus"""
        # REMOVE HIGHLIGHT FROm CURRENT EVENT
        self._unhighlight_menu_item(self.buttons[button.menu_level][self.current_menu_item_index[button.menu_level]])
        self._highlight_menu_item(button)
        # IF ANOTHER SUBMENU IS OPENED, CLOSE IT AND OPEN SUBMENU OF THIS ITEM
        if button.item.submenu and self.current_menu_level > 0 and len(button.item.submenu) > 0:
            while self.current_menu_level > button.menu_level:
                self._close_submenu()
            self._open_submenu(button.item.submenu, button)
        else:
            self.current_menu_item_index[button.menu_level] = button.index
            self._close_submenu(button.parent_submenu)

    def _on_menu_item_focus_loss(self, button: _MenuButton, event=None):
        """Callback: menu item lost focus"""
        if self.current_menu_level == 0:
            self._unhighlight_menu_item(button)

    # KEYBOARD NAVIGATION:
    def _keyboard_nav_execute_command(self, event=None):
        """Custom handling for command execution from keyboard navigation"""
        if len(self.opened_submenus) > 0 and self.current_menu_item_index[self.current_menu_level] != -1:
            # FIND FOCUSED BUTTON AND EXECUTE ITS COMMAND
            selected_button = self.buttons[self.current_menu_level][
                self.current_menu_item_index[self.current_menu_level]]
            self._execute_command(selected_button.item.command)

    def _keyboard_nav_submenu_up(self, event=None):
        """Callback: keyboard up"""
        if self.current_menu_item_index[0] == -1:
            return
        if self.current_menu_level == 1 and self.current_menu_item_index[self.current_menu_level] == 0:
            # IF FIRST ITEM OF FIRST SUBMENU IS FOCUSED MOVE TO TOPLEVEL MENU
            self._on_menu_item_focus(self.buttons[0][self.current_menu_item_index[0]])
        else:
            # MOVE FOCUS TO PREVIOUS ITEM
            prev_index = (self.current_menu_item_index[self.current_menu_level] - 1) % len(
                self.buttons[self.current_menu_level])
            button = self.buttons[self.current_menu_level][prev_index]
            self._on_menu_item_focus(button, event)
            self.current_menu_level = button.menu_level

    def _keyboard_nav_submenu_down(self, event=None):
        """Callback: keyboard down"""
        if self.current_menu_item_index[0] == -1:
            return
        if self.current_menu_level == 1 and self.current_menu_item_index[self.current_menu_level] == -1:
            # IF TOPLEVEL MENU IS FOCUSED, MOVE TO SUBMENU
            self._on_menu_item_focus(self.buttons[self.current_menu_level][0])
        else:
            # MOVE FOCUS TO NEXT ITEM
            next_index = (self.current_menu_item_index[self.current_menu_level] + 1) % len(
                self.buttons[self.current_menu_level])
            button = self.buttons[self.current_menu_level][next_index]
            self._on_menu_item_focus(button, event)
            self.current_menu_level = button.menu_level

    # HANDLE ARROW LEFT
    def _keyboard_nav_main_menu_left(self, event=None):
        """Callback: keyboard left"""
        if self.current_menu_item_index[0] == -1:
            return
        if self.current_menu_level == 1 and self.current_menu_item_index[self.current_menu_level] == -1:
            # IF TOPLEVEL MENU IS FOCUSED, MOVE FOCUS TO LEFTER ITEM
            cur_index = self.current_menu_item_index[0]
            next_index = (cur_index - 1) % len(self.buttons[0])
            self._on_menu_item_focus(self.buttons[0][next_index])
        else:
            # CLOSE LAST SUBMENU
            if self.current_menu_level > 1:
                self._close_submenu()

    # HANDLE ARROW RIGHT
    def _keyboard_nav_main_menu_right(self, event=None):
        """Callback: keyboard right"""
        if self.current_menu_item_index[0] == -1:
            return
        if self.current_menu_level == 1 and self.current_menu_item_index[self.current_menu_level] == -1:
            # IF TOPLEVEL MENU IS FOCUSED, MOVE FOCUS TO RIGHTER ITEM
            cur_index = self.current_menu_item_index[0]
            next_index = (cur_index + 1) % len(self.buttons[0])
            self._on_menu_item_focus(self.buttons[0][next_index])
        else:
            button = self.buttons[self.current_menu_level][self.current_menu_item_index[self.current_menu_level]]
            # IF CURRENT ITEM HAS SUBMENU
            if button.item.submenu:
                # IF SUBMENU IS NOT OPENED, OPEN IT
                if self.current_menu_level == len(self.buttons) - 1:
                    self._open_submenu(button.item.submenu, button, event)
                    self.current_menu_level = button.menu_level
                # MOVE FOCUS TO NEXT LEVEL SUBMENU
                next_button = self.buttons[button.menu_level + 1][0]
                self.current_menu_level += 1
                self._on_menu_item_focus(next_button, event)

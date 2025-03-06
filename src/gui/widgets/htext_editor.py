import random
import re
import tkinter as tk
from functools import partial
from tkinter import ttk

from spacy.tokens import Doc
from tkinter_autoscrollbar import AutoScrollbar

from src.backend.run_context import RunContext
from src.backend.service.config_service import ConfigService
from src.backend.service.import_service import ImportService
from src.backend.service.nlp_service import NlpService
from src.backend.service.spellcheck_service import SpellcheckService
from src.const.colors import TEXT_EDITOR_BG, ACCENT_2_COLOR, LIGHT_WHITE, EDITOR_TEXT_COLOR, PRIMARY_COLOR, \
    PANEL_TEXT_COLOR, LONG_SENTENCE_HIGHLIGHT_COLOR_MID, LONG_SENTENCE_HIGHLIGHT_COLOR_HIGH, \
    SEARCH_RESULT_HIGHLIGHT_COLOR, CURRENT_SEARCH_RESULT_HIGHLIGHT_COLOR, CLOSE_WORDS_PALLETE
from src.const.font_awesome_icons import FontAwesomeIcons
from src.const.fonts import HELVETICA_FONT_NAME, TEXT_SIZE_MENU, FA_SOLID, BOLD_FONT, ITALIC_FONT
from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, GRAMMAR_ERROR_NON_LITERAL_WORD, \
    GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO, GRAMMAR_ERROR_S_INSTEAD_OF_Z, GRAMMAR_ERROR_Z_INSTEAD_OF_S, \
    GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING, \
    NON_LITERAL_WORDS
from src.const.tags import ITALIC_TAG_NAME, BOLD_TAG_NAME, CLOSE_WORD_PREFIX, SEARCH_RESULT_TAG_NAME, \
    CURRENT_SEARCH_RESULT_TAG_NAME, PARAGRAPH_TAG_NAME, FORMATTING_TAGS, LONG_SENTENCE_TAG_NAME_MID, \
    LONG_SENTENCE_TAG_NAME_HIGH, TRAILING_SPACES_TAG_NAME, COMPUTER_QUOTE_MARKS_TAG_NAME, DANGLING_QUOTE_MARK_TAG_NAME, \
    SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME, SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME, MULTIPLE_PUNCTUATION_TAG_NAME, \
    MULTIPLE_SPACES_TAG_NAME, GRAMMAR_ERROR_TAG_NAME, CLOSE_WORD_TAG_NAME, CLOSE_WORD_RANGE_PREFIX, BOLD_ITALIC_TAG_NAME
from src.const.values import A4_SIZE_INCHES, NLP_BATCH_SIZE, READABILITY_MAX_VALUE
from src.domain.config import Config
from src.domain.htext_file import HTextFormattingTag
from src.gui.gui_utils import GuiUtils
from src.gui.widgets.hector_button import HectorButton
from src.gui.widgets.tooltip import Tooltip
from src.utils import Utils

NLP_DEBOUNCE_LENGTH = 500


class HTextEditor:
    """Rich text editor for manipulation of htext files"""
    def __init__(
            self,
            root: tk.Widget,
            text_editor_frame: tk.Frame,
            tooltip: Tooltip,
            doc: Doc,
            word_freq_text: tk.Text,
            close_words_text: tk.Text,
            on_word_selected,
            on_text_paste,
            on_text_analyzed,
            on_formatting_changed,
    ):
        """
        Constructor for rich tect editor
        :param root tkinter root widget reprersenting window
        :param text_editor_frame Outer container for editor
        :param tooltip Tooltip implementation for showing tooltips on mouse over
        :param word_freq_text Temporary workaround for handling on mouse overs on frequend words. Tkinter text widget
        :param close_words_text Temporary workaround for handling on mouse overs on close words. Tkinter text widget
        :param on_word_selected Callback - User clicked on word
        :param on_text_paste Callback - text has been pasted
        :param on_text_analyzed Callback - text has been analyzed
        :param on_formatting_changed Callback - formatting has been changed
        """
        # NLP DOCUMENT
        self.doc = doc
        # WIDGETS
        self.root = root
        self.text_editor_frame = text_editor_frame
        self.word_freq_text = word_freq_text
        self.close_words_text = close_words_text
        # CALLBACKS
        self.on_word_selected = on_word_selected
        self.on_text_paste = on_text_paste
        self.on_text_analyzed = on_text_analyzed
        self.on_formatting_changed = on_formatting_changed
        self.tooltip = tooltip
        # DICTIONARY THAT HOLDS COLOR OF WORD TO PREVENT RECOLORING WHILE TYPING
        self.close_word_colors = {}
        # TIMERS FOR DEBOUNCING CHANGE EVENTS
        self.analyze_text_debounce_timer = None
        # EDITOR TEXT SIZE
        self.text_size = 10
        # SEARCH DATA
        self.search_matches = []
        self.last_search = ''
        self.last_match_index = 0
        self.last_tags = set()
        # CLOSE WORDS METADATA
        self.close_words = {}
        self.highlighted_word = None
        # GUI INITIALIZATION
        dpi = self.root.winfo_fpixels('1i')
        text_editor_scroll_frame = tk.Frame(text_editor_frame, width=10, relief=tk.FLAT, background=PRIMARY_COLOR)
        text_editor_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        text_editor_scroll = AutoScrollbar(text_editor_scroll_frame, orient='vertical',
                                           style='arrowless.Vertical.TScrollbar', takefocus=False)
        text_editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text_editor_outer_frame = tk.Frame(text_editor_frame, borderwidth=0, width=int(A4_SIZE_INCHES * dpi),
                                           relief=tk.RAISED, background=TEXT_EDITOR_BG)
        text_editor_outer_frame.pack(expand=True, fill=tk.Y, padx=5, pady=10, )
        # EDITOR TOOLBAR
        self.editor_toolbar_frame = tk.Frame(text_editor_outer_frame, background=ACCENT_2_COLOR, borderwidth=1)
        self.editor_toolbar_frame.pack(fill=tk.X, pady=5)
        ttk.Separator(text_editor_outer_frame, orient='horizontal').pack(fill=tk.X)
        self.toolbar_file_name = tk.Label(self.editor_toolbar_frame, text="(neuložený súbor)",
                                          background=ACCENT_2_COLOR, foreground=LIGHT_WHITE, padx=10,
                                          font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.toolbar_file_name.pack(side=tk.LEFT)
        self.bold_toolbar_icon = GuiUtils.fa_image(
            FA_SOLID,
            ACCENT_2_COLOR,
            foreground=LIGHT_WHITE,
            char=FontAwesomeIcons.bold,
            size=16
        )
        self.italic_toolbar_icon = GuiUtils.fa_image(
            FA_SOLID,
            ACCENT_2_COLOR,
            foreground=LIGHT_WHITE,
            char=FontAwesomeIcons.italic,
            size=16
        )
        HectorButton(
            self.editor_toolbar_frame,
            image=self.italic_toolbar_icon,
            background=ACCENT_2_COLOR,
            foreground=LIGHT_WHITE,
            highlightthickness=0,
            command=partial(self.toggle_format, ITALIC_TAG_NAME),
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
        HectorButton(
            self.editor_toolbar_frame,
            image=self.bold_toolbar_icon,
            background=ACCENT_2_COLOR,
            foreground=LIGHT_WHITE,
            highlightthickness=0,
            command=partial(self.toggle_format, BOLD_TAG_NAME),
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
        self.text_editor = tk.Text(text_editor_outer_frame, wrap=tk.WORD, relief=tk.RAISED, highlightthickness=0,
                                   yscrollcommand=text_editor_scroll.set, background=TEXT_EDITOR_BG,
                                   foreground=EDITOR_TEXT_COLOR, borderwidth=0,
                                   spacing1=1.2, spacing2=1.2, spacing3=1.2, undo=True, autoseparators=True, maxundo=-1,
                                   insertbackground=PANEL_TEXT_COLOR)
        self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size), )
        self.text_editor.pack(expand=1, fill=tk.BOTH, padx=20, pady=20)
        text_editor_outer_frame.pack_propagate(False)
        text_editor_scroll.config(command=self.text_editor.yview)

    def bind_events(self):
        """Apply mouse and keyboard bindings"""
        self.text_editor.unbind('<Control-z>')
        self.text_editor.unbind('<Control-Z>')
        self.text_editor.unbind('<Control-y>')
        self.text_editor.unbind('<Control-Y>')
        self.text_editor.unbind('<Control-Shift-z>')
        self.text_editor.unbind('<Control-Shift-Z>')
        self.text_editor.bind("<Return>", self._on_enter)
        self.text_editor.bind("<KeyRelease>", self._on_typing_done)
        self.text_editor.bind("<Button-1>", lambda e: self.root.after(0, self.on_word_selected))
        self.text_editor.bind("<Control-a>", self.select_all)
        self.text_editor.bind("<Control-A>", self.select_all)
        self.text_editor.bind("<<Paste>>", self.handle_clipboard_paste)
        self.text_editor.bind('<Motion>', self._editor_on_mouse_motion)
        self.text_editor.bind('<Leave>', self._editor_on_mouse_leave)

    def _on_enter(self, event):
        """
        Handle Enter key to:
          - End the current paragraph and any active formatting.
          - Insert a newline.
          - Start a new paragraph and reapply formatting if it was active.
        """
        # Determine which formatting tags (bold, italic, bold_italic) are active at the insertion point.
        current_tags = self.text_editor.tag_names("insert")
        active_formatting = []
        for tag in (BOLD_TAG_NAME, ITALIC_TAG_NAME, BOLD_ITALIC_TAG_NAME):
            if tag in current_tags:
                active_formatting.append(tag)

        # Insert a newline to end the current paragraph.
        self.text_editor.insert("insert", "\n")

        # Get the boundaries of the new line.
        new_line_start = self.text_editor.index("insert linestart")
        new_line_end = self.text_editor.index("insert lineend")

        # Apply the paragraph tag to the new line.
        self.tag_add(PARAGRAPH_TAG_NAME, new_line_start, new_line_end)

        # Remove any formatting tags that might have been carried over into the new line.
        for tag in (BOLD_TAG_NAME, ITALIC_TAG_NAME, BOLD_ITALIC_TAG_NAME):
            self.text_editor.tag_remove(tag, new_line_start, new_line_end)

        # Reapply any formatting that was active when Enter was pressed
        # so that the new paragraph begins with the desired formatting.
        for tag in active_formatting:
            self.tag_add(tag, new_line_start, new_line_end)

        # Return "break" to stop the default newline behavior.
        return "break"

    def get_carret_position(self, index_name):
        """Get carret possition for given index"""
        possible_carret = self.text_editor.count("1.0", self.text_editor.index(index_name), "chars")
        if possible_carret is None:
            return None
        return possible_carret[0]

    def apply_suggestion(self, span, suggestion, event, carret_index):
        """Apply suggestion at position"""
        self.move_carret(carret_index)
        self.create_selection(span.start_char, span.end_char)
        self._paste_text(suggestion, event, False)

    def create_selection(self, from_char, to_char):
        """Create new selection"""
        self.tag_add(tk.SEL, f"1.0 + {from_char} chars", f"1.0 + {to_char} chars")

    def toggle_format(self, new_tag_name):
        """Toggle given formatting tag"""
        if self.text_editor.tag_ranges(tk.SEL):
            selection_range = self.text_editor.tag_ranges(tk.SEL)
            tags_at_selection = self.tag_names(selection_range[0])
            removed = False
            for tag in tags_at_selection:
                if tag in [BOLD_TAG_NAME, ITALIC_TAG_NAME, BOLD_ITALIC_TAG_NAME]:
                    if tag == BOLD_ITALIC_TAG_NAME:
                        self.tag_remove(tag, selection_range[0], selection_range[1])
                        self.tag_add(BOLD_TAG_NAME if new_tag_name == ITALIC_TAG_NAME else ITALIC_TAG_NAME,
                                     selection_range[0], selection_range[1])
                        removed = True
                    elif tag == new_tag_name:
                        self.tag_remove(tag, selection_range[0], selection_range[1])
                        removed = True
                    elif tag != new_tag_name:
                        self.tag_remove(tag, selection_range[0], selection_range[1])
                        self.tag_add(BOLD_ITALIC_TAG_NAME, selection_range[0], selection_range[1])
                        removed = True
            if not removed:
                self.tag_add(new_tag_name, selection_range[0], selection_range[1])
            self.on_formatting_changed()

    def set_text_size(self, text_size):
        """Set text size and apply to all tags"""
        self.text_size = min(30, max(1, int(text_size)))
        # CHANGE FONT SIZE IN EDITOR
        self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size))
        # CLOSE WORDS ARE ALWAYS HIGHLIGHTED WITH BIGGER FONT. WE NEED TO UPDATE TAGS
        for tag in self.text_editor.tag_names():
            if tag == BOLD_TAG_NAME:
                self.text_editor.tag_configure(tagName=tag,
                                               font=(HELVETICA_FONT_NAME, self.text_size, BOLD_FONT))
            elif tag == ITALIC_TAG_NAME:
                self.text_editor.tag_configure(tagName=tag,
                                               font=(HELVETICA_FONT_NAME, self.text_size, ITALIC_FONT))
            elif tag == BOLD_ITALIC_TAG_NAME:
                self.text_editor.tag_configure(tagName=tag,
                                               font=(HELVETICA_FONT_NAME, self.text_size, f"{BOLD_FONT} {ITALIC_FONT}"))

    def tag_config(self, tag_name, cnf=None, **kw):
        """Configure tag"""
        self.text_editor.tag_config(tag_name, cnf=cnf, **kw)

    def tag_add(self, tag_name, start_index, end_index):
        """Add tag"""
        self.text_editor.tag_add(tag_name, start_index, end_index)

    def tag_bind(self, tag_name, event_name, func):
        """Bind tag to event"""
        self.text_editor.tag_bind(tag_name, event_name, func)

    def tag_remove(self, tag_name, start_index, end_index):
        """Remove tag"""
        self.text_editor.tag_remove(tag_name, start_index, end_index)

    def tag_names(self, index):
        """Get all tag names"""
        return self.text_editor.tag_names(index)

    def clear_tags(self):
        """Clear tags"""
        for tag in self.text_editor.tag_names():
            if tag != PARAGRAPH_TAG_NAME and tag not in FORMATTING_TAGS:
                self.text_editor.tag_delete(tag)

    def setup_tags(self, config):
        """Setup tag colors and priorities"""
        self.tag_config(PARAGRAPH_TAG_NAME,
                        lmargin1=f'{config.appearance_settings.paragraph_lmargin1}m',
                        spacing3=f'{config.appearance_settings.paragraph_spacing3}m')
        self.tag_config(LONG_SENTENCE_TAG_NAME_MID, background=LONG_SENTENCE_HIGHLIGHT_COLOR_MID)
        self.tag_config(LONG_SENTENCE_TAG_NAME_HIGH, background=LONG_SENTENCE_HIGHLIGHT_COLOR_HIGH)
        self.tag_config(TRAILING_SPACES_TAG_NAME, background="red")
        self.tag_config(COMPUTER_QUOTE_MARKS_TAG_NAME, background="red")
        self.tag_config(DANGLING_QUOTE_MARK_TAG_NAME, background="red")
        self.tag_config(SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME, background="red")
        self.tag_config(SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME, background="red")
        self.tag_config(MULTIPLE_PUNCTUATION_TAG_NAME, background="red")
        self.tag_config(MULTIPLE_SPACES_TAG_NAME, background="red")
        self.tag_config(SEARCH_RESULT_TAG_NAME, background=SEARCH_RESULT_HIGHLIGHT_COLOR)
        self.tag_config(CURRENT_SEARCH_RESULT_TAG_NAME, background=CURRENT_SEARCH_RESULT_HIGHLIGHT_COLOR)
        self.tag_config(GRAMMAR_ERROR_TAG_NAME, underline=True, underlinefg="red")
        self.tag_config(BOLD_TAG_NAME, font=(HELVETICA_FONT_NAME, self.text_size, BOLD_FONT))
        self.tag_config(ITALIC_TAG_NAME, font=(HELVETICA_FONT_NAME, self.text_size, ITALIC_FONT))
        self.tag_config(BOLD_ITALIC_TAG_NAME, font=(HELVETICA_FONT_NAME, self.text_size, f"{BOLD_FONT} {ITALIC_FONT}"))
        self.text_editor.tag_raise(COMPUTER_QUOTE_MARKS_TAG_NAME)
        self.text_editor.tag_raise("sel")

    def get_formatting(self) -> list[HTextFormattingTag]:
        """Get formatting applied to text"""
        output = []
        for tag in self.text_editor.tag_names():
            if tag in [BOLD_TAG_NAME, ITALIC_TAG_NAME, BOLD_ITALIC_TAG_NAME]:
                indices = self.text_editor.tag_ranges(tag)
                for i in range(0, len(indices), 2):
                    output.append(HTextFormattingTag(tag, str(indices[i]), str(indices[i + 1])))
        return output

    def set_formatting(self, formatting: list[HTextFormattingTag]):
        """Apply new formatting to text"""
        if formatting:
            for formatting_tag in formatting:
                self.text_editor.tag_add(
                    formatting_tag.tag_name,
                    formatting_tag.start_index,
                    formatting_tag.end_index,
                )

    def index(self, index_name):
        """Get editor index"""
        return self.text_editor.index(index_name)

    def move_carret(self, index, event=None):
        """Move carret to a new index"""
        self.text_editor.see(index)
        self.text_editor.mark_set(tk.INSERT, index)

    def get_text(self, start_index, end_index):
        """Get text from editor"""
        return self.text_editor.get(start_index, end_index)

    def get_text_as_html(self):
        """
        Exports the contents of the Tkinter Text widget to an HTML string.
        Paragraphs are determined by newline characters.
        If inline formatting (bold, italic, bold_italic) is active at a paragraph break,
        it will be closed for the current paragraph and immediately re-applied in the new one.
        """
        dump = self.text_editor.dump("1.0", tk.END, tag=True, text=True)
        html = ""
        # List to track active inline formatting.
        # Each entry is a tuple: (tag, closing_markup)
        active_inline = []
        # Mapping to determine opening tag from the formatting tag.
        opening_mapping = {
            BOLD_TAG_NAME: "<strong>",
            ITALIC_TAG_NAME: "<em>",
            BOLD_ITALIC_TAG_NAME: "<strong><em>"
        }
        # Mapping for closing tags is already stored with each active formatting.

        # Start the first paragraph.
        html += "<p>"

        for item in dump:
            event_type = item[0]
            if event_type == "text":
                text = item[1]
                # Split text on newline characters.
                parts = text.split("\n")
                for i, part in enumerate(parts):
                    html += part
                    # If this part is not the last one, we encountered a newline.
                    if i < len(parts) - 1:
                        if active_inline:
                            # Save a copy of active inline formatting.
                            active = active_inline[:]
                            # Close inline formatting in reverse order.
                            for tag, closing in reversed(active):
                                html += closing
                        # End the current paragraph.
                        html += "</p>\n"
                        # Start a new paragraph.
                        html += "<p>"
                        if active_inline:
                            # Reapply the inline formatting in the same order as originally applied.
                            for tag, _ in active_inline:
                                html += opening_mapping.get(tag, "")
            elif event_type == "tagon":
                tag = item[1]
                if tag == BOLD_TAG_NAME:
                    html += "<strong>"
                    active_inline.append((BOLD_TAG_NAME, "</strong>"))
                elif tag == ITALIC_TAG_NAME:
                    html += "<em>"
                    active_inline.append((ITALIC_TAG_NAME, "</em>"))
                elif tag == BOLD_ITALIC_TAG_NAME:
                    html += "<strong><em>"
                    active_inline.append((BOLD_ITALIC_TAG_NAME, "</em></strong>"))
                # We ignore any paragraph tag events since we are using newlines.
            elif event_type == "tagoff":
                tag = item[1]
                if tag in (BOLD_TAG_NAME, ITALIC_TAG_NAME, BOLD_ITALIC_TAG_NAME):
                    # Find the most recent matching tag and remove it.
                    for i in range(len(active_inline) - 1, -1, -1):
                        if active_inline[i][0] == tag:
                            html += active_inline[i][1]
                            active_inline.pop(i)
                            break
                # Ignore any paragraph tag closing events.

        # At the end of the dump, close any remaining inline formatting.
        while active_inline:
            _, closing = active_inline.pop()
            html += closing
        # End the final paragraph.
        html += "</p>"
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>
{html}
</body>
</html>"""

    def set_text(self, text):
        """Set text to editor"""
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(tk.END, text)

    def set_filename(self, text):
        """Set filename"""
        self.toolbar_file_name.config(text=text)

    def mark_edit_separator(self):
        """Mark undo separator"""
        self.text_editor.edit_separator()

    def edit_undo(self):
        """Undo"""
        self.text_editor.edit_undo()

    def edit_redo(self):
        """Redo"""
        self.text_editor.edit_redo()

    # SEARCH IN TEXT EDITOR
    def search_text(self, text):
        """Search text in editor"""
        search_string = Utils.remove_accents(text.replace("\n", "").lower())
        if self.last_search == search_string:
            return
        self.last_search = search_string
        self.last_match_index = 0
        self.tag_remove(SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        self.tag_remove(CURRENT_SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        expression = rf"{search_string}"
        self.search_matches = list(
            re.finditer(expression, Utils.remove_accents(self.doc.text.lower()), flags=re.UNICODE))
        if len(self.search_matches) == 0:
            return
        editor_counts = self.text_editor.count("1.0", self.text_editor.index(tk.INSERT), "chars")
        carrent_position = 0
        if editor_counts is not None:
            carrent_position = self.text_editor.count("1.0", self.text_editor.index(tk.INSERT), "chars")[0]
        first_match_highlighted = False
        for i, match in enumerate(self.search_matches):
            start, end = match.span()
            start_index = f"1.0 + {start} chars"
            end_index = f"1.0 + {end} chars"
            self.tag_add(SEARCH_RESULT_TAG_NAME, start_index, end_index)
            if not first_match_highlighted and start > carrent_position:
                self.last_match_index = i
        self.highlight_search()
        self.text_editor.tag_raise(CURRENT_SEARCH_RESULT_TAG_NAME)

    def reset_search(self):
        """Reset search"""
        self.search_matches.clear()
        self.last_search = ''
        self.last_match_index = 0

    def next_search(self, event):
        """Jump to next search result"""
        results_count = len(self.search_matches)
        if results_count == 0:
            return
        self.last_match_index = (self.last_match_index + 1) % results_count
        self.highlight_search()

    def prev_search(self, event):
        """Jump to previous search result"""
        results_count = len(self.search_matches)
        if results_count == 0:
            return
        self.last_match_index = (self.last_match_index - 1) % results_count
        self.highlight_search()

    def highlight_search(self):
        """Highlight search results"""
        self.tag_remove(CURRENT_SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        start, end = self.search_matches[self.last_match_index].span()
        start_index = f"1.0 + {start} chars"
        end_index = f"1.0 + {end} chars"
        self.tag_add(CURRENT_SEARCH_RESULT_TAG_NAME, start_index, end_index)
        self.move_carret(end_index)

    def select_all(self, event):
        """Create selection on all text"""
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.text_editor.tag_raise(tk.SEL)
        return "break"

    def focus(self):
        """Focus editor"""
        self.text_editor.focus()
        return

    def jump_to_next_word_occourence(self, event, trigger, tag_prefix=CLOSE_WORD_PREFIX):
        """Jump to next tag, prefiexed by tag_tag_prefix"""
        self.focus()
        # Získanie indexu myši
        mouse_index = trigger.index(f"@{event.x},{event.y}")
        # Získanie všetkých tagov na pozícii myši
        tags_at_mouse = trigger.tag_names(mouse_index)
        for tag in tags_at_mouse:
            if tag.startswith(tag_prefix):
                next_range = self.text_editor.tag_nextrange(tag, self.text_editor.index(tk.INSERT))
                if not next_range:
                    next_range = self.text_editor.tag_nextrange(tag, '0.0')
                if next_range:
                    self.move_carret(next_range[1])
        return "break"

    # noinspection PyMethodMayBeStatic
    def get_hunspell_suggestions(self, token):
        """Get hunspell suggestion for token"""
        return ", ".join(RunContext().spellcheck_dictionary.suggest(token.lower_))

    def handle_clipboard_paste(self, event):
        """Handle paste event"""
        # GET CLIPBOARD
        try:
            clipboard_text = event.widget.selection_get(selection='CLIPBOARD')
        except tk.TclError:
            clipboard_text = ''

        self._paste_text(clipboard_text, event)
        # CANCEL DEFAULT PASTE
        return "break"

    def analyze_text(self, force_full_analysis=False):
        """Execute test analysis"""
        text = self.text_editor.get(1.0, tk.END)
        if not force_full_analysis and self.doc.text == text:
            return
        ctx = RunContext()
        config = ConfigService.select_config(ctx.global_config, ctx.project, ctx.current_file)
        # GET TEXT FROM EDITOR
        # RUN ANALYSIS
        if not force_full_analysis and len(text) > 100 and abs(
                len(self.doc.text) - len(text)) < 20 and config.analysis_settings.enable_partial_nlp:
            # PARTIAL NLP
            carret_position = self.get_carret_position(tk.INSERT)
            if carret_position is not None:
                self.doc = NlpService.partial_analysis(text, self.doc, ctx.nlp, config, carret_position)
                self.mark_edit_separator()
            else:
                # FALLBACK TO FULL NLP
                self.doc = NlpService.full_analysis(text, ctx.nlp, NLP_BATCH_SIZE, config)
                self.mark_edit_separator()
                self.reset_search()
        else:
            # FULL NLP
            # FALLBACK TO FULL NLP
            self.doc = NlpService.full_analysis(text, ctx.nlp, NLP_BATCH_SIZE, config)
            self.mark_edit_separator()
            self.reset_search()
        # CLEAR TAGS
        self.clear_tags()
        # SETUP PARAGRAPH TAGGING
        for paragraph in self.doc._.paragraphs:
            start_index = f"1.0 + {paragraph.start_char} chars"
            end_index = f"1.0 + {paragraph.end_char} chars"
            self.tag_add(PARAGRAPH_TAG_NAME, start_index, end_index)
        # RUN ANALYSIS FUNCTIONS
        self._highlight_long_sentences(self.doc, config)
        self._highlight_close_words(self.doc, config)
        self._highlight_multiple_spaces(self.doc, config)
        self._highlight_multiple_punctuation(self.doc, config)
        self._highlight_trailing_spaces(self.doc, config)
        self._highlight_quote_mark_errors(self.doc, config)
        self._run_spellcheck(self.doc, config)
        self.setup_tags(config)
        # MOUSE BINDINGS
        GuiUtils.bind_tag_mouse_event(CLOSE_WORD_TAG_NAME,
                                      self.text_editor,
                                      lambda e: self.highlight_same_word(e, self.text_editor),
                                      lambda e: self.unhighlight_same_word(e)
                                      )
        # CLEAR DEBOUNCE TIMER IF ANY
        self.analyze_text_debounce_timer = None
        self.on_text_analyzed(self.doc)

    def highlight_same_word(self, event, trigger, tag_prefix=CLOSE_WORD_PREFIX, tooltip=None):
        """Highlight tag prefixed by tag_prefix"""
        self.unhighlight_same_word(event)
        # Získanie indexu myši
        mouse_index = trigger.index(f"@{event.x},{event.y}")
        if tooltip is not None:
            abs_x = trigger.winfo_rootx() + event.x
            abs_y = trigger.winfo_rooty() + event.y
            self.tooltip.show(tooltip, abs_x, abs_y)
        # Získanie všetkých tagov na pozícii myši
        tags_at_mouse = trigger.tag_names(mouse_index)
        self.word_freq_text.config(cursor="hand2")
        self.close_words_text.config(cursor="hand2")
        for tag in tags_at_mouse:
            if tag.startswith(tag_prefix):
                self.highlighted_word = tag
                self.text_editor.tag_config(tag, background="white", foreground="black")
                self.close_words_text.tag_config(tag, background="white", foreground="black")
                self.word_freq_text.tag_config(tag, background="white", foreground="black")

    def unhighlight_same_word(self, event):
        """Unhiglight last higlight triggered by highlight_same_word method"""
        if self.highlighted_word is not None and len(self.highlighted_word) > 0:
            tags = [self.highlighted_word]
            parts = self.highlighted_word.split(":")
            if len(parts) > 1:
                tags.append(parts[0])
            for tag in tags:
                self.word_freq_text.config(cursor="xterm")
                self.close_words_text.config(cursor="xterm")
                original_color = self.close_word_colors.get(tag, "")
                self.text_editor.tag_config(tag, background="", foreground=original_color)
                self.close_words_text.tag_config(tag, background="", foreground="")
                self.word_freq_text.tag_config(tag, background="", foreground="")
            self.tooltip.hide()
            self.highlighted_word = None

    def _editor_on_mouse_motion(self, event):
        """Mouse motion handling"""
        x, y = event.x, event.y
        index = self.text_editor.index(f"@{x},{y}")
        current_tags = set(self.tag_names(index)) - FORMATTING_TAGS
        if current_tags != self.last_tags:
            if current_tags:
                # There are tags under the mouse
                error_messages = self._convert_tags_to_error_messages(current_tags, index)
                if error_messages:
                    tooltip_text = "\n---\n".join(error_messages)
                    # Get the absolute position of the mouse
                    abs_x = self.text_editor.winfo_rootx() + x
                    abs_y = self.text_editor.winfo_rooty() + y
                    self.tooltip.show(tooltip_text, abs_x, abs_y)
                else:
                    self.tooltip.hide()
            else:
                # No tags under the mouse
                self.tooltip.hide()
        self.last_tags = current_tags

    def _editor_on_mouse_leave(self, event):
        """Mouse leave handling"""
        self.tooltip.hide()
        self.last_tags = set()

    def _convert_tags_to_error_messages(self, current_tags, index):
        """Convert set of tags (usually under cursor) to set of error messages for user"""
        error_messages = set()
        tag_message_map = {
            LONG_SENTENCE_TAG_NAME_MID: 'Táto veta je trochu dlhšia.',
            LONG_SENTENCE_TAG_NAME_HIGH: 'Táto veta je dlhá.',
            MULTIPLE_PUNCTUATION_TAG_NAME: 'Viacnásobná interpunkcia.',
            TRAILING_SPACES_TAG_NAME: 'Zbytočná medzera na konci odstavca.',
            COMPUTER_QUOTE_MARKS_TAG_NAME: 'Počítačová úvodzovka. V beletrii by sa mali používať '
                                           'slovenské úvodzovky „ “.\n\nPOZOR! Nesprávne úvodzovky '
                                           'môžu narušiť správne určenie hraníc viet!',
            DANGLING_QUOTE_MARK_TAG_NAME: 'Úvodzovka by nemala mať medzeru z oboch strán.',
            SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME: 'Tu by mala byť použitá spodná („) úvozdovka.',
            SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME: 'Tu by mala byť použitá horná (“) úvozdovka.',
            MULTIPLE_SPACES_TAG_NAME: 'Viacnásobná medzera.',
            CLOSE_WORD_TAG_NAME: 'Toto slovo sa opakuje viackrát na krátkom úseku'
        }

        for tag in current_tags:
            if tag in tag_message_map:
                # MAP SIMPLE ERRORS
                error_messages.add(tag_message_map[tag])
            elif tag == GRAMMAR_ERROR_TAG_NAME:
                # SPECIAL HANDLING FOR GRAMMAR_ERRORS
                word_position = self.text_editor.count("1.0", index, "chars")
                if word_position is not None:
                    span = self.doc.char_span(word_position[0], word_position[0], alignment_mode='expand')
                    if span is not None:
                        token = span.root
                        grammar_error_map = {
                            GRAMMAR_ERROR_TYPE_MISSPELLED_WORD: lambda: f'Možný preklep v slove.\n\nNávrhy: '
                                                                        f'{self.get_hunspell_suggestions(token)}',
                            GRAMMAR_ERROR_NON_LITERAL_WORD: lambda: f'Slovo nie je spisovné.\n\n'
                                                                    f'Návrh: {NON_LITERAL_WORDS[token.lower_]}',
                            GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO: lambda: 'Výraz nie je spisovný.\n\nNávrh: to',
                            GRAMMAR_ERROR_S_INSTEAD_OF_Z: lambda: 'Chybná predložka.\n\nNávrh: z/zo',
                            GRAMMAR_ERROR_Z_INSTEAD_OF_S: lambda: 'Chybná predložka.\n\nNávrh: s/so',
                            GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR: lambda: 'Privlasťnovacie zámená majú '
                                                                      'v datíve množného tvar bez dĺžňa.',
                            GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING: lambda: 'Privlasťnovacie zámená majú '
                                                                      'v inštrumentáli jednotného čísla tvar s dĺžňom.',
                            GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX: lambda: f'Slovo by malo končiť na í.\n\n'
                                                                       f'Návrhy: {span.root.text[:-1] + "í"}',
                            GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX: lambda: f'Slovo by malo končiť na ý.\n\n'
                                                                       f'Návrhy: {span.root.text[:-1] + "ý"}',
                            GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX: lambda: f'Slovo by malo končiť na ísi.\n\n'
                                                                         f'Návrhy: {span.root.text[:-3] + "ísi"}',
                            GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX: lambda: f'Slovo by malo končiť na ýsi.\n\n'
                                                                         f'Návrhy: {span.root.text[:-3] + "ýsi"}'
                        }
                        if token._.grammar_error_type in grammar_error_map:
                            error_messages.add(grammar_error_map[token._.grammar_error_type]())
        return error_messages

    def _paste_text(self, text, event, force_full_analysis=True):
        """Paste text"""
        # IF THERE SI SELECTED TEXT IN EDITOR, OVERWRITE IT WITH SELECTED TEXT
        if event.widget.tag_ranges(tk.SEL):
            event.widget.delete("sel.first", "sel.last")
        # NORMALIZE TEXT
        text = ImportService.normalize_text(text)
        event.widget.insert(tk.INSERT, text)
        self.analyze_text(force_full_analysis=force_full_analysis)
        self.on_text_paste(event)

    def _highlight_long_sentences(self, doc: Doc, config: Config):
        if not config.analysis_settings.enable_long_sentences:
            return
        doc_size = len(doc.text)
        doc_text = doc.text
        for sentence in doc.sents:
            if sentence._.is_long_sentence or sentence._.is_mid_sentence:
                start = sentence.start_char
                while start < doc_size - 1 and (doc_text[start] == '\n' or doc_text[start] == '\r'):
                    start += 1
                start_index = f"1.0 + {start} chars"
                end_index = f"1.0 + {sentence.end_char} chars"
                if sentence._.is_long_sentence:
                    self.tag_add(LONG_SENTENCE_TAG_NAME_HIGH, start_index, end_index)
                else:
                    self.tag_add(LONG_SENTENCE_TAG_NAME_MID, start_index, end_index)

    def _highlight_multiple_spaces(self, doc: Doc, config: Config):
        self.tag_remove(MULTIPLE_SPACES_TAG_NAME, "1.0", tk.END)
        if config.analysis_settings.enable_multiple_spaces:
            matches = NlpService.find_multiple_spaces(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.tag_add(MULTIPLE_SPACES_TAG_NAME, start_index, end_index)

    def _highlight_multiple_punctuation(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_multiple_punctuation:
            matches = NlpService.find_multiple_punctuation(doc)
            for match in matches:
                if match.group() not in ["?!"]:
                    start_index = f"1.0 + {match.start()} chars"
                    end_index = f"1.0 + {match.end()} chars"
                    self.tag_add(MULTIPLE_PUNCTUATION_TAG_NAME, start_index, end_index)

    def _highlight_trailing_spaces(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_trailing_spaces:
            matches = NlpService.find_trailing_spaces(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.tag_add(TRAILING_SPACES_TAG_NAME, start_index, end_index)

    def _highlight_quote_mark_errors(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_quote_corrections:
            matches = NlpService.find_computer_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.tag_add(COMPUTER_QUOTE_MARKS_TAG_NAME, start_index, end_index)
            matches = NlpService.find_dangling_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.tag_add(DANGLING_QUOTE_MARK_TAG_NAME, start_index, end_index)
            matches = NlpService.find_incorrect_lower_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.tag_add(SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME, start_index, end_index)
            matches = NlpService.find_incorrect_upper_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.tag_add(SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME, start_index, end_index)

    def _run_spellcheck(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_spellcheck:
            SpellcheckService.spellcheck(RunContext().spellcheck_dictionary, doc)
            for word in self.doc._.words:
                if word._.has_grammar_error:
                    start_index = f"1.0 + {word.idx} chars"
                    end_index = f"1.0 + {word.idx + len(word.lower_)} chars"
                    self.tag_add(GRAMMAR_ERROR_TAG_NAME, start_index, end_index)

    def _highlight_close_words(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_close_words:
            self.tag_remove("close_word", "1.0", tk.END)
            raw_close_words = NlpService.evaluate_close_words(doc, config)
            self.close_words = {}
            for word in raw_close_words:
                tag_name = f"{CLOSE_WORD_PREFIX}{word}"
                word_partitions = NlpService.partition_close_words(
                    raw_close_words[word],
                    config.analysis_settings.close_words_min_distance_between_words
                )
                self.close_words[word] = {"total": len(raw_close_words[word]), "repetition_groups": word_partitions}
                for word_partition in word_partitions:
                    first_token = word_partition[0]
                    first_token_index = self.text_editor.index(f"1.0+{first_token.idx} chars")
                    first_token_par = first_token_index.split(".")[0]
                    prefix = f"{tag_name}:{CLOSE_WORD_RANGE_PREFIX}"
                    range_tag_name = f"{prefix}{first_token_par}"
                    for occ in word_partition:
                        color = random.choice(CLOSE_WORDS_PALLETE)
                        start_index = f"1.0 + {occ.idx} chars"
                        end_index = f"1.0 + {occ.idx + len(occ.lower_)} chars"
                        tag_name = f"{CLOSE_WORD_PREFIX}{word}"
                        original_color = self.close_word_colors.get(tag_name, "")
                        if original_color != "":
                            color = original_color
                        else:
                            self.close_word_colors[tag_name] = color
                        self.tag_add(tag_name, start_index, end_index)
                        self.tag_add(range_tag_name, start_index, end_index)
                        self.tag_add(CLOSE_WORD_TAG_NAME, start_index, end_index)
                        self.tag_config(tag_name, foreground=color)

    def _on_typing_done(self, event):
        if self.analyze_text_debounce_timer is not None:
            self.root.after_cancel(self.analyze_text_debounce_timer)
        # PREVENT STANDARD ANALYSIS ON CTRL+V
        if event.state & 0x0004 and event.keysym != 'v':
            return
        self.analyze_text_debounce_timer = self.root.after(
            NLP_DEBOUNCE_LENGTH,
            self.analyze_text,
            False
        )

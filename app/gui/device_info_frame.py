"""Device information display tab."""
import customtkinter as ctk

from app.gui.styles import COLORS, FONTS, PADDING


class DeviceInfoFrame(ctk.CTkFrame):
    """Tab displaying device metadata from the backup."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._labels: list[tuple[ctk.CTkLabel, ctk.CTkLabel]] = []
        self._build_placeholder()

    def _build_placeholder(self):
        self._placeholder = ctk.CTkLabel(
            self,
            text="Load a backup to see device information",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
        )
        self._placeholder.pack(expand=True)

    def populate(self, info_pairs: list[tuple[str, str]]):
        """
        Populate with (label, value) pairs from format_device_info().
        Empty labels serve as section separators.
        """
        # Clear existing
        for widget in self.winfo_children():
            widget.destroy()
        self._labels = []

        # Scrollable container
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        scroll.pack(fill="both", expand=True, padx=PADDING["section"], pady=PADDING["section"])

        # Configure grid columns
        scroll.grid_columnconfigure(0, weight=0, minsize=180)
        scroll.grid_columnconfigure(1, weight=1)

        row = 0
        for label_text, value_text in info_pairs:
            if not label_text:
                # Separator
                sep = ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"])
                sep.grid(
                    row=row, column=0, columnspan=2, sticky="ew",
                    pady=PADDING["widget"],
                )
                row += 1
                continue

            label = ctk.CTkLabel(
                scroll,
                text=label_text,
                font=FONTS["label"],
                text_color=COLORS["text_secondary"],
                anchor="w",
            )
            label.grid(
                row=row, column=0, sticky="w",
                padx=(0, PADDING["section"]),
                pady=2,
            )

            value = ctk.CTkLabel(
                scroll,
                text=value_text,
                font=FONTS["value"],
                text_color=COLORS["text"],
                anchor="w",
            )
            value.grid(row=row, column=1, sticky="w", pady=2)

            # Make long values selectable via right-click copy
            value.bind("<Button-3>", lambda e, v=value_text: self._copy_to_clipboard(v))

            self._labels.append((label, value))
            row += 1

    def _copy_to_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()
        self._labels = []
        self._build_placeholder()

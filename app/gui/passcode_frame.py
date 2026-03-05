"""Screen Time / Restrictions passcode display tab."""
import customtkinter as ctk

from app.gui.styles import COLORS, FONTS, PADDING


class PasscodeFrame(ctk.CTkFrame):
    """Tab showing the extracted passcode with status and details."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(expand=True, fill="both", padx=PADDING["section"], pady=PADDING["section"])

        # Status icon / label area
        self._status_label = ctk.CTkLabel(
            self._container,
            text="Load a backup to extract the passcode",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
        )
        self._status_label.pack(pady=(40, 10))

        # Large passcode display
        self._passcode_label = ctk.CTkLabel(
            self._container,
            text="",
            font=FONTS["mono_large"],
            text_color=COLORS["passcode_found"],
        )
        self._passcode_label.pack(pady=10)

        # Method / details
        self._method_label = ctk.CTkLabel(
            self._container,
            text="",
            font=FONTS["body_small"],
            text_color=COLORS["text_secondary"],
        )
        self._method_label.pack(pady=4)

        # Progress bar (hidden by default)
        self._progress_frame = ctk.CTkFrame(self._container, fg_color="transparent")

        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame, width=400, height=16
        )
        self._progress_bar.pack(pady=4)
        self._progress_bar.set(0)

        self._progress_text = ctk.CTkLabel(
            self._progress_frame,
            text="",
            font=FONTS["body_small"],
            text_color=COLORS["text_secondary"],
        )
        self._progress_text.pack(pady=2)

        # Details section
        self._details_frame = ctk.CTkFrame(
            self._container, fg_color=COLORS["bg_card"], corner_radius=8
        )

        self._details_text = ctk.CTkTextbox(
            self._details_frame,
            font=FONTS["mono"],
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["bg_card"],
            height=150,
            wrap="word",
            state="disabled",
        )
        self._details_text.pack(fill="both", expand=True, padx=8, pady=8)

    def show_searching(self):
        """Show that passcode search is in progress."""
        self._status_label.configure(
            text="Searching for passcode...",
            text_color=COLORS["info"],
        )
        self._passcode_label.configure(text="")
        self._method_label.configure(text="")
        self._progress_frame.pack(pady=10, after=self._passcode_label)
        self._progress_bar.set(0)
        self._progress_text.configure(text="Initializing...")

    def update_progress(self, current: int, total: int, phase: str = ""):
        """Update the progress bar during brute force."""
        progress = current / total if total > 0 else 0
        self._progress_bar.set(progress)
        pct = int(progress * 100)
        text = f"{phase} {pct}% ({current:,}/{total:,})" if phase else f"{pct}%"
        self._progress_text.configure(text=text)

    def show_result(self, result: dict):
        """Display the extraction result."""
        self._progress_frame.pack_forget()

        found = result.get("found", False)
        passcode = result.get("passcode")
        method = result.get("method", "")
        ios_range = result.get("ios_range", "")
        time_taken = result.get("time_taken", 0)
        error = result.get("error")
        details = result.get("details", [])

        if found and passcode:
            self._status_label.configure(
                text="Passcode Found!",
                text_color=COLORS["passcode_found"],
                font=FONTS["heading"],
            )
            self._passcode_label.configure(
                text=passcode,
                text_color=COLORS["passcode_found"],
            )
            method_text = f"Method: {method}"
            if ios_range:
                method_text += f" | {ios_range}"
            if time_taken > 0:
                method_text += f" | Cracked in {time_taken:.1f}s"
            self._method_label.configure(text=method_text)
        else:
            self._status_label.configure(
                text="Passcode Not Found",
                text_color=COLORS["passcode_not_found"],
                font=FONTS["heading"],
            )
            self._passcode_label.configure(text="")
            self._method_label.configure(
                text=error or "Could not extract passcode from this backup"
            )

        # Show details
        if details or error:
            self._details_frame.pack(
                fill="x", pady=(20, 0), padx=20,
                after=self._method_label,
            )
            self._details_text.configure(state="normal")
            self._details_text.delete("1.0", "end")
            all_details = []
            if details:
                all_details.extend(details)
            if error and error not in details:
                all_details.append(f"Error: {error}")
            self._details_text.insert("1.0", "\n".join(all_details))
            self._details_text.configure(state="disabled")
        else:
            self._details_frame.pack_forget()

    def clear(self):
        """Reset to initial state."""
        self._status_label.configure(
            text="Load a backup to extract the passcode",
            text_color=COLORS["text_muted"],
            font=FONTS["body"],
        )
        self._passcode_label.configure(text="")
        self._method_label.configure(text="")
        self._progress_frame.pack_forget()
        self._details_frame.pack_forget()

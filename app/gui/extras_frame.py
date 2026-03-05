"""WiFi networks and extra information tab."""
import customtkinter as ctk

from app.gui.styles import COLORS, FONTS, PADDING


class ExtrasFrame(ctk.CTkFrame):
    """Tab for WiFi networks and other extracted data."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_placeholder()

    def _build_placeholder(self):
        self._placeholder = ctk.CTkLabel(
            self,
            text="Load a backup to see WiFi networks and other data",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
        )
        self._placeholder.pack(expand=True)

    def populate(self, wifi_networks: list[dict] = None, extra_info: dict = None):
        """Populate with WiFi networks and extra data."""
        for widget in self.winfo_children():
            widget.destroy()

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        scroll.pack(fill="both", expand=True, padx=PADDING["section"], pady=PADDING["section"])

        has_content = False

        # WiFi Networks section
        if wifi_networks:
            has_content = True
            ctk.CTkLabel(
                scroll,
                text=f"Known WiFi Networks ({len(wifi_networks)})",
                font=FONTS["subheading"],
                text_color=COLORS["text"],
            ).pack(anchor="w", pady=(0, 8))

            for net in wifi_networks:
                net_frame = ctk.CTkFrame(
                    scroll, fg_color=COLORS["bg_card"], corner_radius=6
                )
                net_frame.pack(fill="x", pady=2)

                inner = ctk.CTkFrame(net_frame, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=6)

                # SSID (left)
                ssid = net.get("ssid", "Unknown")
                ctk.CTkLabel(
                    inner,
                    text=ssid,
                    font=FONTS["body"],
                    text_color=COLORS["text"],
                    anchor="w",
                ).pack(side="left")

                # Last joined (right)
                last_joined = net.get("last_joined", "")
                if last_joined:
                    ctk.CTkLabel(
                        inner,
                        text=last_joined,
                        font=FONTS["body_small"],
                        text_color=COLORS["text_muted"],
                        anchor="e",
                    ).pack(side="right")

                # Security
                security = net.get("security", "")
                if security:
                    ctk.CTkLabel(
                        inner,
                        text=security,
                        font=FONTS["body_small"],
                        text_color=COLORS["text_secondary"],
                        anchor="e",
                    ).pack(side="right", padx=(0, 12))

        # Extra info section
        if extra_info:
            has_content = True
            if wifi_networks:
                ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"]).pack(
                    fill="x", pady=12
                )

            ctk.CTkLabel(
                scroll,
                text="Additional Information",
                font=FONTS["subheading"],
                text_color=COLORS["text"],
            ).pack(anchor="w", pady=(0, 8))

            info_frame = ctk.CTkFrame(
                scroll, fg_color=COLORS["bg_card"], corner_radius=6
            )
            info_frame.pack(fill="x", pady=2)
            info_frame.grid_columnconfigure(1, weight=1)

            row = 0
            for key, value in extra_info.items():
                ctk.CTkLabel(
                    info_frame,
                    text=key,
                    font=FONTS["label"],
                    text_color=COLORS["text_secondary"],
                    anchor="w",
                ).grid(row=row, column=0, sticky="w", padx=10, pady=3)

                ctk.CTkLabel(
                    info_frame,
                    text=str(value),
                    font=FONTS["value"],
                    text_color=COLORS["text"],
                    anchor="w",
                ).grid(row=row, column=1, sticky="w", padx=10, pady=3)
                row += 1

        if not has_content:
            ctk.CTkLabel(
                scroll,
                text="No WiFi or additional data found in this backup",
                font=FONTS["body"],
                text_color=COLORS["text_muted"],
            ).pack(expand=True, pady=40)

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()
        self._build_placeholder()

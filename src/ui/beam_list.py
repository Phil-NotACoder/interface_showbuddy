import tkinter as tk
from tkinter import ttk
from .widgets import ScrollableFrame, RotaryDial


class BeamListView(ttk.Frame):
    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.rows = {}

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        self.inner = self.scroll_frame.scrollable_frame

    def render(self, state):
        current_ids = set(state.fixtures.keys())
        existing_ids = set(self.rows.keys())

        for fid in existing_ids - current_ids:
            self.rows[fid]["frame"].destroy()
            del self.rows[fid]

        for fid in current_ids - existing_ids:
            self._create_fixture_strip(fid, state.fixtures[fid])

        for fid in current_ids:
            self._update_fixture_strip(fid, state.fixtures[fid], state)

    def _create_fixture_strip(self, fid, fix):
        frame = tk.Frame(self.inner, bg="#141414", bd=1, relief="solid")
        frame.pack(fill="x", padx=5, pady=5)

        header = tk.Frame(frame, bg="#141414")
        header.pack(fill="x", padx=5, pady=5)

        lbl = tk.Label(header, text=f"FIX {fid}", fg="white", bg="#141414", font=("Arial", 10, "bold"))
        lbl.pack(side="left")

        btn = tk.Button(header, text="MODE", width=8, relief="flat",
                        command=lambda f=fid: self._toggle_shape(f))
        btn.pack(side="right")

        # --- ZONE DE CONTRÔLES À HAUTEUR FIXE ---
        controls_container = tk.Frame(frame, bg="#141414", height=85)
        controls_container.pack(fill="x", padx=5, pady=5)
        controls_container.pack_propagate(False)

        # --- CONTROLES ROUND (Size) ---
        round_controls = tk.Frame(controls_container, bg="#141414")
        # Protection getattr
        size_val = getattr(fix, "size", 20.0)
        size_var = tk.DoubleVar(value=size_val)
        self._create_slider(round_controls, "Size", size_var, 5, 150, fid, "size")

        # --- CONTROLES BEAM (Angle, Len, Cone) ---
        beam_controls = tk.Frame(controls_container, bg="#141414")

        dial_frame = tk.Frame(beam_controls, bg="#141414")
        dial_frame.pack(side="left", padx=5)
        tk.Label(dial_frame, text="Angle", fg="#aaa", bg="#141414", font=("Arial", 8)).pack()

        # Protection getattr
        angle_val = getattr(fix, "angle", 0.0)
        dial = RotaryDial(dial_frame, size=40, min_val=0, max_val=360, initial_val=angle_val,
                          bg="#141414", command=lambda v, f=fid: self._on_dial_change(f, v))
        dial.pack(pady=2)

        sliders_frame = tk.Frame(beam_controls, bg="#141414")
        sliders_frame.pack(side="left", fill="x", expand=True, padx=5)

        # Protection getattr
        len_val = getattr(fix, "beam_length", 100.0)
        cone_val = getattr(fix, "cone_angle", 45.0)

        len_var = tk.DoubleVar(value=len_val)
        cone_var = tk.DoubleVar(value=cone_val)

        self._create_slider(sliders_frame, "Len", len_var, 10, 300, fid, "beam_length")
        self._create_slider(sliders_frame, "Cone", cone_var, 10, 160, fid, "cone_angle")

        self.rows[fid] = {
            "frame": frame,
            "header_bg": header,
            "lbl": lbl,
            "btn": btn,
            "controls_container": controls_container,
            "round_controls": round_controls,
            "beam_controls": beam_controls,
            "size_var": size_var,
            "dial": dial,
            "len_var": len_var,
            "cone_var": cone_var
        }

    def _create_slider(self, parent, label, var, min_v, max_v, fid, param):
        f = tk.Frame(parent, bg="#141414")
        f.pack(fill="x", pady=2)
        tk.Label(f, text=label, fg="#ccc", bg="#141414", width=4, anchor="w", font=("Arial", 8)).pack(side="left")

        scale = tk.Scale(f, variable=var, from_=min_v, to=max_v, orient="horizontal",
                         bg="#141414", fg="white", troughcolor="#333", highlightthickness=0, showvalue=0)
        scale.pack(side="left", fill="x", expand=True)

        var.trace_add("write", lambda *args: self._on_val_change(fid, param, var.get()))

    def _update_fixture_strip(self, fid, fix, state):
        row = self.rows[fid]

        bg = "#2b2b2b" if fid == state.selected_fixture_id else "#141414"
        row["frame"].configure(bg=bg)
        row["header_bg"].configure(bg=bg)
        row["lbl"].configure(bg=bg)
        row["controls_container"].configure(bg=bg)
        row["round_controls"].configure(bg=bg)
        row["beam_controls"].configure(bg=bg)

        # Protection getattr
        shape = getattr(fix, "shape", "circle")

        if shape == "beam":
            row["btn"].configure(text="BEAM", fg="#d4af37", bg="#444")
            row["round_controls"].pack_forget()
            row["beam_controls"].pack(fill="both", expand=True)
        else:
            row["btn"].configure(text="ROUND", fg="#888", bg="#333")
            row["beam_controls"].pack_forget()
            row["round_controls"].pack(fill="both", expand=True)

        # Protection getattr pour les valeurs
        angle_val = getattr(fix, "angle", 0.0)
        len_val = getattr(fix, "beam_length", 100.0)
        cone_val = getattr(fix, "cone_angle", 45.0)
        size_val = getattr(fix, "size", 20.0)

        if abs(row["dial"].value - angle_val) > 1.0:
            row["dial"].set_value(angle_val)
        if abs(row["len_var"].get() - len_val) > 0.5:
            row["len_var"].set(len_val)
        if abs(row["cone_var"].get() - cone_val) > 0.5:
            row["cone_var"].set(cone_val)

        if abs(row["size_var"].get() - size_val) > 0.5:
            row["size_var"].set(size_val)

    def _toggle_shape(self, fid):
        btn = self.rows[fid]["btn"]
        current_text = btn.cget("text")
        new_shape = "circle" if current_text == "BEAM" else "beam"
        if self.on_change:
            self.on_change(fid, "shape", new_shape, send_osc=False)

    def _on_dial_change(self, fid, value):
        if self.on_change:
            self.on_change(fid, "angle", value, send_osc=False)

    def _on_val_change(self, fid, param, value):
        if self.on_change:
            self.on_change(fid, param, float(value), send_osc=False)
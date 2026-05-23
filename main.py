import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from collections import deque
from datetime import datetime

from data_simulator import MachineDataSimulator
from anomaly_detector import AnomalyDetector
from database import Database

BG_BASE   = "#1e1e2e"
BG_MANTLE = "#181825"
BG_CARD   = "#2a2a3e"
FG_TEXT   = "#cdd6f4"
FG_SUBTEXT= "#a6adc8"
FG_ACCENT = "#89b4fa"
FG_GREEN  = "#a6e3a1"
FG_YELLOW = "#f9e2af"
FG_RED    = "#f38ba8"
FG_GRAY   = "#6c7086"

CHART_COLORS = ["#89b4fa", "#a6e3a1", "#fab387", "#cba6f7"]

MAX_POINTS  = 120
REFRESH_MS  = 1_000
STATS_EVERY = 10

PARAMS = list(MachineDataSimulator.PARAMS.keys())


class PlcMonitorApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("PLC Monitor Pro  \u2014  System Monitorowania Maszyn")
        self.geometry("1280x760")
        self.minsize(960, 620)
        self.configure(bg=BG_BASE)

        self.simulator = MachineDataSimulator(anomaly_prob=0.04)
        self.detector  = AnomalyDetector(window=60, z_thresh=3.5)
        self.db        = Database()

        self.running   = False
        self._counter  = 0

        self.time_buf  = deque(maxlen=MAX_POINTS)
        self.data_bufs = {p: deque(maxlen=MAX_POINTS) for p in PARAMS}
        self.cur_val   = {p: 0.0  for p in PARAMS}
        self.cur_stat  = {p: "OK" for p in PARAMS}

        self._build_style()
        self._build_ui()
        self._update_stats_tab()
        self._tick_clock()

    def _build_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",          background=BG_BASE,   borderwidth=0)
        s.configure("TNotebook.Tab",      background=BG_CARD,   foreground=FG_GRAY,
                    font=("Segoe UI", 10), padding=[18, 6])
        s.map("TNotebook.Tab",
              background=[("selected", BG_BASE)],
              foreground=[("selected", FG_ACCENT)])
        s.configure("Treeview",           background=BG_CARD,   foreground=FG_TEXT,
                    fieldbackground=BG_CARD, font=("Segoe UI", 9), rowheight=26)
        s.configure("Treeview.Heading",   background=BG_MANTLE, foreground=FG_ACCENT,
                    font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("Treeview",                 background=[("selected", "#45475a")])
        s.configure("Vertical.TScrollbar", background=BG_CARD,
                    troughcolor=BG_MANTLE, borderwidth=0)

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG_MANTLE, pady=7)
        bar.pack(fill="x", side="top")
        tk.Label(bar, text="\u2699  PLC Monitor Pro",
                 font=("Segoe UI", 13, "bold"),
                 bg=BG_MANTLE, fg=FG_ACCENT).pack(side="left", padx=16)
        self.status_lbl = tk.Label(bar, text="\u25cf  ZATRZYMANO",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=BG_MANTLE, fg=FG_GRAY)
        self.status_lbl.pack(side="left", padx=20)
        btn_f = tk.Frame(bar, bg=BG_MANTLE)
        btn_f.pack(side="right", padx=14)
        def btn(parent, text, cmd, bg, state="normal"):
            return tk.Button(parent, text=text, command=cmd,
                             font=("Segoe UI", 9, "bold"),
                             bg=bg, fg="white", relief="flat",
                             padx=14, pady=5, cursor="hand2",
                             state=state,
                             activebackground=bg, activeforeground="white")
        self.start_btn = btn(btn_f, "\u25b6  START",    self.start_monitoring, "#1a6b3a")
        self.start_btn.pack(side="left", padx=3)
        self.stop_btn  = btn(btn_f, "\u25a0  STOP",     self.stop_monitoring,  "#6b1a1a", "disabled")
        self.stop_btn.pack(side="left", padx=3)
        btn(btn_f, "\u2b07  Eksport CSV",    self.export_readings,  "#2a2a3e").pack(side="left", padx=3)
        btn(btn_f, "\u2b07  Eksport alerty", self.export_anomalies, "#2a2a3e").pack(side="left", padx=3)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_MANTLE, pady=3)
        bar.pack(fill="x", side="bottom")
        self.lbl_reads   = tk.Label(bar, text="Odczyty: 0",
                                    font=("Segoe UI", 8), bg=BG_MANTLE, fg=FG_GRAY)
        self.lbl_reads.pack(side="left", padx=12)
        self.lbl_anomaly = tk.Label(bar, text="Anomalie: 0",
                                    font=("Segoe UI", 8), bg=BG_MANTLE, fg=FG_GRAY)
        self.lbl_anomaly.pack(side="left", padx=12)
        self.lbl_clock   = tk.Label(bar, text="",
                                    font=("Segoe UI", 8), bg=BG_MANTLE, fg=FG_GRAY)
        self.lbl_clock.pack(side="right", padx=12)

    def _build_ui(self):
        self._build_topbar()
        self._build_statusbar()
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self.notebook = nb
        self._build_tab_monitor(nb)
        self._build_tab_alerts(nb)
        self._build_tab_stats(nb)

    def _build_tab_monitor(self, nb):
        frame = tk.Frame(nb, bg=BG_BASE)
        nb.add(frame, text="  \U0001f4ca  Monitor  ")
        cards_row = tk.Frame(frame, bg=BG_BASE)
        cards_row.pack(fill="x", padx=10, pady=(8, 4))
        self.val_lbl  = {}
        self.stat_lbl = {}
        for i, param in enumerate(PARAMS):
            cfg  = MachineDataSimulator.PARAMS[param]
            card = tk.Frame(cards_row, bg=BG_CARD, padx=10, pady=6)
            card.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(card, text=param,
                     font=("Segoe UI", 9), bg=BG_CARD, fg=FG_SUBTEXT).pack()
            vl = tk.Label(card, text="\u2014",
                          font=("Segoe UI", 22, "bold"),
                          bg=BG_CARD, fg=CHART_COLORS[i])
            vl.pack()
            self.val_lbl[param] = vl
            tk.Label(card, text=cfg["unit"],
                     font=("Segoe UI", 8), bg=BG_CARD, fg=FG_GRAY).pack()
            sl = tk.Label(card, text="\u25cf  OK",
                          font=("Segoe UI", 8, "bold"),
                          bg=BG_CARD, fg=FG_GREEN, pady=3)
            sl.pack()
            self.stat_lbl[param] = sl
        chart_frame = tk.Frame(frame, bg=BG_BASE)
        chart_frame.pack(fill="both", expand=True, padx=8, pady=(2, 6))
        self.fig  = Figure(facecolor=BG_BASE)
        self.fig.subplots_adjust(hspace=0.42, wspace=0.30,
                                 left=0.07, right=0.97,
                                 top=0.93, bottom=0.08)
        self.axes  = []
        self.lines = []
        for i, param in enumerate(PARAMS):
            cfg = MachineDataSimulator.PARAMS[param]
            ax  = self.fig.add_subplot(2, 2, i + 1)
            ax.set_facecolor(BG_CARD)
            ax.set_title(f"{param}  [{cfg['unit']}]",
                         color=FG_TEXT, fontsize=9, pad=4)
            ax.tick_params(colors=FG_GRAY, labelsize=7)
            ax.set_xlabel("czas [s]", color=FG_GRAY, fontsize=7)
            for sp in ax.spines.values():
                sp.set_color(FG_GRAY)
                sp.set_linewidth(0.5)
            ax.axhline(cfg["alarm_high"], color=FG_RED,    linestyle="--",
                       linewidth=0.8, alpha=0.75, label="Pr\u00f3g g\u00f3rny")
            ax.axhline(cfg["alarm_low"],  color=FG_YELLOW, linestyle="--",
                       linewidth=0.8, alpha=0.75, label="Pr\u00f3g dolny")
            margin = (cfg["alarm_high"] - cfg["alarm_low"]) * 0.15
            ax.set_ylim(cfg["alarm_low"] - margin, cfg["alarm_high"] + margin)
            line, = ax.plot([], [], color=CHART_COLORS[i], linewidth=1.3)
            self.axes.append(ax)
            self.lines.append(line)
        canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        canvas.get_tk_widget().configure(bg=BG_BASE)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.chart_canvas = canvas

    def _build_tab_alerts(self, nb):
        frame = tk.Frame(nb, bg=BG_BASE)
        nb.add(frame, text="  \u26a0  Alerty  ")
        toolbar = tk.Frame(frame, bg=BG_BASE, pady=8)
        toolbar.pack(fill="x", padx=12)
        tk.Label(toolbar, text="Dziennik Anomalii",
                 font=("Segoe UI", 11, "bold"),
                 bg=BG_BASE, fg=FG_TEXT).pack(side="left")
        tk.Button(toolbar, text="Wyczy\u015b\u0107 widok",
                  font=("Segoe UI", 9),
                  bg=BG_CARD, fg=FG_TEXT, relief="flat",
                  padx=10, pady=3, cursor="hand2",
                  command=self._clear_alert_view).pack(side="right")
        cols = ("Czas", "Parametr", "Warto\u015b\u0107", "Pow\u00f3d")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        widths = (140, 120, 90, 500)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=60, stretch=(col == "Pow\u00f3d"))
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 10))
        sb.pack(side="right", fill="y", padx=(0, 6), pady=(0, 10))
        tree.tag_configure("ALARM_H", foreground=FG_RED)
        tree.tag_configure("ALARM_L", foreground=FG_YELLOW)
        tree.tag_configure("STAT",    foreground="#cba6f7")
        self.alert_tree = tree

    def _build_tab_stats(self, nb):
        frame = tk.Frame(nb, bg=BG_BASE)
        nb.add(frame, text="  \U0001f4c8  Statystyki  ")
        self.stats_frame = frame
        summary = tk.Frame(frame, bg=BG_BASE)
        summary.pack(fill="x", padx=12, pady=14)
        self._sw = {}
        for title, key, color in [
            ("\u0141\u0105czne odczyty",    "reads",     FG_ACCENT),
            ("\u0141\u0105czne anomalie",   "anomalies", FG_RED),
            ("Wska\u017anik anomalii", "rate",      FG_YELLOW),
        ]:
            c = tk.Frame(summary, bg=BG_CARD, padx=24, pady=14)
            c.pack(side="left", fill="x", expand=True, padx=6)
            tk.Label(c, text=title, font=("Segoe UI", 9),
                     bg=BG_CARD, fg=FG_SUBTEXT).pack()
            lbl = tk.Label(c, text="\u2014", font=("Segoe UI", 22, "bold"),
                           bg=BG_CARD, fg=color)
            lbl.pack()
            self._sw[key] = lbl
        cf = tk.Frame(frame, bg=BG_BASE)
        cf.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.stats_fig = Figure(facecolor=BG_BASE, tight_layout=True)
        self.stats_ax  = self.stats_fig.add_subplot(1, 1, 1)
        self.stats_ax.set_facecolor(BG_CARD)
        for sp in self.stats_ax.spines.values():
            sp.set_color(FG_GRAY)
        sc = FigureCanvasTkAgg(self.stats_fig, master=cf)
        sc.get_tk_widget().configure(bg=BG_BASE)
        sc.get_tk_widget().pack(fill="both", expand=True)
        self.stats_canvas = sc

    def start_monitoring(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_lbl.config(text="\u25cf  MONITOROWANIE", fg=FG_GREEN)
        self._schedule_update()

    def stop_monitoring(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_lbl.config(text="\u25cf  ZATRZYMANO", fg=FG_GRAY)

    def _schedule_update(self):
        if not self.running:
            return
        self._do_update()
        self.after(REFRESH_MS, self._schedule_update)

    def _do_update(self):
        ts, readings = self.simulator.get_reading()
        self.db.save_reading(ts, readings)
        self._counter += 1
        self.time_buf.append(ts)
        for param, val in readings.items():
            self.data_bufs[param].append(val)
            self.cur_val[param] = val
        for param, val in readings.items():
            cfg = MachineDataSimulator.PARAMS[param]
            is_anom, reason = self.detector.check(
                param, val, cfg["alarm_high"], cfg["alarm_low"]
            )
            if is_anom:
                self.db.save_anomaly(ts, param, val, reason)
                self._append_alert(ts, param, val, reason)
                self.cur_stat[param] = "ALARM"
            else:
                self.cur_stat[param] = "OK"
        self._refresh_cards()
        self._refresh_charts()
        self._refresh_statusbar()
        if self._counter % STATS_EVERY == 0:
            self._update_stats_tab()

    def _refresh_cards(self):
        for param in PARAMS:
            val  = self.cur_val[param]
            stat = self.cur_stat[param]
            self.val_lbl[param].config(text=f"{val:.1f}")
            if stat == "ALARM":
                self.stat_lbl[param].config(text="\u25cf  ALARM", fg=FG_RED)
            else:
                self.stat_lbl[param].config(text="\u25cf  OK",    fg=FG_GREEN)

    def _refresh_charts(self):
        ts_list = list(self.time_buf)
        if not ts_list:
            return
        t0 = ts_list[0]
        x  = [t - t0 for t in ts_list]
        for ax, line, param in zip(self.axes, self.lines, PARAMS):
            y = list(self.data_bufs[param])
            n = min(len(x), len(y))
            if n == 0:
                continue
            line.set_data(x[:n], y[:n])
            ax.set_xlim(0, max(x[-1], 10))
        self.chart_canvas.draw_idle()

    def _append_alert(self, ts, param, val, reason):
        cfg      = MachineDataSimulator.PARAMS[param]
        time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        val_str  = f"{val:.2f} {cfg['unit']}"
        if "g\u00f3rny" in reason:
            tag = "ALARM_H"
        elif "dolny" in reason:
            tag = "ALARM_L"
        else:
            tag = "STAT"
        self.alert_tree.insert("", 0,
                               values=(time_str, param, val_str, reason),
                               tags=(tag,))
        children = self.alert_tree.get_children()
        if len(children) > 300:
            self.alert_tree.delete(children[-1])

    def _clear_alert_view(self):
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)

    def _update_stats_tab(self):
        total_r = self.db.get_total_readings()
        total_a = self.db.get_total_anomalies()
        rate    = f"{total_a / total_r * 100:.1f} %" if total_r > 0 else "\u2014"
        self._sw["reads"].config(text=str(total_r))
        self._sw["anomalies"].config(text=str(total_a))
        self._sw["rate"].config(text=rate)
        stats = self.db.get_anomaly_stats()
        ax    = self.stats_ax
        ax.cla()
        ax.set_facecolor(BG_CARD)
        for sp in ax.spines.values():
            sp.set_color(FG_GRAY)
        ax.tick_params(colors=FG_GRAY, labelsize=9)
        if stats:
            params = [s[0] for s in stats]
            counts = [s[1] for s in stats]
            colors = [CHART_COLORS[PARAMS.index(p) % len(CHART_COLORS)]
                      if p in PARAMS else FG_ACCENT for p in params]
            bars = ax.bar(params, counts, color=colors, edgecolor="none", width=0.5)
            ax.bar_label(bars, fmt="%d", color=FG_TEXT, fontsize=10, padding=3)
            ax.set_ylabel("Liczba anomalii", color=FG_GRAY, fontsize=9)
        else:
            ax.text(0.5, 0.5, "Brak zarejestrowanych anomalii",
                    ha="center", va="center",
                    color=FG_SUBTEXT, fontsize=11,
                    transform=ax.transAxes)
        ax.set_title("Anomalie wg parametru", color=FG_TEXT, fontsize=10)
        self.stats_canvas.draw_idle()

    def _refresh_statusbar(self):
        self.lbl_reads.config(text=f"Odczyty: {self.db.get_total_readings()}")
        self.lbl_anomaly.config(text=f"Anomalie: {self.db.get_total_anomalies()}")

    def _tick_clock(self):
        self.lbl_clock.config(text=datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    def export_readings(self):
        fp = filedialog.asksaveasfilename(
            title="Zapisz odczyty jako CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"odczyty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if fp:
            try:
                n = self.db.export_csv(fp)
                messagebox.showinfo("Eksport zako\u0144czony",
                                    f"Zapisano {n} wierszy do:\n{fp}")
            except Exception as exc:
                messagebox.showerror("B\u0142\u0105d eksportu", str(exc))

    def export_anomalies(self):
        fp = filedialog.asksaveasfilename(
            title="Zapisz anomalie jako CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"anomalie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if fp:
            try:
                n = self.db.export_anomalies_csv(fp)
                messagebox.showinfo("Eksport zako\u0144czony",
                                    f"Zapisano {n} anomalii do:\n{fp}")
            except Exception as exc:
                messagebox.showerror("B\u0142\u0105d eksportu", str(exc))


if __name__ == "__main__":
    app = PlcMonitorApp()
    app.mainloop()
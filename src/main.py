from __future__ import annotations
import csv, ctypes, hashlib, json, os, queue, re, subprocess, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

APP = "ARK Cheat Detector"
ROOT = Path(__file__).resolve().parent.parent
SIG_FILE = ROOT / "data" / "signatures.json"
PATTERNS = {
    "Aim assistance": re.compile(r"\b(?:aimbot|aim[-_ ]?bot|triggerbot|trigger[-_ ]?bot)\b", re.I),
    "ESP / wall information": re.compile(r"\b(?:esp|wallhack|wall[-_ ]?hack|radar)\b", re.I),
    "Movement or weapon modification": re.compile(r"\b(?:speedhack|speed[-_ ]?hack|no[-_ ]?recoil|recoil[-_ ]?control|rapidfire)\b", re.I),
    "Trainer / memory modification": re.compile(r"\b(?:trainer|memory[-_ ]?editor|cheat[-_ ]?engine)\b", re.I),
    "Code injection terminology": re.compile(r"\b(?:injector|dll[-_ ]?injector)\b", re.I),
    "Generic cheat label": re.compile(r"\b(?:cheat|ark[-_ ]?hack)\b", re.I),
}
TERMS = ("aimbot", "aim bot", "triggerbot", "trigger bot", "esp", "wallhack",
         "wall hack", "radar", "speedhack", "speed hack", "no-recoil",
         "recoil-control", "rapidfire", "trainer", "memory editor",
         "cheat engine", "injector", "cheat", "ark-hack")
BG, PANEL, FG, MUTED, BLUE = "#10151f", "#192333", "#e8eef7", "#9aabc0", "#39a7ff"
SKIP_DIRS = {"$recycle.bin", "system volume information"}

def get_fixed_drives():
    """Return Windows fixed-drive roots, e.g. C:\\\\ and D:\\\\."""
    if os.name != "nt":
        return [Path.home()]
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    drives = []
    for index in range(26):
        if mask & (1 << index):
            root = f"{chr(65 + index)}:\\\\"
            if ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root)) == 3:
                drives.append(Path(root))
    return drives

class Scanner:
    def __init__(self, emit):
        self.emit, self.cancel = emit, False
        self.findings = []
        self.files_scanned = 0
        self.skipped = 0

    def run(self, roots):
        try:
            db = json.loads(SIG_FILE.read_text(encoding="utf-8"))
            hashes = {h.lower() for h in db.get("sha256", [])}
        except Exception:
            hashes = set()
            self.emit("Signature database unavailable; continuing with heuristic checks.")
        # Visible process names only. No process memory inspection or injection.
        try:
            output = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], text=True,
                errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=20)
            for row in csv.reader(output.splitlines()):
                if row and any(term in row[0].lower() for term in TERMS):
                    self.add("Process name", "Review", row[0],
                        "Broad keyword match only; not proof of cheating.")
        except Exception as exc:
            self.emit(f"Could not read process list: {exc}")

        def on_walk_error(_error):
            self.skipped += 1

        for root in roots:
            if self.cancel:
                break
            self.emit(f"Starting drive {root} ...")
            directory_count = 0
            for current, dirs, names in os.walk(root, topdown=True, followlinks=False, onerror=on_walk_error):
                if self.cancel:
                    break
                directory_count += 1
                # Send directory-level progress too: some folders take time to enumerate
                # before 250 files have been processed.
                if directory_count == 1 or directory_count % 20 == 0:
                    self.emit(f"Scanning {root} | {self.files_scanned:,} files checked | "
                              f"{directory_count:,} folders visited | {self.skipped:,} inaccessible skipped")
                # Avoid filesystem bookkeeping folders; Windows and installed-app folders
                # remain in scope when the current account has read permission.
                dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
                for name in names:
                    if self.cancel:
                        break
                    path = Path(current) / name
                    try:
                        if path.is_symlink() or not path.is_file():
                            continue
                        self.files_scanned += 1
                        if any(term in path.name.lower() for term in TERMS):
                            self.add("Filename", "Review", str(path),
                                "Broad keyword match only; legitimate files may use similar names.")
                        if hashes and path.stat().st_size <= 200 * 1024 * 1024:
                            h = hashlib.sha256()
                            with path.open("rb") as f:
                                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                                    if self.cancel:
                                        break
                                    h.update(chunk)
                            if not self.cancel and h.hexdigest().lower() in hashes:
                                self.add("SHA-256 match", "High-confidence indicator", str(path),
                                    "Matches a locally configured hash; independently verify the signature.")
                    except (OSError, PermissionError):
                        self.skipped += 1
                    if self.files_scanned % 250 == 0:
                        self.emit(f"Scanned {self.files_scanned:,} files; {self.skipped:,} inaccessible items skipped...")
        return self.findings

    def add(self, kind, level, location, reason):
        self.findings.append({"type": kind, "severity": level, "location": location, "reason": reason})

class App:
    def __init__(self, root):
        self.root, self.events = root, queue.Queue()
        self.drives = get_fixed_drives()
        self.root.title(APP); self.root.geometry("980x660"); self.root.minsize(800, 540)
        self.root.configure(bg=BG); self.build(); self.root.after(100, self.poll)

    def build(self):
        style = ttk.Style(); style.theme_use("clam")
        style.configure("Treeview", background=PANEL, foreground=FG, fieldbackground=PANEL, rowheight=26)
        style.configure("Treeview.Heading", background="#202d40", foreground=FG)
        top = tk.Frame(self.root, bg=BG, padx=24, pady=18); top.pack(fill="x")
        tk.Label(top, text="ARK CHEAT DETECTOR", bg=BG, fg=FG, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(top, text="MICROSOFT STORE / XBOX EDITION • READ-ONLY WHOLE-PC SCAN",
            bg=BG, fg=BLUE, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        body = tk.Frame(self.root, bg=BG, padx=24); body.pack(fill="both", expand=True)
        card = tk.Frame(body, bg=PANEL, padx=14, pady=12); card.pack(fill="x", pady=(0,12))
        tk.Label(card, text="Whole-PC scan scope", bg=PANEL, fg=FG, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.paths = tk.Label(card,
            text=("Fixed drives: " + ", ".join(str(p) for p in self.drives)) if self.drives else "No fixed drives detected",
            bg=PANEL, fg=MUTED, anchor="w", justify="left", wraplength=850)
        self.paths.pack(fill="x", pady=6)
        tk.Label(card, text="All detected fixed drives are included automatically. Windows-protected locations may be skipped if access is denied.",
            bg=PANEL, fg=MUTED, anchor="w", justify="left", wraplength=850).pack(fill="x")
        row2 = tk.Frame(body, bg=BG); row2.pack(fill="x", pady=(0,12))
        self.start = self.btn(row2, "START WHOLE-PC SCAN", self.scan); self.start.pack(side="left")
        self.stop = self.btn(row2, "Cancel", self.cancel, True, "disabled"); self.stop.pack(side="left", padx=8)
        self.bar = ttk.Progressbar(row2, mode="indeterminate"); self.bar.pack(side="left", fill="x", expand=True)
        card2 = tk.Frame(body, bg=PANEL, padx=12, pady=10); card2.pack(fill="both", expand=True)
        tk.Label(card2, text="Scan findings", bg=PANEL, fg=FG, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.table = ttk.Treeview(card2, columns=("level","kind","location"), show="headings")
        for c, title, width in [("level","Assessment",170),("kind","Finding",160),("location","File / process",520)]:
            self.table.heading(c, text=title); self.table.column(c, width=width)
        self.table.pack(fill="both", expand=True, pady=8)
        self.table.tag_configure("review", foreground="#ffbf69")
        self.table.tag_configure("high", foreground="#ff6b6b")
        foot = tk.Frame(body, bg=BG); foot.pack(fill="x", pady=8)
        self.status = tk.Label(foot, text="Ready. Whole-PC scan not started.", bg=BG, fg=MUTED); self.status.pack(side="left")
        self.btn(foot, "Export JSON report", self.export, True).pack(side="right")

    def btn(self, parent, label, command, secondary=False, state="normal"):
        return tk.Button(parent, text=label, command=command, state=state,
            bg="#202d40" if secondary else BLUE, fg=FG if secondary else "#071421",
            relief="flat", padx=14, pady=8, font=("Segoe UI",9,"bold"), cursor="hand2")

    def scan(self):
        if not self.drives:
            messagebox.showwarning("No drives", "No fixed drives were detected."); return
        scope = ", ".join(str(p) for p in self.drives)
        if not messagebox.askyesno("Approve whole-PC scan",
            f"This will recursively inspect accessible files on every detected fixed drive: {scope}\\n\\n"
            "It may take a long time and use substantial disk activity. Some protected Windows or app files "
            "will be skipped. It reads filenames and hashes (files up to 200 MiB) and visible process names. "
            "It does not modify, delete, upload, or execute files. Continue?"):
            return
        for item in self.table.get_children(): self.table.delete(item)
        self.start.config(state="disabled"); self.stop.config(state="normal")
        self.bar.start(12); self.status.config(text="Scanning all detected fixed drives...")
        self.scanner = Scanner(lambda msg: self.events.put(("status", msg)))
        self.scan_roots = [str(p) for p in self.drives]
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            findings = self.scanner.run(self.drives)
            report = {"application": APP, "created_unix": int(time.time()),
                "scan_scope": self.scan_roots, "files_scanned": self.scanner.files_scanned,
                "inaccessible_items_skipped": self.scanner.skipped, "findings": findings,
                "cancelled": self.scanner.cancel,
                "disclaimer": "Indicators are not proof. Access-denied locations are skipped. No findings do not guarantee a clean PC."}
            self.events.put(("done", report))
        except Exception as exc:
            self.events.put(("error", f"{type(exc).__name__}: {exc}"))

    def cancel(self):
        if hasattr(self, "scanner"): self.scanner.cancel = True
        self.status.config(text="Cancelling scan...")

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "status":
                    self.status.config(text=event[1])
                elif event[0] == "error":
                    self.bar.stop()
                    self.start.config(state="normal"); self.stop.config(state="disabled")
                    self.status.config(text="Scan stopped because of an error.")
                    messagebox.showerror("Scan error", "The scan could not finish:\\n\\n" + event[1])
                else:
                    self.report = event[1]; self.bar.stop()
                    self.start.config(state="normal"); self.stop.config(state="disabled")
                    for f in self.report["findings"]:
                        tag = "high" if f["severity"].startswith("High") else "review"
                        self.table.insert("", "end", values=(f["severity"],f["type"],f["location"]), tags=(tag,))
                    self.status.config(text=f"Finished: {self.report['files_scanned']:,} files scanned; "
                        f"{self.report['inaccessible_items_skipped']:,} inaccessible items skipped; "
                        f"{len(self.report['findings'])} finding(s).")
                    self.export(silent=True)
                    messagebox.showinfo("Scan complete",
                        "Findings are indicators, not proof. Some protected locations may have been skipped.")
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def export(self, silent=False):
        if not hasattr(self, "report"):
            if not silent: messagebox.showinfo("No report", "Run a scan first.")
            return
        out = Path.home() / "Documents" / "ARK-Cheat-Detector-Reports"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"scan-report-{int(time.time())}.json"
        path.write_text(json.dumps(self.report, indent=2), encoding="utf-8")
        if not silent: messagebox.showinfo("Report saved", str(path))

if __name__ == "__main__":
    root = tk.Tk(); App(root); root.mainloop()

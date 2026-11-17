from __future__ import annotations
import csv, hashlib, json, os, queue, re, subprocess, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP = "ARK Cheat Detector"
ROOT = Path(__file__).resolve().parent.parent
SIG_FILE = ROOT / "data" / "signatures.json"
# Broad indicator categories based on public ARK anti-cheat discussions.
# These are keyword heuristics only; ordinary tools can match them.
PATTERNS = {
    "Aim assistance": re.compile(r"\b(?:aimbot|aim[-_ ]?bot|triggerbot|trigger[-_ ]?bot)\b", re.I),
    "ESP / wall information": re.compile(r"\b(?:esp|wallhack|wall[-_ ]?hack|radar)\b", re.I),
    "Movement or weapon modification": re.compile(r"\b(?:speedhack|speed[-_ ]?hack|no[-_ ]?recoil|recoil[-_ ]?control|rapidfire)\b", re.I),
    "Trainer / memory modification": re.compile(r"\b(?:trainer|memory[-_ ]?editor|cheat[-_ ]?engine)\b", re.I),
    "Code injection terminology": re.compile(r"\b(?:injector|dll[-_ ]?injector)\b", re.I),
    "Generic cheat label": re.compile(r"\b(?:cheat|ark[-_ ]?hack)\b", re.I),
}
def matched_category(value):
    for category, pattern in PATTERNS.items():
        if pattern.search(value):
            return category
    return None
BG, PANEL, FG, MUTED, BLUE = "#10151f", "#192333", "#e8eef7", "#9aabc0", "#39a7ff"

class Scanner:
    def __init__(self, emit):
        self.emit, self.cancel = emit, False
        self.findings = []

    def run(self, folders):
        try:
            db = json.loads(SIG_FILE.read_text(encoding="utf-8"))
            hashes = {h.lower() for h in db.get("sha256", [])}
        except Exception:
            hashes = set()
            self.emit("Signature database unavailable; continuing with filename checks.")
        # Process names only; no process memory inspection or injection.
        try:
            output = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], text=True,
                errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=20)
            for row in csv.reader(output.splitlines()):
                if row and any(term in row[0].lower() for term in TERMS):
                    self.add("Process name", "Review", row[0],
                        "Broad keyword match only; not proof of cheating.")
        except Exception as exc:
            self.emit(f"Could not read process list: {exc}")
        paths = []
        for folder in folders:
            for current, dirs, names in os.walk(folder):
                dirs[:] = [d for d in dirs if d.lower() not in
                    {"windows", "$recycle.bin", "system volume information"}]
                paths.extend(Path(current) / n for n in names)
        total = max(1, len(paths))
        for i, path in enumerate(paths, 1):
            if self.cancel: break
            try:
                if path.is_symlink() or not path.is_file(): continue
                if any(term in path.name.lower() for term in TERMS):
                    self.add("Filename", "Review", str(path),
                        "Broad keyword match only; legitimate files may use similar names.")
                if path.stat().st_size <= 200 * 1024 * 1024 and hashes:
                    h = hashlib.sha256()
                    with path.open("rb") as f:
                        for chunk in iter(lambda: f.read(1024 * 1024), b""):
                            if self.cancel: break
                            h.update(chunk)
                    if not self.cancel and h.hexdigest().lower() in hashes:
                        self.add("SHA-256 match", "High-confidence indicator", str(path),
                            "Matches a locally configured hash; independently verify the signature.")
            except (OSError, PermissionError):
                pass
            if i % 25 == 0 or i == len(paths):
                self.emit(f"Scanned {i}/{len(paths)} files...")
        return self.findings

    def add(self, kind, level, location, reason):
        self.findings.append({"type": kind, "severity": level, "location": location, "reason": reason})

class App:
    def __init__(self, root):
        self.root, self.folders, self.events = root, [], queue.Queue()
        self.root.title(APP); self.root.geometry("980x660"); self.root.minsize(800, 540)
        self.root.configure(bg=BG); self.build(); self.root.after(100, self.poll)

    def build(self):
        style = ttk.Style(); style.theme_use("clam")
        style.configure("Treeview", background=PANEL, foreground=FG, fieldbackground=PANEL, rowheight=26)
        style.configure("Treeview.Heading", background="#202d40", foreground=FG)
        top = tk.Frame(self.root, bg=BG, padx=24, pady=18); top.pack(fill="x")
        tk.Label(top, text="ARK CHEAT DETECTOR", bg=BG, fg=FG, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(top, text="MICROSOFT STORE / XBOX EDITION • READ-ONLY LOCAL SCANNER",
            bg=BG, fg=BLUE, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        body = tk.Frame(self.root, bg=BG, padx=24); body.pack(fill="both", expand=True)
        card = tk.Frame(body, bg=PANEL, padx=14, pady=12); card.pack(fill="x", pady=(0,12))
        tk.Label(card, text="Scan locations", bg=PANEL, fg=FG, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.paths = tk.Label(card, text="No folders selected", bg=PANEL, fg=MUTED, anchor="w")
        self.paths.pack(fill="x", pady=6)
        row = tk.Frame(card, bg=PANEL); row.pack(fill="x")
        self.btn(row, "Add folder", self.add).pack(side="left")
        self.btn(row, "Clear", self.clear, True).pack(side="left", padx=6)
        row2 = tk.Frame(body, bg=BG); row2.pack(fill="x", pady=(0,12))
        self.start = self.btn(row2, "START FULL SCAN", self.scan); self.start.pack(side="left")
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
        self.status = tk.Label(foot, text="Ready. No files scanned.", bg=BG, fg=MUTED); self.status.pack(side="left")
        self.btn(foot, "Export JSON report", self.export, True).pack(side="right")

    def btn(self, parent, label, command, secondary=False, state="normal"):
        return tk.Button(parent, text=label, command=command, state=state,
            bg="#202d40" if secondary else BLUE, fg=FG if secondary else "#071421",
            relief="flat", padx=14, pady=8, font=("Segoe UI",9,"bold"), cursor="hand2")

    def add(self):
        p = filedialog.askdirectory(title="Choose a folder to scan")
        if p and p not in self.folders: self.folders.append(p); self.refresh_paths()

    def clear(self):
        self.folders.clear(); self.refresh_paths()

    def refresh_paths(self):
        self.paths.config(text="; ".join(self.folders) if self.folders else "No folders selected")

    def scan(self):
        if not self.folders:
            messagebox.showwarning("Choose folders", "Add at least one folder first."); return
        if not messagebox.askyesno("Approve scan",
            "This scan reads filenames and hashes in the selected folders and checks visible process names. "
            "It does not modify, delete, upload, or execute files. Continue?"): return
        for item in self.table.get_children(): self.table.delete(item)
        self.start.config(state="disabled"); self.stop.config(state="normal")
        self.bar.start(12); self.status.config(text="Scanning selected folders...")
        self.scanner = Scanner(lambda msg: self.events.put(("status", msg)))
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        findings = self.scanner.run(list(self.folders))
        report = {"application": APP, "created_unix": int(time.time()),
            "scan_scope": self.folders, "findings": findings,
            "cancelled": self.scanner.cancel,
            "disclaimer": "Indicators are not proof. No findings do not guarantee a clean PC."}
        self.events.put(("done", report))

    def cancel(self):
        if hasattr(self, "scanner"): self.scanner.cancel = True
        self.status.config(text="Cancelling...")

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "status": self.status.config(text=event[1])
                else:
                    self.report = event[1]; self.bar.stop()
                    self.start.config(state="normal"); self.stop.config(state="disabled")
                    for f in self.report["findings"]:
                        tag = "high" if f["severity"].startswith("High") else "review"
                        self.table.insert("", "end", values=(f["severity"],f["type"],f["location"]), tags=(tag,))
                    self.status.config(text=f"Finished: {len(self.report['findings'])} item(s) for review.")
                    self.export(silent=True)
                    messagebox.showinfo("Scan complete", "Findings are indicators, not proof of cheating.")
        except queue.Empty: pass
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

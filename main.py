"""ForensiX - Digital Evidence Collection and Investigation Toolkit."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from modules import database as db
from modules.evidence_collection import collect_folder
from modules.duplicate_detector import find_duplicates
from modules.timeline_analyzer import build_timeline
from modules.integrity_checker import verify_all
from modules.custody import add_custody_event, get_custody_events
from modules.usb_forensics import get_usb_history
from modules.report_generator import generate_pdf_report

class App(tk.Tk):
    COLS = ("evidence_id", "case_id", "file_name", "size_bytes", "modified_utc", "sha256")
    def __init__(self):
        super().__init__()
        self.title("ForensiX | Digital Forensics Investigation Toolkit")
        self.geometry("1360x760")
        self.minsize(1050, 620)
        self.configure(padx=8, pady=8)
        self._build()
        self.refresh()

    def _build(self):
        header=ttk.Frame(self); header.pack(fill="x", pady=(0,8))
        ttk.Label(header,text="FORENSIX",font=("Segoe UI",20,"bold")).pack(side="left",padx=(4,18))
        ttk.Label(header,text="Digital Evidence Collection & Investigation",font=("Segoe UI",11)).pack(side="left")
        form=ttk.LabelFrame(self,text="Investigation details",padding=8); form.pack(fill="x",pady=(0,8))
        ttk.Label(form,text="Case ID").grid(row=0,column=0,sticky="w")
        self.case=ttk.Entry(form,width=18); self.case.insert(0,"CASE-001"); self.case.grid(row=0,column=1,padx=6)
        ttk.Label(form,text="Investigator").grid(row=0,column=2,sticky="w",padx=(12,0))
        self.inv=ttk.Entry(form,width=24); self.inv.insert(0,"Anushree Lad"); self.inv.grid(row=0,column=3,padx=6)
        ttk.Button(form,text="Collect Evidence",command=self.on_collect).grid(row=0,column=4,padx=8)
        ttk.Button(form,text="Refresh",command=self.refresh).grid(row=0,column=5,padx=4)

        actions=ttk.LabelFrame(self,text="Forensic tools",padding=8); actions.pack(fill="x",pady=(0,8))
        buttons=[("Verify Integrity",self.on_integrity),("Find Duplicates",self.show_duplicates),
                 ("Forensic Timeline",self.show_timeline),("Chain of Custody",self.show_custody),
                 ("USB History",self.show_usb),("Export PDF Report",self.on_report)]
        for i,(label,cmd) in enumerate(buttons): ttk.Button(actions,text=label,command=cmd).grid(row=0,column=i,padx=4,pady=2,sticky="ew")
        for i in range(len(buttons)): actions.columnconfigure(i,weight=1)

        stats=ttk.Frame(self); stats.pack(fill="x",pady=(0,6))
        self.stat_total=tk.StringVar(); self.stat_cases=tk.StringVar(); self.stat_verified=tk.StringVar(); self.stat_alerts=tk.StringVar()
        for title,var in [("Evidence items",self.stat_total),("Cases",self.stat_cases),("Verified",self.stat_verified),("Integrity alerts",self.stat_alerts)]:
            box=ttk.LabelFrame(stats,text=title,padding=7); box.pack(side="left",fill="x",expand=True,padx=3)
            ttk.Label(box,textvariable=var,font=("Segoe UI",14,"bold")).pack()

        table=ttk.LabelFrame(self,text="Evidence register — double-click a row for full details",padding=5); table.pack(fill="both",expand=True)
        self.tree=ttk.Treeview(table,columns=self.COLS,show="headings")
        headings={"evidence_id":"Evidence ID","case_id":"Case ID","file_name":"File name","size_bytes":"Size (bytes)","modified_utc":"Modified (UTC)","sha256":"SHA-256"}
        widths=(95,105,190,100,185,430)
        for c,w in zip(self.COLS,widths): self.tree.heading(c,text=headings[c]); self.tree.column(c,width=w,anchor="w")
        y=ttk.Scrollbar(table,orient="vertical",command=self.tree.yview); x=ttk.Scrollbar(table,orient="horizontal",command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        self.tree.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")
        table.rowconfigure(0,weight=1); table.columnconfigure(0,weight=1)
        self.tree.bind("<Double-1>",self.show_details)
        self.progress=ttk.Progressbar(self,mode="determinate"); self.progress.pack(fill="x",pady=(7,0))
        self.status=tk.StringVar(value="Ready. Work only with files you are authorized to examine.")
        ttk.Label(self,textvariable=self.status,padding=5).pack(fill="x")

    def _case_inv(self):
        case=self.case.get().strip(); inv=self.inv.get().strip()
        if not case or not inv: raise ValueError("Enter both Case ID and Investigator.")
        return case,inv

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        data=db.load_db(); records=data.get("records",[])
        for r in records:
            self.tree.insert("","end",iid=r["evidence_id"],values=tuple(r.get(c,"") for c in self.COLS))
        cases=len({r.get("case_id") for r in records})
        alerts=sum(1 for r in records if r.get("last_integrity_status")=="FAILED")
        verified=sum(1 for r in records if r.get("last_integrity_status")=="VERIFIED")
        self.stat_total.set(str(len(records))); self.stat_cases.set(str(cases)); self.stat_verified.set(str(verified)); self.stat_alerts.set(str(alerts))
        self.status.set(f"Loaded {len(records)} evidence item(s). Evidence copies are stored under: {db.EVIDENCE_DIR}")

    def on_collect(self):
        try: case,inv=self._case_inv()
        except ValueError as e: messagebox.showwarning("Missing details",str(e)); return
        folder=filedialog.askdirectory(title="Select a folder containing authorized test/evidence files")
        if not folder: return
        try:
            stats=collect_folder(folder,case,inv)
            self.refresh()
            messagebox.showinfo("Collection complete",f"Collected: {stats['collected']}\nFailed: {stats['failed']}\nTotal: {stats['total']}\n\nSee database/collection.log for details.")
        except Exception as e: messagebox.showerror("Collection error",str(e))

    def show_details(self,_event=None):
        selected=self.tree.focus()
        rec=next((r for r in db.load_db().get("records",[]) if r.get("evidence_id")==selected),None)
        if rec: self._text_window(f"Evidence details — {selected}",json_text(rec))

    def _text_window(self,title,content):
        win=tk.Toplevel(self); win.title(title); win.geometry("1000x560")
        frame=ttk.Frame(win,padding=8); frame.pack(fill="both",expand=True)
        text=tk.Text(frame,wrap="none",font=("Consolas",10)); sy=ttk.Scrollbar(frame,command=text.yview); sx=ttk.Scrollbar(frame,orient="horizontal",command=text.xview)
        text.configure(yscrollcommand=sy.set,xscrollcommand=sx.set); text.insert("1.0",content); text.configure(state="disabled")
        text.grid(row=0,column=0,sticky="nsew"); sy.grid(row=0,column=1,sticky="ns"); sx.grid(row=1,column=0,sticky="ew")
        frame.rowconfigure(0,weight=1); frame.columnconfigure(0,weight=1)

    def on_integrity(self):
        results=verify_all(self.case.get().strip() or None)
        self.refresh()
        if not results: messagebox.showinfo("Integrity check","No collected evidence records found."); return
        ok=sum(x["status"]=="VERIFIED" for x in results); bad=len(results)-ok
        self._text_window("Evidence integrity verification", "\n".join(f"{x['evidence_id']} | {x['file_name']} | {x['status']} | {x.get('detail','')}" for x in results)+f"\n\nVerified: {ok}   Failed/Missing: {bad}")

    def show_duplicates(self):
        groups=find_duplicates(self.case.get().strip() or None)
        lines=[]
        for group in groups:
            lines.append(f"SHA-256: {group['sha256']}\nCopies: {len(group['items'])}")
            lines.extend(f"  {r['evidence_id']} | {r['file_name']} | {r.get('evidence_copy','')}" for r in group['items']); lines.append("")
        self._text_window("Duplicate evidence detection", "\n".join(lines) if lines else "No duplicate content found in the selected case.")

    def show_timeline(self):
        events=build_timeline(self.case.get().strip() or None)
        lines=[f"{e['timestamp']} | {e['event']} | {e['evidence_id']} | {e['file_name']} | {e.get('path','')}" for e in events]
        self._text_window("Forensic timeline", "\n".join(lines) if lines else "No timeline events found.")

    def show_custody(self):
        records=db.load_db().get("records",[]); case=self.case.get().strip()
        win=tk.Toplevel(self); win.title("Chain of Custody"); win.geometry("850x520")
        form=ttk.Frame(win,padding=8); form.pack(fill="x")
        ttk.Label(form,text="Evidence ID").grid(row=0,column=0); evid=ttk.Entry(form,width=16); evid.grid(row=0,column=1,padx=5)
        ttk.Label(form,text="Action").grid(row=0,column=2); action=ttk.Combobox(form,values=["TRANSFERRED","EXAMINED","SEALED","RELEASED","NOTE"],state="readonly",width=14); action.set("EXAMINED"); action.grid(row=0,column=3,padx=5)
        ttk.Label(form,text="Handled by").grid(row=1,column=0,pady=5); person=ttk.Entry(form,width=22); person.insert(0,self.inv.get().strip()); person.grid(row=1,column=1,padx=5)
        ttk.Label(form,text="Details / recipient").grid(row=1,column=2); details=ttk.Entry(form,width=35); details.grid(row=1,column=3,padx=5)
        cols=("time","evidence_id","action","person","details"); tree=ttk.Treeview(win,columns=cols,show="headings")
        for c,w in zip(cols,(180,100,110,160,280)): tree.heading(c,text=c.replace("_"," ").title()); tree.column(c,width=w)
        tree.pack(fill="both",expand=True,padx=8,pady=8)
        def reload_events():
            tree.delete(*tree.get_children())
            for e in get_custody_events(case or None): tree.insert("","end",values=(e.get("timestamp_utc"),e.get("evidence_id"),e.get("action"),e.get("person"),e.get("details")))
        def add():
            try: add_custody_event(evid.get().strip(),case,person.get().strip(),action.get(),details.get().strip())
            except Exception as ex: messagebox.showerror("Custody entry",str(ex),parent=win); return
            reload_events(); messagebox.showinfo("Saved","Chain-of-custody event recorded.",parent=win)
        ttk.Button(form,text="Add custody event",command=add).grid(row=2,column=3,sticky="e",pady=6)
        reload_events()

    def show_usb(self):
        items=get_usb_history()
        if isinstance(items,str): self._text_window("USB device history",items); return
        self._text_window("USB device history", "\n".join(f"{x['key']} | {x.get('device_name','')} | {x.get('last_write_time','')}" for x in items) or "No USB history entries found.")

    def on_report(self):
        try: case,inv=self._case_inv()
        except ValueError as e: messagebox.showwarning("Missing details",str(e)); return
        path=generate_pdf_report(case,inv)
        if path: messagebox.showinfo("Report generated",f"PDF report saved to:\n{path}")
        else: messagebox.showerror("Missing dependency","Install reportlab using: python -m pip install -r requirements.txt")


def json_text(obj):
    import json
    return json.dumps(obj,indent=2,ensure_ascii=False)

if __name__ == "__main__": App().mainloop()

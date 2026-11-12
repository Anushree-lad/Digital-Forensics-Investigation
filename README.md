# ForensiX — Digital Forensics Investigation Toolkit

A Windows-friendly Python desktop application for authorized digital-evidence acquisition, file metadata review, SHA-256/MD5 hashing, integrity re-verification, duplicate-content detection, basic filesystem timeline generation, chain-of-custody event logging, basic Windows USB registry enumeration, and case PDF reporting.

## Run
1. Extract this folder.
2. Open it in VS Code.
3. In the terminal, run `python -m venv .venv` then activate it: PowerShell ` .venv\Scripts\Activate.ps1`.
4. Install PDF dependency: `python -m pip install -r requirements.txt`.
5. Run `python main.py`.

Tkinter is included with most standard Windows Python installations. If the `tkinter` module is missing, repair/reinstall Python with Tcl/Tk support.

## Modules
- Collect Evidence: recursively copies files from a selected source folder; hashes source and copy and records only matching acquisitions.
- Verify Integrity: recalculates current SHA-256 hashes of evidence copies and compares with acquisition-time hashes.
- Find Duplicates: groups currently stored evidence copies by matching SHA-256.
- Forensic Timeline: displays creation, modification, access and collection timestamps in UTC.
- Chain of Custody: records handler, action, timestamp and details for a known evidence item.
- USB History: read-only enumeration of selected Windows USB registry keys (best-effort; not a complete connection history).
- PDF Report: exports case evidence, integrity status, timeline and duplicate groups.

## Data locations
- `evidence/`: acquired copies.
- `database/evidence.json`: evidence register.
- `database/chain_of_custody.json`: custody event history.
- `database/collection.log`: application activity log.
- `reports/`: generated PDF reports.

## Forensic limitations and safe use
- Use only on systems and data you own or are explicitly authorized to examine.
- Work from forensic images/copies when possible; this tool is not a write-blocker and does not create a bit-for-bit disk image.
- The source folder is read, not modified intentionally, but normal OS access may update access times depending on filesystem settings.
- Filesystem timestamps may be changed, rounded, or interpreted differently across filesystems and are leads, not proof of an event.
- Windows USB enumeration keys are not a full USB event log; some registry details may require elevated read permissions.
- JSON custody records are application logs, not tamper-proof or cryptographically signed records. Protect and independently preserve the database/log files for real investigations.
- MD5 is shown for legacy identification only. SHA-256 is the primary integrity digest.
- This is an educational investigation aid, not a certified forensic suite. Validate results independently before relying on them.

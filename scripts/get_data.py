"""Download and separate Tableau Sample Superstore dataset into clean tables.

Splits multi-sheet concatenated CSV into:
- data/raw/raw_orders.csv (9,994 line items)
- data/raw/raw_people.csv (Regional managers)
- data/raw/raw_returns.csv (Returned orders)
"""
import subprocess
from pathlib import Path

URL = "https://raw.githubusercontent.com/leonism/sample-superstore/master/data/superstore.csv"

raw_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)
combined_csv = raw_dir / "superstore_combined.csv"

if not combined_csv.exists() or combined_csv.stat().st_size < 1000:
    print("Downloading raw Superstore CSV via curl...")
    subprocess.run(["curl.exe", "-L", URL, "-o", str(combined_csv)], check=True)

lines = combined_csv.read_text(encoding="latin1").splitlines()

# Locate boundaries
people_idx = None
returns_idx = None

for i, line in enumerate(lines):
    if line.strip() == "Person,Region":
        people_idx = i
    elif line.strip() == "Returned,Order ID":
        returns_idx = i

if people_idx is None or returns_idx is None:
    raise ValueError("Could not find table delimiters in raw superstore file.")

orders_lines = lines[:people_idx]
people_lines = lines[people_idx:returns_idx]
returns_lines = lines[returns_idx:]

(raw_dir / "raw_orders.csv").write_text("\n".join(orders_lines), encoding="utf-8")
(raw_dir / "raw_people.csv").write_text("\n".join(people_lines), encoding="utf-8")
(raw_dir / "raw_returns.csv").write_text("\n".join(returns_lines), encoding="utf-8")

print(f"Extracted {len(orders_lines)-1:,} orders into raw_orders.csv")
print(f"Extracted {len(people_lines)-1:,} managers into raw_people.csv")
print(f"Extracted {len(returns_lines)-1:,} returns into raw_returns.csv")

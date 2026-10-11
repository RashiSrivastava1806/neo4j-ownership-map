import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "Data"
    / "raw"
    / "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

columns_to_check = [
    "OpenCorporates",
    "LEI",
    "PermID",
    "DUNL",
    "CapIQ",
]

with DATA_FILE.open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    reader = csv.DictReader(file)
    rows = list(reader)

print("=" * 60)
print("LINK AND IDENTIFIER FIELD CHECK")
print("=" * 60)

for column in columns_to_check:
    values = [
        (row.get(column) or "").strip()
        for row in rows
    ]

    nonempty_values = [value for value in values if value]
    empty_count = len(values) - len(nonempty_values)

    url_values = [
        value for value in nonempty_values
        if value.lower().startswith(("http://", "https://", "www."))
    ]

    print(f"\nColumn: {column}")
    print(f"Non-empty values: {len(nonempty_values)}")
    print(f"Empty values: {empty_count}")
    print(f"Values that look like URLs: {len(url_values)}")
    print("Sample non-empty values:")

    for value in nonempty_values[:3]:
        print(f"  {value}")

print("\nNo data was modified.")
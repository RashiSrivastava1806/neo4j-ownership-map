
import csv
from collections import defaultdict, Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "Data"
    / "raw"
    / "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

def normalize_name(value):
    return " ".join((value or "").upper().split())

groups = defaultdict(list)

with DATA_FILE.open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        name = (row.get("Subsidiary Name (Clean)") or "").strip()

        if name:
            groups[normalize_name(name)].append(row)

duplicate_groups = {
    name: records
    for name, records in groups.items()
    if len(records) > 1
}

print("=" * 65)
print("DUPLICATE ENTITY INVESTIGATION")
print("=" * 65)
print(f"Duplicate name groups: {len(duplicate_groups)}")

same_identifier_groups = 0
different_identifier_groups = 0
missing_identifier_groups = 0

for records in duplicate_groups.values():
    identifiers = [
        (row.get("Business ID") or "").strip()
        for row in records
    ]

    nonempty = [identifier for identifier in identifiers if identifier]

    if len(nonempty) != len(identifiers):
        missing_identifier_groups += 1
    elif len(set(nonempty)) == 1:
        same_identifier_groups += 1
    else:
        different_identifier_groups += 1

print(f"Groups with at least one missing Business ID: {missing_identifier_groups}")
print(f"Groups with identical Business IDs throughout: {same_identifier_groups}")
print(f"Groups with different Business IDs: {different_identifier_groups}")

print("\nFIRST 20 DUPLICATE NAME GROUPS")
print("-" * 65)

for name, records in list(duplicate_groups.items())[:20]:
    print(f"\nNormalized name: {name}")
    print(f"Number of records: {len(records)}")

    for index, row in enumerate(records, start=1):
        print(f"  Record {index}:")
        print(f"    Entity: {row.get('Subsidiary Name (Clean', '')}")
        print(f"    Business ID: {row.get('Business ID', '')}")
        print(f"    OpenCorporates: {row.get('OpenCorporates', '')}")
        print(f"    LEI: {row.get('LEI', '')}")
        print(f"    ISO3: {row.get('ISO3', '')}")
        print(f"    Hierarchy: {row.get('Hierarchy', '')}")
        print(f"    Parent MNE: {row.get('Parent MNE', '')}")
        print(f"    Direct parent: {row.get('Parent of Subsidiary', '')}")

print("\nInvestigation complete. No data was modified.")

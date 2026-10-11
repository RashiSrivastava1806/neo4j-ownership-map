
import csv
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "Data"
    / "raw"
    / "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

stats = defaultdict(Counter)
examples = defaultdict(list)

with DATA_FILE.open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        hierarchy = (
            row.get("Hierarchy") or ""
        ).strip() or "[BLANK]"

        entity = (
            row.get("Subsidiary Name (Clean)") or ""
        ).strip()

        parent_mne = (
            row.get("Parent MNE") or ""
        ).strip()

        direct_parent = (
            row.get("Parent of Subsidiary") or ""
        ).strip()

        stats[hierarchy]["total"] += 1

        if direct_parent:
            stats[hierarchy]["has_parent"] += 1
        else:
            stats[hierarchy]["no_parent"] += 1

        if entity and direct_parent and entity == direct_parent:
            stats[hierarchy]["self_parent_name"] += 1

        if len(examples[hierarchy]) < 5:
            examples[hierarchy].append({
                "entity": entity,
                "parent": direct_parent or "[EMPTY]",
                "parent_mne": parent_mne,
            })

print("=" * 65)
print("HIERARCHY AND PARENT RELATIONSHIP ANALYSIS")
print("=" * 65)

for hierarchy, counts in sorted(stats.items()):
    print(f"\nHierarchy: {hierarchy}")
    print(f"Total records: {counts['total']}")
    print(f"Records with direct parent: {counts['has_parent']}")
    print(f"Records without direct parent: {counts['no_parent']}")
    print(f"Same entity/parent name: {counts['self_parent_name']}")

    print("Examples:")
    for item in examples[hierarchy]:
        print(f"  Entity: {item['entity']}")
        print(f"  Direct parent: {item['parent']}")
        print(f"  Parent MNE: {item['parent_mne']}")
        print()

print("\nAnalysis complete. No data was modified.")


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

def normalize_name(value):
    """Conservative normalization for name matching."""
    return " ".join((value or "").upper().split())

with DATA_FILE.open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    rows = list(csv.DictReader(file))

entity_counts = Counter()
entity_display_names = defaultdict(list)
parent_counts = Counter()
parent_display_names = defaultdict(list)

for row in rows:
    entity = (row.get("Subsidiary Name (Clean)") or "").strip()
    parent = (row.get("Parent of Subsidiary") or "").strip()

    if entity:
        key = normalize_name(entity)
        entity_counts[key] += 1

        if entity not in entity_display_names[key]:
            entity_display_names[key].append(entity)

    if parent:
        key = normalize_name(parent)
        parent_counts[key] += 1

        if parent not in parent_display_names[key]:
            parent_display_names[key].append(parent)

matched_parent_records = 0
unmatched_parent_records = 0
ambiguous_parent_records = 0
self_parent_records = 0
unmatched_examples = []
ambiguous_examples = []
self_parent_examples = []

for row in rows:
    entity = (row.get("Subsidiary Name (Clean)") or "").strip()
    parent = (row.get("Parent of Subsidiary") or "").strip()

    if not parent:
        continue

    entity_key = normalize_name(entity)
    parent_key = normalize_name(parent)
    matches = entity_counts[parent_key]

    if matches == 0:
        unmatched_parent_records += 1

        if len(unmatched_examples) < 20:
            unmatched_examples.append((parent, entity))
    elif matches == 1:
        matched_parent_records += 1
    else:
        ambiguous_parent_records += 1

        if len(ambiguous_examples) < 20:
            ambiguous_examples.append(
                (parent, entity, matches)
            )

    if entity_key and entity_key == parent_key:
        self_parent_records += 1

        if len(self_parent_examples) < 10:
            self_parent_examples.append((entity, parent))

duplicate_entity_names = {
    name: count
    for name, count in entity_counts.items()
    if count > 1
}

print("=" * 65)
print("PARENT-NAME VALIDATION")
print("=" * 65)
print(f"Total source records: {len(rows)}")
print(f"Records with a direct parent: {sum(parent_counts.values())}")
print(f"Parent records matching one entity name: {matched_parent_records}")
print(f"Parent records with no entity-name match: {unmatched_parent_records}")
print(f"Parent records matching multiple entity records: {ambiguous_parent_records}")
print(f"Potential self-parent records: {self_parent_records}")
print(f"Distinct normalized entity names: {len(entity_counts)}")
print(f"Entity names appearing more than once: {len(duplicate_entity_names)}")

print("\nUNMATCHED PARENT EXAMPLES")
for parent, entity in unmatched_examples:
    print(f"  Parent: {parent} | Child: {entity}")

print("\nAMBIGUOUS PARENT EXAMPLES")
for parent, entity, count in ambiguous_examples:
    print(
        f"  Parent: {parent} | Child: {entity} "
        f"| Matching entity records: {count}"
    )

print("\nPOTENTIAL SELF-PARENT EXAMPLES")
for entity, parent in self_parent_examples:
    print(f"  Entity: {entity} | Parent: {parent}")

print("\nVALIDATION COMPLETE. No data was modified.")

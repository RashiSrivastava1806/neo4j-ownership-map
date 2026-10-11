
import csv
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path.cwd()

INPUT_FILE = (
    ROOT / "Data" / "raw" /
    "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

OUTPUT_DIR = ROOT / "Data" / "processed"
AUDIT_FILE = OUTPUT_DIR / "direct_parent_relationship_audit.csv"
SUMMARY_FILE = OUTPUT_DIR / "direct_parent_relationship_summary.txt"

ENTITY_COL = "Subsidiary Name (Clean)"
PARENT_COL = "Parent of Subsidiary"


def normalize(value):
    """Normalize text for name comparison only."""
    return " ".join((value or "").strip().casefold().split())


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}\n"
            "Run this script from the repository root."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    name_to_rows = defaultdict(list)

    with INPUT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV has no header.")

        for row_number, row in enumerate(reader, start=2):
            row["_source_row"] = str(row_number)
            records.append(row)

            entity_key = normalize(row.get(ENTITY_COL, ""))

            if entity_key:
                name_to_rows[entity_key].append(row_number)

    status_counts = Counter()
    records_with_parent = 0
    audit_rows = []

    for row in records:
        child_name = row.get(ENTITY_COL, "").strip()
        parent_name = row.get(PARENT_COL, "").strip()

        if not parent_name:
            continue

        records_with_parent += 1

        child_key = normalize(child_name)
        parent_key = normalize(parent_name)
        matching_rows = name_to_rows.get(parent_key, [])

        if child_key and child_key == parent_key:
            status = "POTENTIAL_SELF_PARENT"

        elif len(matching_rows) == 0:
            status = "PARENT_NOT_FOUND"

        elif len(matching_rows) == 1:
            status = "UNIQUE_NAME_MATCH"

        else:
            status = "AMBIGUOUS_PARENT_NAME"

        status_counts[status] += 1

        audit_rows.append({
            "Source_Row_Number": row["_source_row"],
            "Child_Name": child_name,
            "Direct_Parent_Name": parent_name,
            "Matching_Parent_Record_Count": len(matching_rows),
            "Matching_Parent_Source_Rows": ";".join(
                str(number) for number in matching_rows
            ),
            "Match_Status": status,
        })

    columns = [
        "Source_Row_Number",
        "Child_Name",
        "Direct_Parent_Name",
        "Matching_Parent_Record_Count",
        "Matching_Parent_Source_Rows",
        "Match_Status",
    ]

    with AUDIT_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(audit_rows)

    with SUMMARY_FILE.open("w", encoding="utf-8") as file:
        file.write("DIRECT-PARENT RELATIONSHIP AUDIT\n")
        file.write("=" * 40 + "\n\n")
        file.write(f"Total source records: {len(records)}\n")
        file.write(
            f"Records with a direct-parent value: "
            f"{records_with_parent}\n\n"
        )
        file.write("CLASSIFICATION COUNTS\n")
        file.write("-" * 40 + "\n")

        for status, count in sorted(status_counts.items()):
            file.write(f"{status}: {count}\n")

        file.write("\nINTERPRETATION\n")
        file.write(
            "UNIQUE_NAME_MATCH means the parent name matches one "
            "source record, not that ownership is independently "
            "verified.\n"
        )
        file.write(
            "AMBIGUOUS_PARENT_NAME means multiple records match "
            "the parent name and require identity resolution.\n"
        )
        file.write(
            "No ownership edges were created and no source data "
            "was modified.\n"
        )

    print("Direct-parent audit completed.")
    print(f"Total source records: {len(records)}")
    print(f"Records with direct-parent values: {records_with_parent}")
    print("\nClassification counts:")

    for status, count in sorted(status_counts.items()):
        print(f"{status}: {count}")

    print(f"\nAudit CSV: {AUDIT_FILE}")
    print(f"Summary: {SUMMARY_FILE}")
    print("Original dataset was not modified.")


if __name__ == "__main__":
    main()

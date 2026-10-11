
import csv
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path.cwd()

INPUT_FILE = (
    ROOT / "Data" / "raw" /
    "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

OUTPUT_DIR = ROOT / "Data" / "processed"

REVIEW_FILE = OUTPUT_DIR / "entity_resolution_review.csv"
SUMMARY_FILE = OUTPUT_DIR / "entity_resolution_summary.txt"

NAME_COL = "Subsidiary Name (Clean)"
COUNTRY_COL = "ISO3"
BUSINESS_ID_COL = "Business ID"
LEI_COL = "LEI"
OPENCORPORATES_COL = "OpenCorporates"
PARENT_MNE_COL = "Parent MNE"
DIRECT_PARENT_COL = "Parent of Subsidiary"

IDENTIFIER_COLS = [
    BUSINESS_ID_COL,
    LEI_COL,
    OPENCORPORATES_COL,
]


def normalize(value):
    """Normalize text for comparison without modifying source values."""
    return " ".join((value or "").strip().casefold().split())


def get_nonempty_values(records, column):
    """Return distinct non-empty values for a field."""
    return {
        record[column].strip()
        for record in records
        if record.get(column, "").strip()
    }


def classify_group(records):
    """
    Classify a duplicate-name group for human review.
    This function never merges records automatically.
    """
    conflicts = []

    for column in IDENTIFIER_COLS:
        values = get_nonempty_values(records, column)

        if len(values) > 1:
            conflicts.append(column)

    countries = get_nonempty_values(records, COUNTRY_COL)
    parent_groups = get_nonempty_values(records, PARENT_MNE_COL)
    direct_parents = get_nonempty_values(records, DIRECT_PARENT_COL)

    if conflicts:
        return (
            "IDENTIFIER_CONFLICT_REVIEW",
            "Different non-empty values found for: "
            + ", ".join(conflicts)
            + ". Do not merge automatically."
        )

    if len(countries) > 1:
        return (
            "COUNTRY_CONFLICT_REVIEW",
            "Records have different country codes. "
            "Verify legal-entity identity before merging."
        )

    if len(parent_groups) > 1:
        return (
            "PARENT_GROUP_CONFLICT_REVIEW",
            "Records have different Parent MNE values. "
            "Investigate group association."
        )

    if len(direct_parents) > 1:
        return (
            "DIRECT_PARENT_CONFLICT_REVIEW",
            "Records have different direct-parent values. "
            "Verify the ownership relationship."
        )

    all_identifiers_missing = all(
        not record.get(column, "").strip()
        for record in records
        for column in IDENTIFIER_COLS
    )

    if all_identifiers_missing:
        return (
            "INSUFFICIENT_IDENTIFIERS",
            "No Business ID, LEI, or OpenCorporates ID is "
            "available in these records. Keep separate pending review."
        )

    return (
        "POSSIBLE_DUPLICATE_REVIEW",
        "No conflicts detected in the checked fields. "
        "Candidate for further verification, not an automatic merge."
    )


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}\n"
            "Run this script from the repository root."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    original_columns = []

    with INPUT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("The input CSV has no header.")

        original_columns = reader.fieldnames

        required = [
            NAME_COL,
            COUNTRY_COL,
            BUSINESS_ID_COL,
            LEI_COL,
            OPENCORPORATES_COL,
            PARENT_MNE_COL,
            DIRECT_PARENT_COL,
        ]

        missing = [
            column for column in required
            if column not in original_columns
        ]

        if missing:
            raise ValueError(
                f"Missing expected columns: {missing}"
            )

        for row_number, row in enumerate(reader, start=2):
            row["_source_row_number"] = str(row_number)
            records.append(row)

    # Group records by normalized entity name.
    groups = defaultdict(list)

    for record in records:
        key = normalize(record.get(NAME_COL, ""))

        if key:
            groups[key].append(record)

    duplicate_groups = {
        name: group
        for name, group in groups.items()
        if len(group) > 1
    }

    extra_columns = [
        "Source_Row_Number",
        "Normalized_Name",
        "Group_Size",
        "Review_Status",
        "Review_Reason",
    ]

    output_columns = original_columns + extra_columns

    group_status_counts = Counter()
    records_written = 0

    with REVIEW_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=output_columns,
            extrasaction="ignore",
        )
        writer.writeheader()

        for normalized_name, group in sorted(
            duplicate_groups.items()
        ):
            status, reason = classify_group(group)
            group_status_counts[status] += 1

            for record in group:
                output_record = dict(record)

                output_record["Source_Row_Number"] = (
                    record["_source_row_number"]
                )
                output_record["Normalized_Name"] = normalized_name
                output_record["Group_Size"] = len(group)
                output_record["Review_Status"] = status
                output_record["Review_Reason"] = reason

                writer.writerow(output_record)
                records_written += 1

    with SUMMARY_FILE.open(
        "w", encoding="utf-8"
    ) as file:
        file.write("ENTITY-RESOLUTION REVIEW SUMMARY\n")
        file.write("=" * 40 + "\n\n")
        file.write(f"Source records: {len(records)}\n")
        file.write(
            f"Duplicate-name groups: {len(duplicate_groups)}\n"
        )
        file.write(
            f"Records included for review: {records_written}\n\n"
        )
        file.write("GROUP COUNTS BY REVIEW STATUS\n")
        file.write("-" * 40 + "\n")

        for status, count in sorted(
            group_status_counts.items()
        ):
            file.write(f"{status}: {count}\n")

        file.write("\nIMPORTANT\n")
        file.write(
            "No source records were merged or deleted.\n"
            "Review statuses are screening signals, not proof "
            "that two records represent the same legal entity.\n"
        )

    print("Entity-resolution review completed.")
    print(f"Source records: {len(records)}")
    print(f"Duplicate-name groups: {len(duplicate_groups)}")
    print(f"Records exported for review: {records_written}")
    print(f"Review CSV: {REVIEW_FILE}")
    print(f"Summary report: {SUMMARY_FILE}")
    print("Original dataset was not modified.")


if __name__ == "__main__":
    main()

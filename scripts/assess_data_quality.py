
import csv
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "Data"
    / "raw"
    / "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

print("=" * 65)
print("DATA QUALITY ASSESSMENT")
print("=" * 65)

with DATA_FILE.open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    reader = csv.DictReader(file)

    if not reader.fieldnames:
        raise ValueError("CSV headers are missing.")

    headers = reader.fieldnames
    row_count = 0
    blank_rows = 0
    malformed_rows = 0
    missing_counts = Counter()
    exact_duplicates = 0
    seen_rows = set()
    column_value_counts = {header: Counter() for header in headers}

    for row in reader:
        row_count += 1

        # DictReader stores extra fields under the None key.
        if None in row:
            malformed_rows += 1

        values = [row.get(header) for header in headers]

        # Detect completely blank records.
        if all(
            value is None or not value.strip()
            for value in values
        ):
            blank_rows += 1
            continue

        # Count missing values and distinct values per column.
        for header in headers:
            value = row.get(header)

            if value is None or not value.strip():
                missing_counts[header] += 1
            else:
                column_value_counts[header][value.strip()] += 1

        # Detect exact duplicate rows.
        row_signature = tuple(values)

        if row_signature in seen_rows:
            exact_duplicates += 1
        else:
            seen_rows.add(row_signature)

print(f"\nTotal data rows: {row_count}")
print(f"Number of columns: {len(headers)}")
print(f"Completely blank rows: {blank_rows}")
print(f"Rows with extra fields: {malformed_rows}")
print(f"Exact duplicate rows: {exact_duplicates}")

print("\nMISSING VALUES BY COLUMN")
for header in headers:
    missing = missing_counts[header]
    percentage = (
        (missing / row_count) * 100 if row_count else 0
    )
    print(f"{header}: {missing} ({percentage:.2f}%)")

print("\nDISTINCT NON-BLANK VALUES BY COLUMN")
for header in headers:
    distinct = len(column_value_counts[header])
    print(f"{header}: {distinct}")

print("\nQUALITY ASSESSMENT COMPLETED.")
print("No source data was modified.")

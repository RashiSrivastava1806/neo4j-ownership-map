
import csv
from pathlib import Path

# Project root is the parent of the scripts folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "Data"
    / "raw"
    / "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

print("=" * 60)
print("DATASET INSPECTION")
print("=" * 60)

# 1. Verify that the file exists
if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found at: {DATA_FILE}\n"
        "Check the filename and Data/raw/ folder."
    )

print(f"\nFile: {DATA_FILE.name}")
print(f"File size: {DATA_FILE.stat().st_size:,} bytes")

# 2. Inspect the CSV structure without modifying it
with DATA_FILE.open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    reader = csv.reader(file)

    headers = next(reader, None)

    if not headers:
        raise ValueError("The CSV file is empty.")

    print(f"\nNumber of columns: {len(headers)}")
    print("\nCOLUMN HEADERS")

    for index, header in enumerate(headers, start=1):
        print(f"{index}. {header}")

    # 3. Display the first five data records
    print("\nFIRST FIVE RECORDS")

    for index, row in enumerate(reader):
        if index == 5:
            break

        print(f"\nRecord {index + 1}:")

        for header, value in zip(headers, row):
            print(f"  {header}: {value}")

print("\nInspection completed. Original CSV was not modified.")

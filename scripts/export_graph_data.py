
import csv
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path.cwd()

INPUT_FILE = (
    ROOT / "Data" / "raw" /
    "OECD_UNSD_MEIP_Global-Register_2024_Group_Register.csv"
)

OUTPUT_DIR = ROOT / "Data" / "edge_lists"

ENTITIES_FILE = OUTPUT_DIR / "entities.csv"
EDGES_FILE = OUTPUT_DIR / "candidate_edges.csv"
AMBIGUOUS_FILE = OUTPUT_DIR / "ambiguous_edges_review.csv"
SUMMARY_FILE = OUTPUT_DIR / "graph_export_summary.txt"

NAME_COL = "Subsidiary Name (Clean)"
COUNTRY_COL = "ISO3"
HIERARCHY_COL = "Hierarchy"
PARENT_MNE_COL = "Parent MNE"
DIRECT_PARENT_COL = "Parent of Subsidiary"
BUSINESS_ID_COL = "Business ID"
LEI_COL = "LEI"


def normalize(value):
    return " ".join((value or "").strip().casefold().split())


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}\n"
            "Run this script from the repository root."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    name_to_records = defaultdict(list)

    with INPUT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        required = [
            NAME_COL,
            COUNTRY_COL,
            HIERARCHY_COL,
            PARENT_MNE_COL,
            DIRECT_PARENT_COL,
            BUSINESS_ID_COL,
            LEI_COL,
        ]

        if not reader.fieldnames:
            raise ValueError("Input CSV has no header.")

        missing = [
            column for column in required
            if column not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                f"Missing expected columns: {missing}"
            )

        for row_number, row in enumerate(reader, start=2):
            # The source CSV row number is a stable identifier
            # for this particular source record in this dataset.
            row["entity_id"] = f"ENTITY_{row_number}"
            row["source_row"] = str(row_number)
            records.append(row)

            name_key = normalize(row.get(NAME_COL, ""))

            if name_key:
                name_to_records[name_key].append(row)

    # Export all source records as separate graph nodes.
    node_columns = [
        "entity_id",
        "name",
        "country",
        "hierarchy",
        "parent_mne",
        "business_id",
        "lei",
        "source_row",
    ]

    with ENTITIES_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=node_columns
        )
        writer.writeheader()

        for row in records:
            writer.writerow({
                "entity_id": row["entity_id"],
                "name": row.get(NAME_COL, "").strip(),
                "country": row.get(COUNTRY_COL, "").strip(),
                "hierarchy": row.get(HIERARCHY_COL, "").strip(),
                "parent_mne": row.get(PARENT_MNE_COL, "").strip(),
                "business_id": row.get(BUSINESS_ID_COL, "").strip(),
                "lei": row.get(LEI_COL, "").strip(),
                "source_row": row["source_row"],
            })

    edge_columns = [
        "parent_id",
        "child_id",
        "relationship",
        "match_status",
        "parent_name_from_source",
        "child_name",
        "source_row",
    ]

    ambiguous_columns = [
        "child_id",
        "child_name",
        "parent_name_from_source",
        "matching_parent_ids",
        "matching_parent_count",
        "source_row",
        "review_status",
    ]

    counts = Counter()
    candidate_edges = []
    ambiguous_edges = []

    for row in records:
        child_name = row.get(NAME_COL, "").strip()
        parent_name = row.get(DIRECT_PARENT_COL, "").strip()

        if not parent_name:
            counts["NO_DIRECT_PARENT_VALUE"] += 1
            continue

        child_key = normalize(child_name)
        parent_key = normalize(parent_name)

        matches = name_to_records.get(parent_key, [])

        if child_key and child_key == parent_key:
            counts["POTENTIAL_SELF_PARENT_EXCLUDED"] += 1
            continue

        if len(matches) == 1:
            parent_record = matches[0]

            candidate_edges.append({
                "parent_id": parent_record["entity_id"],
                "child_id": row["entity_id"],
                "relationship": "HAS_DIRECT_SUBSIDIARY",
                "match_status": "UNIQUE_NAME_MATCH",
                "parent_name_from_source": parent_name,
                "child_name": child_name,
                "source_row": row["source_row"],
            })

            counts["UNIQUE_NAME_MATCH_CANDIDATE"] += 1

        elif len(matches) > 1:
            ambiguous_edges.append({
                "child_id": row["entity_id"],
                "child_name": child_name,
                "parent_name_from_source": parent_name,
                "matching_parent_ids": ";".join(
                    match["entity_id"] for match in matches
                ),
                "matching_parent_count": len(matches),
                "source_row": row["source_row"],
                "review_status": "AMBIGUOUS_PARENT_NAME",
            })

            counts["AMBIGUOUS_PARENT_REVIEW"] += 1

        else:
            counts["PARENT_NOT_FOUND"] += 1

    with EDGES_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=edge_columns
        )
        writer.writeheader()
        writer.writerows(candidate_edges)

    with AMBIGUOUS_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=ambiguous_columns
        )
        writer.writeheader()
        writer.writerows(ambiguous_edges)

    with SUMMARY_FILE.open("w", encoding="utf-8") as file:
        file.write("GRAPH DATA EXPORT SUMMARY\n")
        file.write("=" * 40 + "\n\n")
        file.write(f"Source records: {len(records)}\n")
        file.write(f"Node records exported: {len(records)}\n")
        file.write(
            f"Candidate edges exported: {len(candidate_edges)}\n"
        )
        file.write(
            f"Ambiguous relationships for review: "
            f"{len(ambiguous_edges)}\n\n"
        )
        file.write("CLASSIFICATION COUNTS\n")
        file.write("-" * 40 + "\n")

        for status, count in sorted(counts.items()):
            file.write(f"{status}: {count}\n")

        file.write("\nLIMITATIONS\n")
        file.write(
            "Each source record is represented as a separate node. "
            "Duplicate legal entities have not been merged.\n"
        )
        file.write(
            "Candidate edges are based on a unique normalized "
            "parent-name match, not independent proof of ownership.\n"
        )
        file.write(
            "No direct-parent edges are inferred from Parent MNE.\n"
        )

    print("Graph data export completed.")
    print(f"Source records: {len(records)}")
    print(f"Node records exported: {len(records)}")
    print(f"Candidate edges exported: {len(candidate_edges)}")
    print(
        f"Ambiguous relationships for review: "
        f"{len(ambiguous_edges)}"
    )
    print(f"\nEntities: {ENTITIES_FILE}")
    print(f"Candidate edges: {EDGES_FILE}")
    print(f"Ambiguous review: {AMBIGUOUS_FILE}")
    print(f"Summary: {SUMMARY_FILE}")
    print("Original dataset was not modified.")


if __name__ == "__main__":
    main()


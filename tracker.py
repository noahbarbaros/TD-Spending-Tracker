#!/usr/bin/env python3
"""
TD Spending Tracker
Parses TD Canada EasyWeb CSV exports and generates a markdown spending report.
"""

import csv
import os
import sys
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
CATEGORIES_FILE = SCRIPT_DIR / "categories.json"
DATA_DIR = SCRIPT_DIR / "data"
OUTPUT_DIR = SCRIPT_DIR / "output"


def load_categories():
    """Load keyword -> category mappings from categories.json."""
    if CATEGORIES_FILE.exists():
        with open(CATEGORIES_FILE) as f:
            return json.load(f)
    return {}


def categorize(description, categories):
    """Match a transaction description to a spending category."""
    desc_lower = description.lower()
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword.lower() in desc_lower:
                return category
    return "Other"


# ---------------------------------------------------------------------------
# CSV Parsing
# ---------------------------------------------------------------------------

def parse_td_csv(filepath):
    """
    Parse a TD Canada EasyWeb CSV export.

    TD CSVs typically have these columns (no header row):
      date, description, debit, credit, balance
    """
    transactions = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue

            # Try to parse the date — TD uses MM/DD/YYYY
            raw_date = row[0].strip()
            try:
                date = datetime.strptime(raw_date, "%m/%d/%Y")
            except ValueError:
                # Skip header rows or malformed lines
                continue

            description = row[1].strip()
            debit = row[2].strip()
            credit = row[3].strip()
            balance = row[4].strip() if len(row) > 4 else ""

            # Determine amount and type
            if debit:
                amount = float(debit.replace(",", ""))
                txn_type = "expense"
            elif credit:
                amount = float(credit.replace(",", ""))
                txn_type = "income"
            else:
                continue

            transactions.append({
                "date": date,
                "description": description,
                "amount": amount,
                "type": txn_type,
                "balance": balance,
            })

    return transactions


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(transactions, categories):
    """Generate a markdown spending report from parsed transactions."""
    if not transactions:
        return "# TD Spending Report\n\nNo transactions found.\n"

    # Sort by date
    transactions.sort(key=lambda t: t["date"])
    start = transactions[0]["date"].strftime("%B %d, %Y")
    end = transactions[-1]["date"].strftime("%B %d, %Y")

    total_income = 0.0
    total_expenses = 0.0
    category_totals = defaultdict(float)
    monthly = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})

    for txn in transactions:
        month_key = txn["date"].strftime("%Y-%m")
        if txn["type"] == "income":
            total_income += txn["amount"]
            monthly[month_key]["income"] += txn["amount"]
        else:
            total_expenses += txn["amount"]
            monthly[month_key]["expenses"] += txn["amount"]
            cat = categorize(txn["description"], categories)
            category_totals[cat] += txn["amount"]

    net = total_income - total_expenses

    # Build markdown
    lines = []
    lines.append(f"# TD Spending Report")
    lines.append(f"**Period:** {start} — {end}\n")

    # Summary
    lines.append("## Summary")
    lines.append(f"| | Amount |")
    lines.append(f"|---|---:|")
    lines.append(f"| **Income** | ${total_income:,.2f} |")
    lines.append(f"| **Expenses** | ${total_expenses:,.2f} |")
    lines.append(f"| **Net** | ${net:,.2f} |")
    lines.append("")

    # Monthly breakdown
    if len(monthly) > 1:
        lines.append("## Monthly Breakdown")
        lines.append("| Month | Income | Expenses | Net |")
        lines.append("|---|---:|---:|---:|")
        for month_key in sorted(monthly):
            m = monthly[month_key]
            month_label = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
            m_net = m["income"] - m["expenses"]
            lines.append(
                f"| {month_label} | ${m['income']:,.2f} | ${m['expenses']:,.2f} | ${m_net:,.2f} |"
            )
        lines.append("")

    # Spending by category
    if category_totals:
        lines.append("## Spending by Category")
        lines.append("| Category | Amount | % of Expenses |")
        lines.append("|---|---:|---:|")
        for cat, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
            pct = (amount / total_expenses * 100) if total_expenses else 0
            lines.append(f"| {cat} | ${amount:,.2f} | {pct:.1f}% |")
        lines.append("")

    # Recent transactions (last 20)
    lines.append("## Recent Transactions")
    lines.append("| Date | Description | Type | Amount |")
    lines.append("|---|---|---|---:|")
    for txn in transactions[-20:]:
        date_str = txn["date"].strftime("%Y-%m-%d")
        emoji = "🟢" if txn["type"] == "income" else "🔴"
        lines.append(
            f"| {date_str} | {txn['description']} | {emoji} {txn['type']} | ${txn['amount']:,.2f} |"
        )
    lines.append("")

    lines.append(f"---\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Find CSV files
    if len(sys.argv) > 1:
        csv_files = [Path(f) for f in sys.argv[1:]]
    else:
        DATA_DIR.mkdir(exist_ok=True)
        csv_files = list(DATA_DIR.glob("*.csv"))
        if not csv_files:
            print("Usage: python tracker.py [file1.csv file2.csv ...]")
            print(f"  Or drop CSV files into: {DATA_DIR}/")
            sys.exit(1)

    # Parse all CSVs
    all_transactions = []
    for csv_file in csv_files:
        print(f"Reading: {csv_file}")
        txns = parse_td_csv(csv_file)
        print(f"  Found {len(txns)} transactions")
        all_transactions.extend(txns)

    if not all_transactions:
        print("No transactions found in the provided files.")
        sys.exit(1)

    print(f"\nTotal: {len(all_transactions)} transactions")

    # Load categories and generate report
    categories = load_categories()
    report = generate_report(all_transactions, categories)

    # Write output
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "spending-report.md"
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Report saved to: {output_file}")
    print("\nCopy this file to your Obsidian vault, or update OBSIDIAN_VAULT below to auto-export.")


if __name__ == "__main__":
    main()

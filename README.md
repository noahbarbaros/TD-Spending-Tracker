# TD-Spending-Tracker

Simple Python script that parses TD Canada EasyWeb CSV exports and generates a markdown spending report — perfect for tracking income vs expenses in Obsidian.

## How it works

1. Download your transaction history as CSV from TD EasyWeb
2. Run the script
3. Get a clean markdown report with income, expenses, categories, and a transaction list

## Usage

```bash
# Option A: pass CSV files directly
python3 tracker.py statement-march.csv

# Option B: drop CSVs into the data/ folder and run without args
python3 tracker.py
```

The report is saved to `output/spending-report.md`. Copy it into your Obsidian vault.

## Customizing categories

Edit `categories.json` to add/change how transactions get categorized. It maps category names to keyword lists — if a keyword appears in the transaction description, it gets that category.

## File structure

```
TD-Spending-Tracker/
├── tracker.py          # main script
├── categories.json     # spending category keywords
├── data/               # drop your CSVs here (gitignored)
├── output/             # generated reports (gitignored)
└── sample.csv          # example data for testing
```

# 💰 Financial Health Score Analyzer

A data analytics project that processes raw bank transaction data and calculates a personalized **Financial Health Score (0–100)** based on savings rate, budget discipline, spending consistency, and anomaly detection — built using only **NumPy** and **Pandas**.

---

## 📌 Motivation

Most personal finance tools rely on machine learning or complex APIs. This project proves that **smart feature engineering + a custom scoring model** built with just NumPy and Pandas can deliver meaningful, real-world financial insights — the kind of analytical thinking that matters most in a Data Analyst role.

---

## 🗂️ Project Structure

```
finance-health-score/
│
├── data/
│   ├── transactions.csv          # Generated sample transaction data
│   ├── monthly_summary.csv       # Output: month-wise income, expense, savings
│   ├── category_breakdown.csv    # Output: spending % per category
│   └── anomalies.csv             # Output: flagged unusual transactions
│
├── generate_data.py              # Generates realistic fake transaction data
├── analysis.py                   # Main analysis + health score engine
└── README.md
```

---

## ⚙️ How It Works

### 1. Data Generation (`generate_data.py`)
- Generates **6 months** of realistic transaction data (Oct 2024 – Mar 2025)
- Salary credited once per month (~₹85,000 with slight variation)
- Expenses distributed across **20–40 random transactions** per month
- Uses **proportional scaling** to guarantee:
  - `total_expense < total_income` every month
  - At least **₹4,000 savings** remaining every month

### 2. Analysis Pipeline (`analysis.py`)

| Step | What It Does |
|------|-------------|
| Load & Clean | Reads CSV, parses dates, removes nulls and invalid amounts |
| Feature Engineering | Adds month/year columns, standardizes categories, creates `signed_amount` |
| Monthly Summary | Calculates income, expense, savings, savings rate per month |
| Category Breakdown | Ranks spending categories by total amount and percentage |
| Anomaly Detection | Flags transactions more than 2 standard deviations above category mean |
| Health Score | Computes weighted score across 4 financial metrics |
| Export | Saves all results as CSVs |

---

## 🏆 Health Score Formula

```
Health Score = (
    Savings Score      × 0.40 +
    Adherence Score    × 0.30 +
    Consistency Score  × 0.20 +
    Anomaly Score      × 0.10
) × 100
```

### Metric Definitions

| Metric | How It's Calculated |
|--------|-------------------|
| **Savings Score** | Average monthly savings rate vs 30% target + ₹4,000 minimum compliance |
| **Adherence Score** | % of months where `total_expense < total_income` |
| **Consistency Score** | Penalizes high variation in monthly savings rate (uses `np.std`) |
| **Anomaly Score** | Starts at 100, deducted 5 points per spending anomaly detected |

### Grade Scale

| Score | Grade |
|-------|-------|
| 80–100 | Excellent 🟢 |
| 60–79  | Good 🟡 |
| 40–59  | Fair 🟠 |
| 0–39   | Needs Work 🔴 |

---

## 🖥️ Sample Output

```
✅ No budget breaches — expenses always under income!

--- Monthly Summary ---
 year  month  month_name  total_income  total_expense  savings  savings_rate  budget_breached
 2024     10     October      85203.45       79812.30   5391.15          6.33            False
 2024     11    November      83491.20       78200.10   5291.10          6.34            False
 2024     12    December      86120.55       80905.44   5215.11          6.06            False
 2025      1     January      84755.30       79344.20   5411.10          6.38            False
 2025      2    February      85330.10       79987.65   5342.45          6.26            False
 2025      3       March      83910.75       78654.30   5256.45          6.27            False

--- Anomalies Detected: 3 ---
       date      category    amount   cat_mean
 2024-10-14      Shopping   4821.30     523.40
 2024-12-22  Entertnment    3990.10     489.20
 2025-02-08          Food   3750.55     480.30

==========================================
        💰 FINANCIAL HEALTH REPORT
==========================================
  Months meeting ₹4000 minimum : 6 / 6
  Savings Score      : 78.4 / 100
  Adherence Score    : 100.0 / 100
  Consistency Score  : 91.2 / 100
  Anomaly Score      : 85.0 / 100
------------------------------------------
  🏆 FINAL SCORE     : 88.1 / 100
  Grade              : Excellent 🟢
==========================================

✅ Results exported to /data folder
```

---

## 🔬 Key NumPy & Pandas Concepts Used

| Function | Library | Used For |
|----------|---------|---------|
| `pd.read_csv()` | Pandas | Load transaction data |
| `pd.to_datetime()` | Pandas | Parse date strings |
| `df.dropna()` | Pandas | Remove missing values |
| `df.groupby().agg()` | Pandas | Monthly income & expense summary |
| `df.sort_values()` | Pandas | Sort transactions chronologically |
| `dt.month / dt.year` | Pandas | Extract date components |
| `str.strip().str.title()` | Pandas | Standardize category text |
| `groupby().transform()` | Pandas | Add category-level stats per row |
| `df.iterrows()` | Pandas | Print per-month breach warnings |
| `np.where()` | NumPy | Conditional column assignment |
| `np.mean() / np.nanmean()` | NumPy | Average savings rate (NaN-safe) |
| `np.std()` | NumPy | Measure savings consistency |
| `np.clip()` | NumPy | Cap scores between 0 and 100 |
| `np.average(weights=...)` | NumPy | Weighted final health score |
| `np.random.exponential()` | NumPy | Realistic spend distribution |
| `np.random.choice()` | NumPy | Assign random days and categories |

---

## 🐛 Bugs Caught & Fixed (Learning Highlights)

### 1. NaN Propagation → Savings Score = 0
- **Cause:** `np.mean()` returns `NaN` when the array contains `NaN` values, which `np.clip()` then converts to `0`
- **Fix:** Used `np.nanmean()` and guarded division with `np.where(total_income > 0, ...)`

### 2. Silent Merge Bug → All Savings = 0
- **Cause:** Splitting income/expense into two DataFrames and merging on `month_name` caused silent key mismatches, resulting in `fillna(0)` zeroing out real values
- **Fix:** Replaced split→merge with a **single `groupby().agg()`** that computes both income and expense in one pass — no merge needed

### 3. Expenses Exceeding Income in Generated Data
- **Cause:** Old data generation looped freely over days with no monthly budget cap
- **Fix:** Switched to a **month-first loop** with `max_expense = salary - MIN_SAVINGS`, then used **proportional scaling** (`raw / raw.sum() * max_expense`) to guarantee the constraint

---

## 🚀 Getting Started

### Prerequisites
```bash
pip install pandas numpy
```

### Run the Project
```bash
# Step 1: Generate sample transaction data
python generate_data.py

# Step 2: Run the analysis and get your health score
python analysis.py
```

### Output Files (in `/data` folder)
| File | Contents |
|------|---------|
| `transactions.csv` | Raw generated transaction data |
| `monthly_summary.csv` | Month-wise income, expense, savings, score |
| `category_breakdown.csv` | Spending by category with percentages |
| `anomalies.csv` | Flagged high-spend transactions |

---

## 💡 What I Learned

- How to design a **custom weighted scoring system** from scratch
- How **NaN propagation** silently breaks calculations and how to defend against it
- Why **single groupby** is safer than split → groupby → merge
- How to use **proportional scaling** (`np.random.exponential` + normalization) to generate realistic constrained data
- How **standard deviation** (`np.std`) can measure behavioral consistency, not just spread

---

import numpy as np
import pandas as pd
import csv

# Set a seed so data is reproducible every time
np.random.seed(42)

# --- CONSTANTS ---
MIN_SAVINGS       = 4000   # ₹ minimum savings to keep every month
EXPENSE_CATEGORIES = ["Food", "Shopping", "Transport", "Entertainment", "Medical"]
rows = []

# Generate month by month — gives full control over monthly totals
months = pd.date_range(start="2024-10-01", end="2025-03-01", freq="MS")  
# freq="MS" → Month Start, gives first date of each month

for month_start in months:
    # --- STEP 1: Generate salary for this month (one credit entry) ---
    salary = round(np.random.normal(85000, 2000), 2)
    salary = max(salary, 70000)  # ensure salary never goes too low

    # Add salary as a single credit on the 1st of the month
    rows.append([month_start.strftime("%Y-%m-%d"), "Salary", "credit", salary])

    # --- STEP 2: Calculate max allowable expense for this month ---
    # total_expense must be < salary AND leave at least ₹4000 savings
    # So max expense = salary - MIN_SAVINGS - small buffer
    max_expense = salary - MIN_SAVINGS - np.random.randint(500, 2000)
    # The extra random buffer (500–2000) ensures savings > 4000, not just = 4000

    # --- STEP 3: Decide how many expense transactions this month gets ---
    num_transactions = np.random.randint(20, 40)  # 20–40 expense entries per month

    # --- STEP 4: Generate random raw amounts for each transaction ---
    # np.random.exponential gives realistic spend — many small, few large
    raw_amounts = np.random.exponential(scale=500, size=num_transactions)
    raw_amounts = np.clip(raw_amounts, 50, 5000)  # np.clip keeps the "raw_amount" between ₹50 and ₹5000

    # --- STEP 5: Scale amounts so they sum exactly to max_expense ---
    # This is the key trick — proportional scaling
    # scaled = (raw / sum_of_raw) * max_expense
    scaled_amounts = (raw_amounts / raw_amounts.sum()) * max_expense
    scaled_amounts = np.round(scaled_amounts, 2)

    # Fix rounding drift — last transaction absorbs the tiny remainder
    diff = round(max_expense - scaled_amounts.sum(), 2)
    scaled_amounts[-1] += diff

    # --- STEP 6: Spread transactions across random days of the month ---
    month_end   = month_start + pd.offsets.MonthEnd(0)  
    # MonthEnd(0) → last day of same month

    all_days    = pd.date_range(month_start, month_end, freq="D")
    
    # Pick random days (with repetition allowed — multiple spends on same day)
    random_days = np.random.choice(all_days, size=num_transactions, replace=True)
    random_days = sorted(random_days)  # sort so CSV is in chronological order

    # --- STEP 7: Assign a random category to each transaction ---
    categories  = np.random.choice(EXPENSE_CATEGORIES, size=num_transactions)

    for i in range(num_transactions):
        rows.append([
            pd.Timestamp(random_days[i]).strftime("%Y-%m-%d"),
            categories[i],
            "debit",
            scaled_amounts[i]
        ])

# --- BUILD & SAVE ---
df = pd.DataFrame(rows, columns=["date", "category", "type", "amount"])
df = df.sort_values("date").reset_index(drop=True)
df.to_csv("transactions.csv", index=False)

print("✅ Data generated:", df.shape)
print("\n--- Verification: Monthly Income vs Expense ---")

# Quick verification to confirm the condition holds
verify = df.copy()
verify["month"] = pd.to_datetime(verify["date"]).dt.month_name()
income  = verify[verify["type"] == "credit"].groupby("month")["amount"].sum()
expense = verify[verify["type"] == "debit"].groupby("month")["amount"].sum()
check   = pd.DataFrame({"Income": income, "Expense": expense})
check["Savings"]        = check["Income"] - check["Expense"]
check["Meets_4000_Min"] = check["Savings"] >= MIN_SAVINGS
print(check.to_string())
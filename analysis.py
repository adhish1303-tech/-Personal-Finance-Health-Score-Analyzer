import numpy as np
import pandas as pd

def load_clean(file_path):
    #Reading CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    # Basic data checks
    print("--- Raw Data ---")
    print(df.head())
    print("\nShape:", df.shape)
    print("\nData Types:\n", df.dtypes)
    print("\nMissing Values:\n", df.isnull().sum())

    #Converting String date values to datetime objects for easier analysis
    df["date"] = pd.to_datetime(df["date"])

    # Removing any rows with missing values in critical columns (date, amount, type)
    df = df.dropna(subset=["date", "amount", "type"])  

    #Removing all the negative values present in the amount column as they are not valid for our analysis
    df = df[df["amount"] > 0]

    print("\n-------Cleaned Data-------:", df.shape)
    return df

df = load_clean("transactions.csv")

def add_features(df):

    #Extracting month, year and month_name from the date column to crete new features for analysis
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    df["month_name"] = df["date"].dt.month_name()

    #Standardizing category text (To avoid issues with case sensitivity and extra spaces("Food" vs " food "))
    df["category"] = df["category"].str.strip().str.title()     #we use str to access string methods because we cannot directly apply string methods to a pandas Series without using str accessor
    
    #Creating a signed_amount category to differentiate between income and expenses (positive for income, negative for expenses)
    #np.where(condition, value_if_true , value_if_false)
    df["signed_amount"] = np.where(df["type"] == "credit", df["amount"], -df["amount"])

    print("\n-------Data with New Features-------:", df.shape)
    return df

df = add_features(df)

def monthly_summry(df): 

    # --- Group everything in ONE single groupby ---
    # No merge needed — signed_amount handles credit/debit direction
    # signed_amount was already created in add_features():
    # credit → positive, debit → negative

    monthly = (
        df.groupby(["year", "month", "month_name"])
        .agg(
            total_income  = ("amount",        lambda x: x[df.loc[x.index, "type"] == "credit"].sum()),
            total_expense = ("amount",        lambda x: x[df.loc[x.index, "type"] == "debit"].sum()),
        )
        .reset_index()
        .sort_values(["year", "month"])      # chronological order
        .reset_index(drop=True)
    )
    #"groupby" func ---> creates grps based on years, months and months_name. This will ensure Oct 2024 and Oct 2025 are not the same 
    #"agg" func ---> by using thsi func we not just summing everything but we are summing based on certain condition 
        #1) total_income -----> looks at the amt colums but the lamda acts like a filter and only sums where the "Type" = "Credit"
        #2) total_expense -----> looks at the amt colums but the lamda acts like a filter and only sums where the "Type" = "Debit"

    #"lamda" func:
        #x --->is the series of amounts for each group (month)
        #x.index ---> tell the lamda exactly which row in the orignal big table belongs to this group (month)
        #df.loc[x.index, "type"] ---> looks at the "Type" column for those specific rows and checks if it's "Credit" or "Debit"
        #x[...] ---> filter outs the specific group(month), keeping only the ones where the "type" = "credit"/ "debit" acc to the statement.

    # --- Calculating Savings Columns ---
    monthly["savings"] = monthly["total_income"] - monthly["total_expense"]

    # --- Calculating Savings Rate ---
    # Savings Rate = (Savings / Income) * 100, but only if income > 0 to avoid division by zero
    monthly["savings_rate"] = np.where(
        monthly["total_income"] > 0,
        np.round((monthly["savings"] / monthly["total_income"]) * 100, 2),
        0
    )

    # --- Adding a Budget Breach Flag to check if expenses exceed income ---
    monthly["budget_breached"] = monthly["total_expense"] >= monthly["total_income"]

    # --- Warnings ---
    breached = monthly[monthly["budget_breached"] == True]
    if not breached.empty:
        print("\n⚠️  Budget Breach Detected:")

        #itreting through the breached months to print out how much was overspent in each month
        for _, row in breached.iterrows():
            #Calculating by how much the expenses has exceded 
            excess = row["total_expense"] - row["total_income"]
            print(f"   → {row['month_name']}: Overspent by ₹{excess:.0f}")
    else:
        print("\n✅ No budget breaches — expenses always under income!")

    print("\n--- Monthly Summary ---")
    print(monthly.to_string(index=False))
    return monthly

summary = monthly_summry(df)

def category_breakdown(df):

    expense_df = df[df["type"] == "debit"]
    total_expense = expense_df["amount"].sum()

    #Calulating total expense per Category
    cat_summary = (
        expense_df.groupby("category")["amount"]    #grouping the data by category 
        .sum()                                      #summing the amount spent in each category to get total spending per category.
        .reset_index()
        .rename(columns={"amount": "total_spent"})  #renaming the amount column to total_spent for clarity
    )

    #Caculating what percentage of total expense each category takes up
    cat_summary["percentage"] = np.round
    (
                (cat_summary["total_spent"] / total_expense) * 100, 2       #Percentage = (Total Spent in Category / Total Expense) * 100
    )

    #Sorting the categories by total spent in descending order to see which cat takes up the most of the expenses.
    cat_summary = cat_summary.sort_values("total_spent", ascending=False)

    print("\n--- Spending by Category ---")
    print(cat_summary.to_string(index=False))
    return cat_summary

cat_summary = category_breakdown(df)

def dectection_anomalies(df):

    #Creating a copy of the original DataFrame to work with for anomaly detection
    expense_df = df[df["type"] == "debit"].copy() 

    #Computing mean and Std_Deviation for each category across all transactions
    expense_df["mean"] = expense_df.groupby("category")["amount"] \
        .transform("mean")  #transform is used to calculate the mean for each category and assign it back to the original DataFrame so that we can compare each transaction against its category mean.
    expense_df["std"]  = expense_df.groupby("category")["amount"] \
        .transform("std")   #same as above but for standard deviation

    
    #Flag for anomalies if amount > mean + 2*std (common threshold to detect outliers)
    expense_df["is_anomaly"] = expense_df["amount"] > (expense_df["mean"]+ 2 * expense_df["std"])       #"is_anomaly" column will contain True/False values 


    anomalies = expense_df[expense_df["is_anomaly"]] \
                    [["date", "category", "amount", "mean"]] \
                    .sort_values("amount", ascending=False)
    #expense_df[expense_df["is_anomaly"]] filters the DataFrame to keep only the rows where "is_anomaly" is True.
    # [["date", "category", "amount", "mean"]] selects only the relevant columns to display in the output.
    #sort_values("amount", ascending=False) sorts the anomalies by amount in descending order to see the most significant anomalies at the top.

    print(f"\n--- Anomalies Detected: {len(anomalies)} ---")
    print(anomalies.to_string(index=False))
    return anomalies

anomalies = dectection_anomalies(df)

def calculate_health_score(summary, anomalies):

    min_savings = 4000 # Minimum savings threshold for a good score (can be adjusted based on financial goals)

    # --- METRIC 1: Average Savings Rate (target: >= 30%) ---
    avg_savings_rate = np.mean(summary["savings_rate"].values)      
            #"summary["savings_rate"]" gives us the savings rate for each month.
            #".values" will convert pandas columns into numpy array
    savings_score    = np.clip(avg_savings_rate / 30 * 100, 0, 100)

    #Checking how many months met the 4000 min.
    months_met_minimum   = (summary["savings"] >= min_savings).sum()
    total_months         = len(summary)
    minimum_met_rate     = months_met_minimum / total_months

    # Blend savings rate score with minimum savings compliance
    # If minimum is always met → no penalty
    # If minimum is never met  → savings score reduced by up to 40%
    savings_score = savings_score * (0.6 + 0.4 * minimum_met_rate)

    print(f"  Months meeting ₹{min_savings} minimum : {months_met_minimum} / {total_months}")

    # --- METRIC 2: Budget Adherence (expense < income every month) ---
    months_in_budget   = (summary["savings"] > 0).sum()
    total_months       = len(summary)
    adherence_score    = (months_in_budget / total_months) * 100

    # --- METRIC 3: Consistency (low variation in savings rate) ---
    std_savings        = np.std(summary["savings_rate"].values)
    # Lower std = more consistent = better score
    consistency_score  = np.clip(100 - std_savings * 2, 0, 100)

    # --- METRIC 4: Anomaly Penalty ---
    anomaly_penalty    = np.clip(len(anomalies) * 5, 0, 40)
    anomaly_score      = 100 - anomaly_penalty

    # --- FINAL WEIGHTED SCORE ---
    weights = [0.40, 0.30, 0.20, 0.10]
    scores  = [savings_score, adherence_score, consistency_score, anomaly_score]

    # np.average with weights = weighted mean
    final_score = np.round(np.average(scores, weights=weights), 1)

    print("\n" + "="*45)
    print("      💰 FINANCIAL HEALTH REPORT")
    print("="*45)
    print(f"  Savings Score      : {savings_score:.1f} / 100")
    print(f"  Adherence Score    : {adherence_score:.1f} / 100")
    print(f"  Consistency Score  : {consistency_score:.1f} / 100")
    print(f"  Anomaly Score      : {anomaly_score:.1f} / 100")
    print("-"*45)
    print(f"  🏆 FINAL SCORE     : {final_score} / 100")

    # Warn the user which months failed the minimum
    failed_months = summary[summary["savings"] < min_savings][["month_name", "savings"]]
    if not failed_months.empty:
        print(f"\n  ⚠️  Months below ₹{min_savings} savings:")
        for _, row in failed_months.iterrows():
            print(f"      → {row['month_name']}: ₹{row['savings']:.0f}")

    if final_score >= 80:   grade = "Excellent 🟢"
    elif final_score >= 60: grade = "Good 🟡"
    elif final_score >= 40: grade = "Fair 🟠"
    else:                   grade = "Needs Work 🔴"

    print(f"  Grade              : {grade}")
    print("="*45)
    return final_score

score = calculate_health_score(summary, anomalies)

def export_results(summary, cat_summary, anomalies, score):
    summary.assign(health_score=score).to_csv(
        "monthly_summary.csv", index=False)

    cat_summary.to_csv("category_breakdown.csv", index=False)
    anomalies.to_csv("anomalies.csv",  index=False)

    print("\n✅ Results exported ")

export_results(summary, cat_summary, anomalies, score)
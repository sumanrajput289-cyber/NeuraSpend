# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Financial Prediction & Behavior Scoring Engine
"""

import collections
from datetime import datetime
import statistics
import math


def calculate_analytical_forecasts(expenses, monthly_budget=50000.0):
    """
    Computes mathematical forecasting metrics from historical transactions.
    Integrates multi-dimensional algorithms for predictions and health scoring.
    
    Returns a dictionary of metrics:
    {
        "average_monthly_spend": float,
        "predicted_next_month": float,
        "predicted_yearly": float,
        "spending_trend": str,         # "Upward", "Downward", or "Stable"
        "highest_growth_category": str,
        "health_score": int,           # 0 to 100
        "health_rating": str           # "Excellent", "Good", "Moderate", "Needs Improvement"
    }
    """
    default_result = {
        "average_monthly_spend": 0.0,
        "predicted_next_month": 0.0,
        "predicted_yearly": 0.0,
        "spending_trend": "Stable",
        "highest_growth_category": "Others",
        "health_score": 100,
        "health_rating": "Excellent"
    }

    if not expenses:
        return default_result

    # 1. Group transaction sums chronologically and by category
    monthly_series = collections.defaultdict(float)
    daily_series = collections.defaultdict(float)
    category_by_month = collections.defaultdict(lambda: collections.defaultdict(float))
    all_categories = collections.defaultdict(float)

    for exp in expenses:
        try:
            amount = float(exp["amount"])
            date_str = exp["transaction_date"]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            month_key = date_obj.strftime("%Y-%m")
            monthly_series[month_key] += amount
            daily_series[date_str] += amount
            category_by_month[month_key][exp["category"]] += amount
            all_categories[exp["category"]] += amount
        except (ValueError, TypeError, KeyError):
            continue

    if not monthly_series:
        return default_result

    # Sort months chronologically
    sorted_months = sorted(monthly_series.items())
    month_keys = [item[0] for item in sorted_months]
    monthly_totals = [item[1] for item in sorted_months]
    
    total_months = len(monthly_totals)
    total_spend = sum(monthly_totals)

    # A. Calculate Average Monthly Spending
    average_monthly_spend = total_spend / total_months

    # B. Forecast Next Month Spending (Linear projection model)
    predicted_next_month = average_monthly_spend
    spending_trend = "Stable"
    
    if total_months >= 2:
        # Calculate month-over-month growth rates
        growth_rates = []
        for i in range(1, len(monthly_totals)):
            prev = monthly_totals[i-1]
            curr = monthly_totals[i]
            if prev > 0:
                growth_rates.append((curr - prev) / prev)
            else:
                growth_rates.append(0.0)
        
        avg_growth = statistics.mean(growth_rates)
        latest_month_spend = monthly_totals[-1]
        predicted_next_month = latest_month_spend * (1 + avg_growth)
        
        # Guard against mathematical noise resulting in negative projections
        if predicted_next_month < 0:
            predicted_next_month = max(0.0, average_monthly_spend)

        # Classify spend trajectory direction
        if avg_growth > 0.05:
            spending_trend = "Upward"
        elif avg_growth < -0.05:
            spending_trend = "Downward"
        else:
            spending_trend = "Stable"
    else:
        predicted_next_month = average_monthly_spend
        spending_trend = "Stable"

    # C. Calculate Predicted Yearly Spending (Feature 1)
    # Projections mathematically scaled: average monthly burn multiplied by 12 calendar units
    predicted_yearly = average_monthly_spend * 12

    # D. Locate the Highest Growth Category
    highest_growth_category = "Others"
    if total_months >= 2:
        latest_month = month_keys[-1]
        prev_month = month_keys[-2]
        
        category_growth = {}
        for cat, curr_amount in category_by_month[latest_month].items():
            prev_amount = category_by_month[prev_month].get(cat, 0.0)
            if prev_amount > 0:
                growth = (curr_amount - prev_amount) / prev_amount
                category_growth[cat] = growth
            else:
                category_growth[cat] = 1.0  # Infinite growth baseline
        
        if category_growth:
            highest_growth_category = max(category_growth, key=category_growth.get)
    else:
        if all_categories:
            highest_growth_category = max(all_categories, key=all_categories.get)

    # ----------------------------------------------------------------------
    # E. MULTI-FACTOR FINANCIAL HEALTH SCORE CALCULATION (0 - 100) (Feature 2)
    # ----------------------------------------------------------------------
    # 1. Budget Adherence Factor (Weight: 50 points)
    # Compares current month spending vs limit
    latest_monthly_spend = monthly_totals[-1] if monthly_totals else total_spend
    budget_limit = monthly_budget if monthly_budget > 0 else 50000.0
    budget_ratio = latest_monthly_spend / budget_limit

    if budget_ratio <= 0.8:
        # High adherence
        budget_points = 50.0
    elif budget_ratio <= 1.0:
        # Warning limit
        budget_points = 50.0 - ((budget_ratio - 0.8) * 100.0)  # down to 30 points
    else:
        # Exceeded
        budget_points = max(0.0, 30.0 - ((budget_ratio - 1.0) * 50.0))

    # 2. Savings Ratio Factor (Weight: 20 points)
    # Savings ratio = (Budget - Spend) / Budget. If spending is low, score is high
    savings_ratio = max(0.0, (budget_limit - latest_monthly_spend) / budget_limit)
    savings_points = savings_ratio * 20.0

    # 3. Expense Consistency/Volatility Factor (Weight: 15 points)
    # High standard deviation in daily spends indicates volatility (unhealthy spending spikes)
    daily_amounts = list(daily_series.values())
    if len(daily_amounts) >= 2:
        try:
            std_dev = statistics.stdev(daily_amounts)
            mean_daily = statistics.mean(daily_amounts)
            coefficient_of_variation = std_dev / mean_daily if mean_daily > 0 else 0
            
            # Less variation (cv < 1.0) gets higher points. High spikes gets lower
            volatility_points = max(0.0, 15.0 - (coefficient_of_variation * 5.0))
        except Exception:
            volatility_points = 10.0
    else:
        volatility_points = 15.0  # Perfect score for single clean entry

    # 4. Category Distribution Balance Factor (Weight: 15 points)
    # We use entropy formula to verify category diversity (balanced spending is healthier)
    if all_categories:
        total_cat_spend = sum(all_categories.values())
        entropy = 0.0
        for val in all_categories.values():
            p = val / total_cat_spend if total_cat_spend > 0 else 0
            if p > 0:
                entropy -= p * math.log2(p)
                
        # Max entropy for 5 categories is log2(5) ~ 2.32
        max_entropy = 2.32
        entropy_ratio = min(1.0, entropy / max_entropy)
        category_points = entropy_ratio * 15.0
    else:
        category_points = 15.0

    # Summing all components
    health_score = int(budget_points + savings_points + volatility_points + category_points)
    health_score = max(0, min(100, health_score))

    # Determine qualitative rating
    if health_score >= 85:
        health_rating = "Excellent"
    elif health_score >= 70:
        health_rating = "Good"
    elif health_score >= 50:
        health_rating = "Moderate"
    else:
        health_rating = "Needs Improvement"

    return {
        "average_monthly_spend": round(average_monthly_spend, 2),
        "predicted_next_month": round(predicted_next_month, 2),
        "predicted_yearly": round(predicted_yearly, 2),
        "spending_trend": spending_trend,
        "highest_growth_category": highest_growth_category,
        "health_score": health_score,
        "health_rating": health_rating
    }

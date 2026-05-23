# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Breathtaking Financial Data Visualizations Center
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections
from datetime import datetime

# Prevent graphical issues on headless systems or background threads
import matplotlib
matplotlib.use("TkAgg")


def setup_chart_aesthetics(fig, ax, theme_colors):
    """
    Applies HSL-harmonized visual variables to a Matplotlib axis.
    Guarantees complete consistency with either the Light or Dark UI theme.
    """
    fig.patch.set_facecolor(theme_colors["bg_card"])
    ax.set_facecolor(theme_colors["bg_card"])
    
    # Grid lines configuration
    ax.grid(True, linestyle="--", alpha=0.15, color=theme_colors["fg_muted"])
    ax.set_axisbelow(True)

    # Frame boundaries coloration
    for spine in ax.spines.values():
        spine.set_color(theme_colors["border"])
        spine.set_linewidth(1.2)

    # Text elements coloring
    ax.tick_params(colors=theme_colors["fg_body"], labelsize=8)
    ax.xaxis.label.set_color(theme_colors["fg_body"])
    ax.yaxis.label.set_color(theme_colors["fg_body"])
    ax.title.set_color(theme_colors["fg_title"])


def render_category_pie_chart(container, expenses, theme_colors):
    """
    1. Pie Chart - Displays the percentage distribution of expenses across categories.
    """
    category_sums = collections.defaultdict(float)
    for exp in expenses:
        category_sums[exp["category"]] += float(exp["amount"])

    labels = list(category_sums.keys())
    sizes = list(category_sums.values())

    fig, ax = plt.subplots(figsize=(3.6, 2.5), dpi=100)
    fig.patch.set_facecolor(theme_colors["bg_card"])

    if sizes:
        pie_colors = [theme_colors["primary"], theme_colors["success"], theme_colors["warning"], theme_colors["danger"], "#8E8E93"]
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct="%1.1f%%",
            startangle=140,
            colors=pie_colors[:len(sizes)],
            textprops={"color": theme_colors["fg_body"], "fontsize": 8},
            wedgeprops={"edgecolor": theme_colors["bg_card"], "linewidth": 1.5, "antialiased": True}
        )
        for autotext in autotexts:
            autotext.set_color("#FFFFFF")
            autotext.set_weight("bold")
    else:
        ax.text(0.5, 0.5, "No Data Available", 
                horizontalalignment="center", verticalalignment="center",
                color=theme_colors["fg_muted"], fontsize=11)

    ax.axis("equal")
    ax.set_title("Category Distribution", fontsize=10, fontweight="bold", color=theme_colors["fg_title"], pad=8)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.configure(background=theme_colors["bg_card"])
    
    plt.close(fig)
    return canvas_widget


def render_monthly_bar_chart(container, expenses, theme_colors):
    """
    2. Bar Chart - Compares monthly totals to trace spending growth trends.
    """
    monthly_totals = collections.defaultdict(float)
    for exp in expenses:
        try:
            date_obj = datetime.strptime(exp["transaction_date"], "%Y-%m-%d")
            month_key = date_obj.strftime("%b %Y")
            monthly_totals[month_key] += float(exp["amount"])
        except (ValueError, TypeError):
            continue

    sorted_months = sorted(monthly_totals.items(), 
                           key=lambda x: datetime.strptime(x[0], "%b %Y"))
    
    months = [item[0] for item in sorted_months]
    totals = [item[1] for item in sorted_months]

    fig, ax = plt.subplots(figsize=(3.6, 2.5), dpi=100)
    setup_chart_aesthetics(fig, ax, theme_colors)

    if months:
        bars = ax.bar(months, totals, color=theme_colors["primary"], width=0.45, alpha=0.95)
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{int(height)}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 2),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, color=theme_colors["fg_muted"])
    else:
        ax.text(0.5, 0.5, "No Data Available", 
                horizontalalignment="center", verticalalignment="center",
                color=theme_colors["fg_muted"], fontsize=11)

    ax.set_title("Monthly Trend Comparison", fontsize=10, fontweight="bold", pad=8)
    plt.xticks(rotation=10)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.configure(background=theme_colors["bg_card"])
    
    plt.close(fig)
    return canvas_widget


def render_expense_line_graph(container, expenses, theme_colors):
    """
    3. Line Graph - Plots expenses chronological trajectory.
    """
    daily_spend = collections.defaultdict(float)
    for exp in expenses:
        try:
            date_str = exp["transaction_date"]
            daily_spend[date_str] += float(exp["amount"])
        except (ValueError, TypeError):
            continue

    sorted_days = sorted(daily_spend.items())
    dates = [item[0] for item in sorted_days]
    amounts = [item[1] for item in sorted_days]

    short_dates = []
    for d in dates:
        try:
            short_dates.append(datetime.strptime(d, "%Y-%m-%d").strftime("%m-%d"))
        except ValueError:
            short_dates.append(d)

    fig, ax = plt.subplots(figsize=(3.6, 2.5), dpi=100)
    setup_chart_aesthetics(fig, ax, theme_colors)

    if dates:
        ax.plot(short_dates, amounts, color=theme_colors["success"], marker="o", 
                linewidth=1.8, markersize=3.5, markerfacecolor=theme_colors["primary"],
                markeredgecolor=theme_colors["fg_body"])
        if len(short_dates) > 6:
            ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    else:
        ax.text(0.5, 0.5, "No Data Available", 
                horizontalalignment="center", verticalalignment="center",
                color=theme_colors["fg_muted"], fontsize=11)

    ax.set_title("Expense Stream Progression", fontsize=10, fontweight="bold", pad=8)
    plt.xticks(rotation=10)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.configure(background=theme_colors["bg_card"])
    
    plt.close(fig)
    return canvas_widget


def render_top_categories_hbar(container, expenses, theme_colors):
    """
    4. Horizontal Bar Chart - Ranks category totals.
    """
    category_sums = collections.defaultdict(float)
    for exp in expenses:
        category_sums[exp["category"]] += float(exp["amount"])

    sorted_cats = sorted(category_sums.items(), key=lambda x: x[1])
    categories = [item[0] for item in sorted_cats]
    sums = [item[1] for item in sorted_cats]

    fig, ax = plt.subplots(figsize=(3.6, 2.5), dpi=100)
    setup_chart_aesthetics(fig, ax, theme_colors)

    if categories:
        ax.barh(categories, sums, color=theme_colors["warning"], height=0.45)
    else:
        ax.text(0.5, 0.5, "No Data Available", 
                horizontalalignment="center", verticalalignment="center",
                color=theme_colors["fg_muted"], fontsize=11)

    ax.set_title("Top Spending Channels", fontsize=10, fontweight="bold", pad=8)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.configure(background=theme_colors["bg_card"])
    
    plt.close(fig)
    return canvas_widget


def render_budget_utilization_chart(container, expenses, budget_limit, warning_limit, theme_colors):
    """
    5. Budget Utilization Graph - Plots monthly total spending compared directly
    against budget limit and warning threshold lines.
    """
    current_month = datetime.now().strftime("%Y-%m")
    total_spent = sum(float(exp["amount"]) for exp in expenses if exp["transaction_date"].startswith(current_month))

    fig, ax = plt.subplots(figsize=(3.6, 2.5), dpi=100)
    setup_chart_aesthetics(fig, ax, theme_colors)

    # Plot single spending bar
    categories = ["Spending", "Warning", "Budget"]
    values = [total_spent, warning_limit, budget_limit]
    bar_colors = [theme_colors["primary"], theme_colors["warning"], theme_colors["danger"]]

    ax.bar(categories, values, color=bar_colors, width=0.4, alpha=0.95)
    for i, v in enumerate(values):
        ax.annotate(f"{int(v)}",
                    xy=(i, v),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, color=theme_colors["fg_body"], fontweight="bold")

    ax.set_title("Current Budget Adherence", fontsize=10, fontweight="bold", pad=8)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.configure(background=theme_colors["bg_card"])
    
    plt.close(fig)
    return canvas_widget


def render_yearly_overview_chart(container, expenses, theme_colors):
    """
    6. Yearly Spending Overview - Groups spending totals chronologically by calendar years.
    """
    yearly_totals = collections.defaultdict(float)
    for exp in expenses:
        try:
            date_obj = datetime.strptime(exp["transaction_date"], "%Y-%m-%d")
            year_key = date_obj.strftime("%Y")
            yearly_totals[year_key] += float(exp["amount"])
        except (ValueError, TypeError):
            continue

    sorted_years = sorted(yearly_totals.items())
    years = [item[0] for item in sorted_years]
    totals = [item[1] for item in sorted_years]

    fig, ax = plt.subplots(figsize=(3.6, 2.5), dpi=100)
    setup_chart_aesthetics(fig, ax, theme_colors)

    if years:
        bars = ax.bar(years, totals, color=theme_colors["success"], width=0.35, alpha=0.95)
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{int(height)}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 2),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=8, color=theme_colors["fg_body"])
    else:
        ax.text(0.5, 0.5, "No Data Available", 
                horizontalalignment="center", verticalalignment="center",
                color=theme_colors["fg_muted"], fontsize=11)

    ax.set_title("Yearly Outflow Volumes", fontsize=10, fontweight="bold", pad=8)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.configure(background=theme_colors["bg_card"])
    
    plt.close(fig)
    return canvas_widget

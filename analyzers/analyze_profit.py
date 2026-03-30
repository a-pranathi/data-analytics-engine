'''
File: analyze_profit.py
Author: Pranathi Ayyadevara
Description:
    	Surfaces net profitability drivers by combining margin, 
        cost, and sales data. Highlights high-impact SKUs contributing to overall profit uplift or drag.
'''

from analyzers.analyze import Analyze
from common.constants import *
import pandas as pd

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class AnalyzeProfit(Analyze):
    def __init__(self, app_container):
        super().__init__(app_container)
        self.analyzer_type = AnalyzerType.PROFIT
        self.output_file = self.app_container.config.get_analyzer_output_file(self.analyzer_type)
    
    def compute_monthly_realized_profit(self):
        df_sales = self.app_container.dataset.get_data(DataTypes.SALES_DATA)
        df_expenses = self.app_container.dataset.get_data(DataTypes.EXPENSE_DATA)
        df_margin = self.app_container.dataset.get_margin_data()

        date_col="Voucher Date"
        sku_col_sales="Stock No"
        sku_col_margin="SKU"
        qty_col="Sales Qty"
        net_amount_col="Net Amount"
        unit_cost_col="Unit_Cost"
        unit_sell_col="Unit_Selling_Price"

        # Ensure date is datetime
        df_sales[date_col] = pd.to_datetime(df_sales[date_col], errors="coerce")

        # Merge sales with margin dataset on SKU
        df_combined = pd.merge(
            df_sales,
            df_margin[[sku_col_margin, unit_cost_col]],
            left_on=sku_col_sales,
            right_on=sku_col_margin,
            how="left"
        )

        df_combined["COGS"] = df_combined[unit_cost_col] * df_combined[qty_col]
        df_combined["Profit"] = df_combined[net_amount_col] - df_combined["COGS"]
        df_combined["Month"] = df_combined[date_col].dt.to_period("M")
        df_monthly = (
            df_combined.groupby("Month", as_index=False)
            .agg({
                qty_col: "sum",
                net_amount_col: "sum",
                "COGS": "sum",
                "Profit": "sum"
            })
            .rename(columns={
                qty_col: "Total_Sales_Qty",
                net_amount_col: "Total_Sales_Value",
                "COGS": "Total_COGS",
                "Profit": "Total_Profit"
            })
        )

        df_monthly = df_monthly.copy()
        df_monthly["Month"] = df_monthly["Month"].astype(str)

        df_expenses = df_expenses.copy()
        df_expenses["month"] = df_expenses["month"].astype(str)
        
        df_final = pd.merge(
            df_monthly,       # from realized margin function
            df_expenses,      # your expense dataset
            left_on="Month",
            right_on="month",
            how="left"
        )

        df_final["Net_Profit"] = df_final["Total_Profit"] - df_final["expense"]

        return df_final


    def plot_profit_expense_overlay(self, df,
                                    month_col="Month",
                                    realized_profit_col="Total_Profit",
                                    expense_col="expense",
                                    net_profit_col="Net_Profit",
                                    title="Realized Profit vs Expenses with Net Profit Overlay",
                                    figsize=(12,6)):
 
        # Work on a copy
        df_plot = df[[month_col, realized_profit_col, expense_col, net_profit_col]].copy()

        # Normalize month to pandas datetime (use first day of month for consistency)
        if np.issubdtype(df_plot[month_col].dtype, np.datetime64):
            dt = pd.to_datetime(df_plot[month_col])
            df_plot["Month_dt"] = dt.dt.to_period("M").dt.to_timestamp()
        else:
            # If strings or Period, coerce to Period[M] then to timestamp
            try:
                per = pd.PeriodIndex(df_plot[month_col], freq="M")
            except Exception:
                per = pd.PeriodIndex(pd.to_datetime(df_plot[month_col]).to_period("M"), freq="M")
            df_plot["Month_dt"] = per.to_timestamp()

        # Coerce numeric columns and fill missing with 0
        for c in [realized_profit_col, expense_col, net_profit_col]:
            df_plot[c] = pd.to_numeric(df_plot[c], errors="coerce").fillna(0)

        # Deduplicate by month (sum duplicates, e.g., if internal merges produced repeated rows)
        df_plot = (
            df_plot.groupby("Month_dt", as_index=False)
            .agg({
                realized_profit_col: "sum",
                expense_col: "sum",
                net_profit_col: "sum"
            })
            .sort_values("Month_dt")
        )

        # Prepare series
        x = df_plot["Month_dt"]
        realized_profit = df_plot[realized_profit_col].values
        expenses_negative = -df_plot[expense_col].values  # plot below zero
        net_profit = df_plot[net_profit_col].values

        # Plot
        #plt.style.use("seaborn-white") 
        fig, ax = plt.subplots(figsize=figsize)

        # Stacked areas (two separate calls keeps clarity for legend)
        ax.stackplot(x, realized_profit, labels=["Realized Profit"], colors=["#2ca02c"], alpha=0.6)
        ax.stackplot(x, expenses_negative, labels=["Expenses (negative)"], colors=["#ff7f0e"], alpha=0.6)

        # Net profit overlay
        ax.plot(x, net_profit, color="#1f77b4", linewidth=2.5, marker="o", label="Net Profit")

        # Zero baseline
        ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")

        # X-axis formatting
        locator = mdates.MonthLocator(interval=1)
        formatter = mdates.DateFormatter("%Y-%m")
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        fig.autofmt_xdate()

        # Annotations: peak and trough net profit
        if len(net_profit) > 0:
            max_idx = int(np.nanargmax(net_profit))
            min_idx = int(np.nanargmin(net_profit))
            ax.annotate(f'Peak ₹{net_profit[max_idx]:,.0f}',
                        (x.iloc[max_idx], net_profit[max_idx]),
                        textcoords="offset points", xytext=(0,8),
                        ha="center", va="bottom", color="#1f77b4", fontsize=9, fontweight="bold")
            ax.annotate(f'Low ₹{net_profit[min_idx]:,.0f}',
                        (x.iloc[min_idx], net_profit[min_idx]),
                        textcoords="offset points", xytext=(0,-18),
                        ha="center", va="top", color="#d62728", fontsize=9)

        # Labels and legend
        ax.set_title(title)
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount (₹)")
        ax.legend(loc="upper left")

        plt.tight_layout()
        return fig

    def process(self):
        print("Performing Profit Analysis...")          

        result = self.compute_monthly_realized_profit()
        fig = self.plot_profit_expense_overlay(result)
        fig.show()

        self.save_report(result)
        self.save_report(data=[("Profit Analysis", result)],
                               figures=[("Profit Analysis", fig)])
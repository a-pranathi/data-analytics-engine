'''
File: analyze_inventory.py
Author: Pranathi Ayyadevara
Description:
    Diagnoses of stock health by analyzing opening, purchase, return,
    sales, and closing data. Flags deadstock, overstock, and discrepancy zones.
'''

import pandas as pd
from analyzers.analyze import Analyze
from common.constants import *

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class AnalyzeInventory(Analyze):
    def __init__(self, app_container):
        super().__init__(app_container)
        self.analyzer_type = AnalyzerType.INVENTORY
        self.output_file = self.app_container.config.get_analyzer_output_file(self.analyzer_type)

    def analyze_negative_stock(self):

        # get opening and closing stock
        opening_df = self.app_container.dataset.get_data(DataTypes.OPENING_STOCK)
        closing_df = self.app_container.dataset.get_data(DataTypes.CLOSING_STOCK)

        # Filter negative quantities
        negative_opening = opening_df[opening_df["Closing Bal.Qty"] < 0].copy()
        negative_closing = closing_df[closing_df["Closing Bal.Qty"] < 0].copy()

        # Tag each with type 
        negative_opening["Type"] = "Negative Opening"
        negative_closing["Type"] = "Negative Closing"

        # Move 'Type' to the front
        cols = ["Type"] + [col for col in negative_opening.columns if col != "Type"]
        negative_opening = negative_opening[cols]
        negative_closing = negative_closing[cols]

        # Combine opening and closing to save to a single file
        combined_df = pd.concat([negative_opening, negative_closing], ignore_index=True)
        return combined_df
    
    def analyze_discrepancy(self):
        # Load datasets
        opening = self.app_container.dataset.get_data(DataTypes.OPENING_STOCK)
        purchases = self.app_container.dataset.get_data(DataTypes.PURCHASE_DATA)
        purchase_returns = self.app_container.dataset.get_data(DataTypes.PURCHASE_RETURN_DATA)
        sales = self.app_container.dataset.get_data(DataTypes.SALES_DATA)
        stock_verification = self.app_container.dataset.get_data(DataTypes.STOCK_VERIFICATION_DATA)
        closing = self.app_container.dataset.get_data(DataTypes.CLOSING_STOCK)

        # Filter out rows where 'Difference Qty' is zero
        #stock_verification = stock_verification[stock_verification['Difference Qty'] != 0]

        # Pre-aggregate quantities by SKU
        opening_qty_map = opening.groupby("Stock No")["Closing Bal.Qty"].sum()
        purchase_qty_map = purchases.groupby("Stock No")["Purchase Qty"].sum()
        return_qty_map = purchase_returns.groupby("Stock No")["Purch. Return Qty"].sum()
        sales_qty_map = sales.groupby("Stock No")["Sales Qty"].sum()
        stock_verification_map = stock_verification.groupby("Stock No")["Difference Qty"].sum()
        closing_qty_map = closing.groupby("Stock No")["Closing Bal.Qty"].sum()

        # Unified SKU list
        sku_set = set(opening_qty_map.index) | set(purchase_qty_map.index) | set(return_qty_map.index) | set(sales_qty_map.index) | set(stock_verification_map.index) | set(closing_qty_map.index)

        summary = []

        for sku in sku_set:
            open_qty = opening_qty_map.get(sku, 0)
            purchase_qty = purchase_qty_map.get(sku, 0)
            return_qty = return_qty_map.get(sku, 0)
            sales_qty = sales_qty_map.get(sku, 0)
            stock_verification_qty = stock_verification_map.get(sku, 0)
            close_qty = closing_qty_map.get(sku, 0)

            expected_close = open_qty + purchase_qty - return_qty - sales_qty + stock_verification_qty
            discrepancy = close_qty - expected_close

            # Collect only if discrepancy exists
            if discrepancy != 0:
                summary.append({
                    "SKU": sku,
                    "Opening Qty": open_qty,
                    "Purchase Qty": purchase_qty,
                    "Purchase Return Qty": return_qty,
                    "Sales Qty": sales_qty,
                    "Stock verification Adjustment": stock_verification_qty,
                    "Expected Closing": expected_close,
                    "Actual Closing": close_qty,
                    "Discrepancy": discrepancy
                })

        return pd.DataFrame(summary)

    def analyze_stock(self):
        margin_data = self.app_container.dataset.get_margin_data()
        stocked_then_removed = margin_data[(margin_data['Sales_Qty'] == 0) & (margin_data['Closing_Qty'] == 0)]
        dead_stock = margin_data[(margin_data['Sales_Qty'] == 0) & (margin_data['Closing_Qty'] > 0)]

        return stocked_then_removed, dead_stock



    def plot_inventory_diagnostics(self):
        steps = []
        changes = []

        opening = self.app_container.dataset.get_aggregate_column(DataTypes.OPENING_STOCK, "Closing Bal.Qty")
        steps.append("Opening Stock")

        value = self.app_container.dataset.get_aggregate_column(DataTypes.PURCHASE_DATA, "Purchase Qty")
        steps.append("Purchase")
        changes.append(value)

        value = self.app_container.dataset.get_aggregate_column(DataTypes.PURCHASE_RETURN_DATA, "Purch. Return Qty")
        steps.append("Purchase Return")
        changes.append(0 - value)

        value = self.app_container.dataset.get_aggregate_column(DataTypes.STOCK_VERIFICATION_DATA, "Difference Qty")
        steps.append("Stock Verification Adjustment")
        changes.append(value)

        value = self.app_container.dataset.get_aggregate_column(DataTypes.SALES_DATA, "Sales Qty")
        steps.append("Sales")
        changes.append(0 - value) 

        cumulative = [opening]  # after Opening
        for ch in changes:
            cumulative.append(cumulative[-1] + ch)  # after each change

        closing = self.app_container.dataset.get_aggregate_column(DataTypes.CLOSING_STOCK, "Closing Bal.Qty")
        steps.append("Descrepency")
        changes.append(closing - cumulative[-1])
        steps.append("closing Stock")

        # Plot setup
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(steps))

        # 1) Opening bar
        ax.bar(x[0], opening, color="steelblue", label="Opening")
        ax.text(x[0], opening, f"{opening:,}", ha="center", va="bottom", fontsize=9)

        # 2) Intermediate changes
        prior_total = opening
        for i, ch in enumerate(changes, start=1):
            color = "green" if ch > 0 else "red"
            ax.bar(x[i], ch, bottom=prior_total, color=color)
            # Label the step value at the top of the bar
            ax.text(x[i], prior_total + ch, f"{ch:+,}", ha="center", va="bottom", fontsize=9)
            prior_total += ch

        # 3) Closing bar
        ax.bar(x[-1], closing, color="navy", label="Closing")
        ax.text(x[-1], closing, f"{closing:,}", ha="center", va="bottom", fontsize=9)

        # Formatting
        ax.set_xticks(x)
        ax.set_xticklabels(steps, rotation=30, ha="right")
        ax.set_ylabel("Units")
        ax.set_title("Stock Reconciliation Waterfall (Units)")
        ax.legend()
        ax.grid(True, axis='y', linestyle='--', alpha=0.4)

        plt.tight_layout()
        return fig


    def classify_inventory_movement(self):
        print("classify_inventory_movement")

    def compute_inventory_velocity(self):
        print("compute_inventory_velocity")


    def compute_stocked_unsold(self):
        print("compute_stocked_unsold")

    def tag_inventory_insights(self):
        print("tag_inventory_insights")

    def process(self):
        print("Performing Inventory Analysis...")         

        negative_stock = self.analyze_negative_stock()
        discrepancy_stock = self.analyze_discrepancy()
        stocked_then_removed, dead_stock = self.analyze_stock()

        fig_inventory_diagnostics = self.plot_inventory_diagnostics()

        self.save_report(data=[("Negative Stock", negative_stock),
                               ("Discrepancy Stock", discrepancy_stock),
                               ("Stocked Then Removed", stocked_then_removed),
                               ("Dead Stock", dead_stock)],
                               figures=[("Inventory Diagnostics", fig_inventory_diagnostics),
                                        ])
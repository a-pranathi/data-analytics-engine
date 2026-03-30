'''
File: analyze_margin.py
Author: Pranathi Ayyadevara
Description:
    Diagnostic module for margin analysis. Computes SKU-level margin gain/erosion
    based on opening and closing stock valuations, sales, returns, and realized margins.
'''

import pandas as pd
import matplotlib.pyplot as plt

from common.constants import *
from analyzers.analyze import Analyze
from common.chart_builder import ChartBuilder 
import seaborn as sns
import numpy as np

class AnalyzeMargin(Analyze):

    def __init__(self, app_container):
        super().__init__(app_container)
        self.analyzer_type = AnalyzerType.MARGIN
        self.output_file = self.app_container.config.get_analyzer_output_file(self.analyzer_type)

    def analyze_margin_change(self):
        opening_df = self.app_container.dataset.get_data(DataTypes.OPENING_STOCK)
        closing_df = self.app_container.dataset.get_data(DataTypes.CLOSING_STOCK)
               
        # Select key columns
        opening_cols = ["Stock No", "Cost Price", "Retail Price", "Closing Bal.Qty"]
        closing_cols = ["Stock No", "Cost Price", "Retail Price", "Closing Bal.Qty"]

        # Prepare opening and closing datasets
        opening = opening_df[opening_cols].copy()
        closing = closing_df[closing_cols].copy()

        opening.rename(columns={
            "Cost Price": "Opening Cost",
            "Retail Price": "Opening Retail",
            "Closing Bal.Qty": "Opening Qty"
        }, inplace=True)

        closing.rename(columns={
            "Cost Price": "Closing Cost",
            "Retail Price": "Closing Retail",
            "Closing Bal.Qty": "Closing Qty"
        }, inplace=True)

        # Merge only items present in both datasets
        merged = pd.merge(opening, closing, on="Stock No", how="inner")

        # Calculate margins and changes
        merged["Opening Margin"] = merged["Opening Retail"] - merged["Opening Cost"]
        merged["Closing Margin"] = merged["Closing Retail"] - merged["Closing Cost"]
        merged["Margin Change"] = merged["Closing Margin"] - merged["Opening Margin"]
        merged["Stock Movement"] = merged["Closing Qty"] - merged["Opening Qty"]
        merged["Weighted Margin Impact"] = merged["Margin Change"] * merged["Closing Qty"]

        # Split into erosion and gain
        erosion_df = merged[merged["Margin Change"] < 0].copy()
        gain_df = merged[merged["Margin Change"] > 0].copy()

        # Stats
        total_items = len(merged)
        erosion_stats = {
            "Count": len(erosion_df),
            "Percent": round(len(erosion_df) / total_items * 100, 2),
            "Total Value Impact": round(erosion_df["Weighted Margin Impact"].sum(), 2)
        }

        gain_stats = {
            "Count": len(gain_df),
            "Percent": round(len(gain_df) / total_items * 100, 2),
            "Total Value Impact": round(gain_df["Weighted Margin Impact"].sum(), 2)
        }

        # Sort results
        erosion_df = erosion_df.sort_values("Margin Change")
        gain_df = gain_df.sort_values("Margin Change", ascending=False)

        margin_stats = pd.DataFrame([
            {"Type": "Margin Erosion", **erosion_stats},
            {"Type": "Margin Gain", **gain_stats}
        ])

        return erosion_df, gain_df, margin_stats

    def tag_insight(self, name, condition_func, df):
        filtered = condition_func(df)
        insight = pd.DataFrame()
        insight['Insight'] = [name] * len(filtered)
        insight = pd.concat([insight.reset_index(drop=True), filtered.reset_index(drop=True)], axis=1)
        return insight


    def compute_realized_unrealized_margin(self):
        top_items = pd.DataFrame()
        top_quantity = 20
        margin_data = self.app_container.dataset.get_margin_data()
        
        insight_conditions = {
            "Top Realized Margin": lambda df: df.sort_values(by='Realized_Margin', ascending=False).head(top_quantity),
            "Bottom Realized Margin": lambda df: df.sort_values(by='Realized_Margin').head(top_quantity),
            "Top Unrealized Margin": lambda df: df[df['Closing_Qty'] > 0].sort_values(by='Unrealized_Margin', ascending=False).head(top_quantity),
            "High Inventory Value": lambda df: df[df['Closing_Qty'] > 0].sort_values(by='Purchase_Value', ascending=False).head(top_quantity),
            "Top Sellers": lambda df: df[df['Sales_Qty'] > 0].sort_values(by='Sales_Qty', ascending=False).head(top_quantity),
            "Top Sale value": lambda df: df[df['Sales_Value'] > 0].sort_values(by='Sales_Value', ascending=False).head(top_quantity),
        }

        for name, condition in insight_conditions.items():
            top_items = pd.concat([top_items, self.tag_insight(name, condition, margin_data)])

        return margin_data, top_items

    def build_horizontal_bar_chart(self, df, metric, xlable, top_n: int = 10):
        try:
            df = df.copy()

            # Validate column
            if metric not in df.columns:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.text(0.5, 0.5, f"Column '{metric}' not found in dataset", ha='center', va='center', fontsize=12)
                ax.axis('off')
                return fig

            # Clean and rank
            df[metric] = pd.to_numeric(df[metric], errors='coerce')
            df = df.dropna(subset=[metric])
            df = df.sort_values(by=metric, ascending=False).head(top_n)
            annotations = df.apply(lambda row: f"{row['Brand']} - {row['Product']}", axis=1).tolist()

            # Label for display
            df['Label'] = df['SKU'].astype(str)

            # Build chart
            chart = ChartBuilder(
                df=df,
                chart_type=ChartType.BARH,
                x=metric,
                y='Label',
                title=f'Top {top_n} SKUs by {metric}',
                xlabel=xlable,
                ylabel='SKU',
                legend=False,
                grid=True,
                annotations=annotations,
                export={'figsize': (10, 6)}
            )

            return chart.render()

        except Exception as e:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, f"Chart error: {str(e)}", ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig

    def analyze_leaderboard_skus(self, df, top_n):
        margin_col='Realized_Margin'
        quantity_col='Sales_Qty'
        value_col='Sales_Value'
        sku_col='SKU'
        brand_col='Brand'
        product_col='Product'

        steps = []
        for i in range(5, top_n+1, 5):
            steps.append(i)

        df[margin_col] = pd.to_numeric(df[margin_col], errors='coerce')
        df[quantity_col] = pd.to_numeric(df[quantity_col], errors='coerce')
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        df = df.dropna(subset=[margin_col, quantity_col, value_col])

        sku_buckets = {}
        leaderboard_summary = []

        for n in steps:
            top_margin = set(df.nlargest(n, margin_col)[sku_col])
            top_quantity = set(df.nlargest(n, quantity_col)[sku_col])
            top_value = set(df.nlargest(n, value_col)[sku_col])

            common_skus = top_margin & top_quantity & top_value
            leaderboard_summary.append({'Top_N': n, 'Leader_SKUs': len(common_skus)})

            for sku in common_skus:
                sku_buckets.setdefault(sku, []).append(n)

        leader_skus = df[[sku_col, brand_col, product_col]].drop_duplicates()
        leader_skus = leader_skus[leader_skus[sku_col].isin(sku_buckets.keys())].copy()
        leader_skus['Top_N Buckets'] = leader_skus[sku_col].map(sku_buckets)

        leaderboard_summary_df = pd.DataFrame(leaderboard_summary)

        return leaderboard_summary_df, leader_skus

    def plot_leaderboard_summary(self, leaderboard_summary_df):
        fig = ChartBuilder(
            df=leaderboard_summary_df,
            chart_type=ChartType.BAR,
            x='Top_N',
            y='Leader_SKUs',
            title='Top-N vs Number of SKUs on All Three Leaderboards',
            xlabel='Top-N Threshold',
            ylabel='Number of Leader SKUs',
            legend=False,
            grid=True
        )
        return fig.render()

    def plot_bucket_contribution_with_efficiency(self, df):

        df_filtered = df[(df["Sales_Value"] > 0) & (df["Realized_Margin"] > 0)].copy()
        fig_bucket_contribution = ChartBuilder.plot_bucket_contribution_with_efficiency(
            df=df_filtered,
            metrics=['Sales_Value', 'Realized_Margin'],
            efficiency_pair=('Sales_Value', 'Realized_Margin'),
            mode='normalized',
            orientation='vertical',
            anchor_metric='Sales_Value',
            title="Normalized % Contribution with Efficiency Overlay"
        )        
        return fig_bucket_contribution

    def process(self):
        print("Performing Margin Analysis...")
        margin_result, top_items = self.compute_realized_unrealized_margin()
        erosion_df, gain_df, margin_stats = self.analyze_margin_change()

        leaderboard_summary_df, leader_skus = self.analyze_leaderboard_skus(margin_result,50)
        fig_top_n_leaders = self.plot_leaderboard_summary(leaderboard_summary_df)

        fig_realized_magin = self.build_horizontal_bar_chart(margin_result, metric='Realized_Margin', xlable='Realized Margin (₹)', top_n=5)
        fig_sales_values = self.build_horizontal_bar_chart(margin_result, metric='Sales_Value', xlable='Sale value (₹)', top_n=5)
        fig_sales_quantity = self.build_horizontal_bar_chart(margin_result, metric='Sales_Qty', xlable='Sale Quantity', top_n=5)
        fig_bucket_contribution = self.plot_bucket_contribution_with_efficiency(margin_result)

        self.save_report(data=[("Margin Diagnostics", margin_result),
                               ("Top Statistics", top_items),
                               ("Margin Erosion", erosion_df), 
                               ("Margin Gain", gain_df),
                               ("Margin Statistics", margin_stats),
                               ("Top N Leaderboard", leader_skus)],                               
                               figures=[("Realized Margin", fig_realized_magin),
                                        ("Sales Quantity", fig_sales_quantity),
                                        ("Sales Values", fig_sales_values),
                                        ("Top N Leaders", fig_top_n_leaders),
                                        ("Normalized Contribution", fig_bucket_contribution)])
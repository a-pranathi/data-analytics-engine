'''
File: app_container.py
Author: Pranathi Ayyadevara
Description:
    Generic wrapper class for building charts and plots.
'''

import pandas as pd
from io import BytesIO
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import colormaps
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import networkx as nx


from common.constants import *

class ChartBuilder:
    def __init__(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x: str = None,
        y: str | list[str] = None,
        title: str = '',
        xlabel: str = None,
        ylabel: str = None,
        legend: bool = True,
        grid: bool = True,
        annotate_max: bool = False,
        stacked: bool = False,
        color: str | list[str] = None,
        annotations: list[str] = None,
        export: dict = None
    ):
        chart_type = chart_type.lower()
        if chart_type not in ChartType.ALL:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        self.df = df
        self.chart_type = chart_type
        self.x = x
        self.y = y
        self.title = title
        self.xlabel = xlabel or x
        self.ylabel = ylabel or (y if isinstance(y, str) else ", ".join(y or []))
        self.legend = legend
        self.grid = grid
        self.annotate_max = annotate_max
        self.stacked = stacked
        self.color = color
        self.annotations = annotations
        self.export = export or {}

    def render(self):
        fig, ax = plt.subplots(figsize=self.export.get('figsize', (10, 6)))

        if self.chart_type == ChartType.LINE:
            for col in self._y_list():
                ax.plot(self.df[self.x], self.df[col], label=col)
        elif self.chart_type == ChartType.BAR:
            if self.stacked:
                bottom = [0] * len(self.df)
                for col in self._y_list():
                    ax.bar(self.df[self.x], self.df[col], bottom=bottom, label=col)
                    bottom = [b + v for b, v in zip(bottom, self.df[col])]
            else:
                for col in self._y_list():
                    ax.bar(self.df[self.x], self.df[col], label=col)
        elif self.chart_type == ChartType.BARH:
            if self.stacked:
                left = [0] * len(self.df)
                for col in self._y_list():
                    ax.barh(self.df[self.y], self.df[col], left=left, label=col, color=self.color or None)
                    left = [l + v for l, v in zip(left, self.df[col])]
            else:
                # 🎨 Auto-color each bar if no color list is provided
                if self.color is None:
                    palette = colormaps.get_cmap('Set2')
                    bar_colors = [palette(i / len(self.df)) for i in range(len(self.df))]
                elif isinstance(self.color, list):
                    bar_colors = self.color
                else:
                    bar_colors = self.color  # single color fallback

                ax.barh(self.df[self.y], self.df[self.x], color=bar_colors, label=self.title or None)
                if self.annotations:
                    for i, (value, label) in enumerate(zip(self.df[self.x], self.annotations)):
                        ax.text(value * 0.01, i, label, va='center', ha='left', fontsize=9, color='white')
                ax.invert_yaxis()
                
        elif self.chart_type == ChartType.SCATTER:
            ax.scatter(self.df[self.x], self.df[self.y], color=self.color or 'teal', label=self.title or 'Data Points')
        elif self.chart_type == ChartType.PIE:
            ax.pie(self.df[self.y], labels=self.df[self.x], autopct='%1.1f%%')
        elif self.chart_type == ChartType.HIST:
            series = pd.to_numeric(self.df[self.y], errors='coerce').dropna()

            # Primary axis: histogram
            ax.hist(
                series,
                bins=self.export.get('bins', 50),
                color=self.color or 'skyblue',
                edgecolor='black',
                linewidth=0.5,
                alpha=0.6,
                label=self.export.get('hist_label', 'Histogram')
            )

            # Secondary axis: KDE
            ax2 = ax.twinx()
            sns.kdeplot(
                series,
                ax=ax2,
                color=self.export.get('kde_color', 'darkblue'),
                linewidth=self.export.get('kde_linewidth', 2.5),
                label=self.export.get('kde_label', 'KDE'),
                zorder=3
            )
            ax2.set_ylabel('Density')

            # Titles and labels
            ax.set_title(self.title, fontsize=14, pad=15)
            ax.set_xlabel(self.xlabel, fontsize=12)
            ax.set_ylabel(self.ylabel, fontsize=12)
            if self.grid:
                ax.grid(True, linestyle='--', alpha=0.5)

            # Combined legend using proxy handles
            if self.legend:
                hist_handle = Patch(facecolor=self.color or 'skyblue', edgecolor='black', alpha=0.6)
                kde_handle = Line2D([0], [0], color=self.export.get('kde_color', 'darkblue'),
                                    linewidth=self.export.get('kde_linewidth', 2.5))
                ax.legend([hist_handle, kde_handle],
                        [self.export.get('hist_label', 'Histogram'), self.export.get('kde_label', 'KDE')],
                        loc=self.export.get('legend_loc', 'upper right'))
        elif self.chart_type == ChartType.GROUPED_BAR:
            # Expect df with index = rows, columns = columns
            # Example: rows = years, columns = quarters

            # Column labels for x-axis (groups)
            col_labels = self.export.get("labels", list(self.df.columns))
            col_labels = [str(c) for c in col_labels]
            if len(col_labels) != len(self.df.columns):
                raise ValueError(f"labels length ({len(col_labels)}) must match number of columns ({len(self.df.columns)})")

            # Row labels for legend (series)
            row_labels = [str(r) for r in self.df.index.tolist()]

            # X positions: one group per column
            n_cols = len(self.df.columns)
            n_rows = len(row_labels)
            x_positions = np.arange(n_cols)
            width = 0.8 / max(n_rows, 1)  # total group width = 0.8

            # 🎨 Color handling
            if self.color is None:
                palette = colormaps.get_cmap('Blues')
                #bar_colors = [palette(i / max(n_rows, 1)) for i in range(n_rows)]
                bar_colors = [palette(0.3 + 0.7 * (i / (n_rows - 1))) for i in range(n_rows)]                
            elif isinstance(self.color, list):
                if len(self.color) < n_rows:
                    raise ValueError(f"color list length ({len(self.color)}) must be >= number of rows ({n_rows})")
                bar_colors = self.color[:n_rows]
            else:
                bar_colors = [self.color] * n_rows

            # Plot each row (series) across columns
            for i, row in enumerate(self.df.index):
                values = pd.to_numeric(self.df.loc[row], errors='coerce').to_numpy()
                offsets = x_positions + i * width
                bars = ax.bar(offsets, values, width, color=bar_colors[i], label=str(row))

                # Annotate each bar
                for bar, val in zip(bars, values):
                    if pd.notna(val):
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            float(val),
                            f"{val:,.0f}",
                            ha='center',
                            va='bottom',
                            fontsize=8
                        )

            # Center tick labels under groups
            ax.set_xticks(x_positions + width * (n_rows - 1) / 2)
            ax.set_xticklabels(col_labels)

            # --- Formatting ---
            ax.set_title(self.title or "", fontsize=14, pad=15)
            ax.set_xlabel(self.xlabel or "Columns", fontsize=12)
            ax.set_ylabel(self.ylabel or "Values", fontsize=12)
            if self.grid:
                ax.grid(True, linestyle='--', alpha=0.5)
            if self.legend:
                ax.legend()
            plt.xticks(rotation=45)

            # --- Generic y-axis tick extension (current max + 1 tick) ---
            max_val = np.nanmax(self.df.values)
            ax.set_ylim(0, max_val * 1.2)  # extend 10% above max
            ticks = ax.get_yticks()
            if ticks[-1] < max_val:
                step = ticks[1] - ticks[0]
                ax.set_yticks(np.append(ticks, ticks[-1] + step))

        # --- Generic formatting (exclude GROUPED_BAR) ---
        if self.chart_type not in {ChartType.PIE, ChartType.HIST, ChartType.GROUPED_BAR}:
            ax.set_title(self.title, fontsize=14, pad=15)
            ax.set_xlabel(self.xlabel, fontsize=12)
            ax.set_ylabel(self.ylabel, fontsize=12)
            if self.grid:
                ax.grid(True, linestyle='--', alpha=0.5)
            if self.legend:
                ax.legend()
            plt.xticks(rotation=45)

        if self.annotate_max and self.chart_type not in {ChartType.PIE, ChartType.HIST, ChartType.GROUPED_BAR}:
            y_data = self.df[self.y[0]] if isinstance(self.y, list) else self.df[self.y]
            max_idx = y_data.idxmax()
            ax.annotate(
                "Max",
                xy=(self.df[self.x][max_idx], y_data[max_idx]),
                xytext=(self.df[self.x][max_idx], y_data[max_idx] * 1.1),
                arrowprops=dict(facecolor='green', shrink=0.05),
                fontsize=10
            )

        if self.chart_type not in {ChartType.PIE, ChartType.HIST, ChartType.GROUPED_BAR}:
            ax.set_title(self.title, fontsize=14, pad=15)
            ax.set_xlabel(self.xlabel, fontsize=12)
            ax.set_ylabel(self.ylabel, fontsize=12)
            if self.grid:
                ax.grid(True, linestyle='--', alpha=0.5)
            if self.legend:
                ax.legend()
            
            plt.xticks(rotation=45)

        if self.annotate_max and self.chart_type not in {ChartType.PIE, ChartType.HIST, ChartType.GROUPED_BAR}:
            y_data = self.df[self.y[0]] if isinstance(self.y, list) else self.df[self.y]
            max_idx = y_data.idxmax()
            ax.annotate("Max",
                        xy=(self.df[self.x][max_idx], y_data[max_idx]),
                        xytext=(self.df[self.x][max_idx], y_data[max_idx] * 1.1),
                        arrowprops=dict(facecolor='green', shrink=0.05),
                        fontsize=10)

        fig.tight_layout()
        return fig

    def save(self, filename: str):
        fig = self.render()
        fig.savefig(
            filename,
            dpi=self.export.get('dpi', 300),
            format=self.export.get('format', 'png'),
            transparent=self.export.get('transparent', False),
            bbox_inches='tight'
        )

    def to_bytes(self):
        fig = self.render()
        buf = BytesIO()
        fig.savefig(
            buf,
            format=self.export.get('format', 'png'),
            dpi=self.export.get('dpi', 300),
            transparent=self.export.get('transparent', False),
            bbox_inches='tight'
        )
        buf.seek(0)
        return buf

    def _y_list(self):
        return self.y if isinstance(self.y, list) else [self.y]
    
    @staticmethod
    def plot_kde_comparison(series_list: list[dict],  # Each dict: {'series': pd.Series, 'label': str, 'color': str}
        title: str = '',
        xlabel: str = '',
        ylabel: str = 'Density',
        figsize: tuple = (10, 6),
        grid: bool = True,
        legend: bool = True
    ):
        fig, ax = plt.subplots(figsize=figsize)

        for item in series_list:
            try:
                sns.kdeplot(
                    item['series'],
                    label=item.get('label', 'Series'),
                    fill=True,
                    color=item.get('color', None),
                    ax=ax
                )
            except Exception as e:
                print(f"KDE plot failed for {item.get('label', 'Series')}: {e}")

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if grid:
            ax.grid(True, linestyle='--', alpha=0.5)
        if legend:
            ax.legend()
        fig.tight_layout()
        return fig
    
    @staticmethod
    def plot_bucket_contribution_with_efficiency(
        df,
        metrics,                         # e.g., ['Sales_Value', 'Realized_Margin']
        efficiency_pair=None,           # e.g., ('Sales_Value', 'Realized_Margin')
        bucket_spec=None,
        mode='normalized',              # 'normalized' or 'absolute'
        orientation='vertical',         # 'vertical' or 'horizontal'
        anchor_metric=None,
        title="Bucket Contribution with Efficiency"
    ):
        """
        Plots grouped bars for metrics across quantile buckets, with efficiency overlay.

        Bars:
            - normalized: % contribution to total
            - absolute: raw sums
        Efficiency:
            - computed from absolute sums: (margin / sales) * 100
            - filtered for stability: NaN if sales < 1e-6
            - plotted as line on secondary axis
        """

        # --- Bucket spec ---
        if bucket_spec is None:
            bucket_spec = [
                ("Top 0.1%", 0.999, 1.0),
                ("Top 0.9%", 0.99, 0.999),
                ("Top 5%", 0.95, 0.99),
                ("Middle 90%", 0.05, 0.95),
                ("Bottom 5%", 0.01, 0.05),
                ("Bottom 0.9%", 0.001, 0.01),
                ("Bottom 0.1%", 0.0, 0.001)
            ]

        if anchor_metric is None:
            anchor_metric = metrics[0]

        bucket_labels = [label for label, _, _ in bucket_spec]
        bucket_masks = []
        for _, q_low, q_high in bucket_spec:
            q_low_val = df[anchor_metric].quantile(q_low)
            q_high_val = df[anchor_metric].quantile(q_high)
            mask = (df[anchor_metric] >= q_low_val) & (df[anchor_metric] <= q_high_val)
            bucket_masks.append(mask)

        # --- Aggregate absolute sums ---
        results_abs = {metric: [] for metric in metrics}
        for mask in bucket_masks:
            for metric in metrics:
                results_abs[metric].append(df.loc[mask, metric].sum())

        # --- Normalize if needed ---
        if mode == 'normalized':
            results_bar = {}
            for metric in metrics:
                total = sum(results_abs[metric])
                results_bar[metric] = [(v / total * 100) if total != 0 else 0 for v in results_abs[metric]]
            bar_label = "Contribution (% of total)"
        else:
            results_bar = results_abs
            bar_label = "Impact (₹)"

        # --- Efficiency calculation with stability filter ---
        efficiency = None
        if efficiency_pair:
            sales_key, margin_key = efficiency_pair
            sales_vals = results_abs.get(sales_key)
            margin_vals = results_abs.get(margin_key)
            efficiency = []
            for s, m in zip(sales_vals, margin_vals):
                if abs(s) < 1e-6:
                    efficiency.append(np.nan)
                else:
                    efficiency.append((m / s) * 100)

        # --- Plotting ---
        fig, ax1 = plt.subplots(figsize=(12, 6))
        x = np.arange(len(bucket_labels))
        bar_width = min(0.25, 0.8 / len(metrics))

        # Plot bars
        for i, metric in enumerate(metrics):
            if orientation == 'horizontal':
                ax1.barh(x + i*bar_width, results_bar[metric], height=bar_width, label=metric)
            else:
                ax1.bar(x + i*bar_width, results_bar[metric], width=bar_width, label=metric)

        # Plot efficiency line
        if efficiency:
            if orientation == 'horizontal':
                ax2 = ax1.twiny()
                ax2.plot(efficiency, x + bar_width*(len(metrics)-1)/2, color='red', marker='o', label='Margin Efficiency (%)')
                ax2.set_xlabel("Margin Efficiency (%)")
            else:
                ax2 = ax1.twinx()
                ax2.plot(x + bar_width*(len(metrics)-1)/2, efficiency, color='red', marker='o', label='Margin Efficiency (%)')
                ax2.set_ylabel("Margin Efficiency (%)")

        # Axis labels
        if orientation == 'horizontal':
            ax1.set_yticks(x + bar_width*(len(metrics)-1)/2)
            ax1.set_yticklabels(bucket_labels)
            ax1.set_xlabel(bar_label)
        else:
            ax1.set_xticks(x + bar_width*(len(metrics)-1)/2)
            ax1.set_xticklabels(bucket_labels, rotation=45, ha='right')
            ax1.set_ylabel(bar_label)

        ax1.set_title(title)
        ax1.grid(True, axis='x' if orientation == 'horizontal' else 'y', linestyle='--', alpha=0.7)

        # Unified legend
        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels() if efficiency else ([], [])
        ax1.legend(handles1 + handles2, labels1 + labels2, loc='best')
        ax1.set_xlabel("SKU Segments by Sales Value Rank", fontsize=12)        
        ax1.set_ylabel("Normalized Contribution (% of Total Sales / Margin)", fontsize=12)        
        ax2.set_ylabel("Margin Efficiency (₹ Margin / ₹ Sales)", fontsize=12)

        plt.tight_layout()
        return plt
    
    @staticmethod
    def plot_heatmap(matrix, labels, time_period="month", cmap="Blues"):

        # --- Step 4: Plot with GridSpec for aligned colorbar ---
        annot_data = matrix.map(lambda x: "" if pd.isna(x) else f"{x:.0f}")
        vmin = np.nanmin(matrix.values)
        vmax = np.nanmax(matrix.values)

        fig = plt.figure(figsize=(12, 4))
        gs = gridspec.GridSpec(nrows=1, ncols=2, width_ratios=[20, 1], wspace=0.02)

        ax  = fig.add_subplot(gs[0])  # heatmap axis

        # Dynamically align colorbar height to heatmap grid
        n_rows = len(matrix.index)
        height = 0.1 + 0.2 * n_rows
        cax = fig.add_axes([0.91, 0.5 - height/2, 0.02, height])  # [left, bottom, width, height]

        sns.heatmap(
            matrix,
            ax=ax,
            cmap=cmap,
            linewidths=0.5,
            linecolor="white",
            square=True,
            cbar=True,
            cbar_ax=cax,
            cbar_kws={"label": f"Total Sales (₹)"},
            vmin=vmin,
            vmax=vmax,
            annot=annot_data,
            fmt=""
        )

        # Border around heatmap
        for _, spine in ax.spines.items():
            spine.set_visible(True)
            spine.set_linewidth(0.75)
            spine.set_color("black")

        period_name = {
            "month":"Monthly",
            "quarter":"Quarterly",
            "halfyear":"Half-yearly",
            "year":"Yearly"
        }[time_period]

        first_year = matrix.index.min()
        last_year = matrix.index.max()
        n_periods = matrix.columns.max()
        years = matrix.index.tolist()    
        
        ax.set_title(f"{period_name} Sales Heatmap ({first_year} – {last_year})", fontsize=14)
        ax.set_xlabel("Quarter" if time_period == "quarter" else time_period.capitalize())
        ax.set_ylabel("Year")
        ax.set_xticks(np.arange(0.5, n_periods + 0.5))
        ax.set_xticklabels(labels, rotation=0)
        ax.set_yticks(np.arange(0.5, len(years) + 0.5))
        ax.set_yticklabels(years, rotation=0)

        plt.subplots_adjust(left=0.06, right=0.88, top=0.90, bottom=0.15)

        return fig
    
    @staticmethod
    def plot_rules(rules: pd.DataFrame, stretch_x: float = 1.5, stretch_y: float = 0.7):
        """
        Plot two separate network diagrams:
        1. One-to-One rules (single antecedent → single consequent)
        2. Many-to-One rules (multi antecedent → single consequent)

        - Layout: kamada_kawai_layout with optional horizontal/vertical stretch
        - Lift colorbar (vertical, right)
        - Confidence shown via edge width + legend (bottom center)
        - Shape legend text (right margin)
        """

        def to_tuple(x):
            return tuple(sorted(map(str, x)))

        def width_legend_handles(confidences):
            """Create sample line handles for min/mid/max confidence widths."""
            if not confidences:
                return []
            cmin, cmax = min(confidences), max(confidences)
            cmed = sorted(confidences)[len(confidences)//2]

            def w(c): return max(0.8, c*5.0)
            return [
                Line2D([0],[0], color='gray', linewidth=w(cmin), label=f"Conf min: {cmin:.2f}"),
                Line2D([0],[0], color='gray', linewidth=w(cmed), label=f"Conf mid: {cmed:.2f}"),
                Line2D([0],[0], color='gray', linewidth=w(cmax), label=f"Conf max: {cmax:.2f}")
            ]

        def draw_graph(subset, title, many_to_one=False):
            if subset.empty:
                print(f"{title}: No rules to display.")
                return

            G = nx.DiGraph()
            for _, row in subset.iterrows():
                ant = to_tuple(row['antecedents'])
                cons = to_tuple(row['consequents'])
                conf, lift = float(row['confidence']), float(row['lift'])
                if many_to_one:
                    G.add_node(ant, shape='square' if len(ant)>1 else 'circle')
                else:
                    G.add_node(ant, shape='circle')
                G.add_node(cons, shape='circle')
                G.add_edge(ant, cons, confidence=conf, lift=lift)

            # Layout with stretch
            pos = nx.kamada_kawai_layout(G)

            for k,(x,y) in pos.items():
                pos[k] = (x*stretch_x, y*stretch_y)

            if many_to_one:
                cons_groups = {}
                for u,v in G.edges():
                    cons_groups.setdefault(v, []).append(u)

                for cons, ants in cons_groups.items():
                    if len(ants) > 1 and cons in pos:
                        cx, cy = pos[cons]
                        r = 0.8  # radius of orbit
                        for i, ant in enumerate(ants):
                            angle = 2*np.pi*i/len(ants)
                            pos[ant] = (cx + r*np.cos(angle), cy + r*np.sin(angle))                
            
            circle_nodes = [n for n,d in G.nodes(data=True) if d['shape']=='circle']
            square_nodes = [n for n,d in G.nodes(data=True) if d['shape']=='square']

            fig, ax = plt.subplots(figsize=(11,8))
            nx.draw_networkx_nodes(G, pos, nodelist=circle_nodes,
                                node_shape='o', node_color='lightblue', node_size=1800, ax=ax)
            if square_nodes:
                nx.draw_networkx_nodes(G, pos, nodelist=square_nodes,
                                    node_shape='s', node_color='lightgreen', node_size=2200, ax=ax)

            edges = list(G.edges(data=True))
            lifts = [d['lift'] for (_,_,d) in edges]
            confidences = [d['confidence'] for (_,_,d) in edges]
            widths = [max(0.8, c*5.0) for c in confidences]

            edge_collection = nx.draw_networkx_edges(
                G, pos, edgelist=edges,
                width=widths,
                edge_color=lifts,
                edge_cmap=plt.cm.plasma,
                edge_vmin=min(lifts),
                edge_vmax=max(lifts),
                arrows=False,
                ax=ax
            )
            if isinstance(edge_collection, list):
                edge_collection = edge_collection[0]

            nx.draw_networkx_labels(G, pos, {n:', '.join(n) for n in G.nodes()}, font_size=9, ax=ax)

            # Lift colorbar (vertical, right)
            cbar = fig.colorbar(edge_collection, ax=ax)
            cbar.set_label("Lift (scale)")

            # Confidence width legend (bottom center)
            conf_handles = width_legend_handles(confidences)
            if conf_handles:
                ax.legend(handles=conf_handles,
                        loc='upper center',
                        bbox_to_anchor=(0.5, -0.05),
                        ncol=3,
                        framealpha=0.8,
                        title="Edge width = Confidence")

            # Shape legend text (right margin)
            ax.text(1.25, 0.5,
                    "Legend:\nCircle = single product\nSquare = product set\nEdge color = Lift",
                    transform=ax.transAxes,
                    fontsize=9, ha='left', va='center',
                    bbox=dict(facecolor='white', alpha=0.7))

            ax.set_title(title)
            ax.axis('off')
            plt.subplots_adjust(bottom=0.25, right=0.8)
            plt.tight_layout()
            return fig

        # Split rules
        one_to_one = rules[(rules['antecedents'].apply(len)==1) & (rules['consequents'].apply(len)==1)]
        many_to_one = rules[(rules['antecedents'].apply(len)>1) & (rules['consequents'].apply(len)==1)]
        many_to_one = many_to_one.nlargest(10, 'lift')  # <-- add this line        

        fig_one_to_one = draw_graph(one_to_one, "One-to-One Rules Network", many_to_one=False)
        fig_may_to_one = draw_graph(many_to_one, "Many-to-One Rules Network", many_to_one=True)
        return fig_one_to_one, fig_may_to_one

    @staticmethod
    def plot_sku_velocity(df):
        """
        Compute SKU velocity and classify SKUs into fast, slow, or deadstock.
        Overlay realized margin for diagnostic clarity.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe with at least ['SKU','Sales_Qty','Realized_Margin'] columns.
        period_days : int, optional
            Time period length (default=30 days).
        fast_threshold : float, optional
            Velocity threshold above which SKUs are considered fast-moving.
        slow_threshold : float, optional
            Velocity threshold below which SKUs are considered deadstock.

        Returns
        -------
        pd.DataFrame
            Original dataframe with added 'Velocity' and 'Classification' columns.
        """
        period_days = 913
        fast_threshold = 0.3
        slow_threshold = 0.01

        # Compute velocity (units sold per day)
        df['Velocity'] = df['Sales_Qty'] / period_days

        # Classify SKUs
        def classify(v):
            if v > fast_threshold:
                return 'Fast-moving'
            elif v >= slow_threshold:
                return 'Slow-moving'
            else:
                return 'Deadstock'

        df['Classification'] = df['Velocity'].apply(classify)

        # Plot scatter: Velocity vs Realized Margin
        fig = plt.figure(figsize=(12,6))
        colors = {'Fast-moving':'green','Slow-moving':'orange','Deadstock':'red'}
        df = df.fillna(0)

        for c in df['Classification'].unique():
            subset = df[df['Classification']==c]
            plt.scatter(subset['Velocity'], subset['Realized_Margin'],
                        c=colors[c], label=c, s=15, alpha=0.7, edgecolors='none')

        plt.xlabel("SKU Velocity (Units per Day)")
        plt.ylabel("Realized Margin (₹)")
        plt.title("SKU Velocity vs Realized Margin")
        plt.legend()
        plt.grid(True)

        return fig    
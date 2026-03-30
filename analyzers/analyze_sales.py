'''
File: analyze_sales.py
Author: Pranathi Ayyadevara
Description:
    	Focuses on sales velocity, quantity, and value trends across SKUs.
        Flags fast movers, slow sellers, and seasonal shifts in demand.
'''

from analyzers.analyze import Analyze
from common.constants import *
from common.chart_builder import ChartBuilder

class AnalyzeSales(Analyze):
    def __init__(self, app_container):
        super().__init__(app_container)
        self.analyzer_type = AnalyzerType.SALES
        self.output_file = self.app_container.config.get_analyzer_output_file(self.analyzer_type)

    def unit_price_distribution(self):
        df = self.app_container.dataset.get_data(DataTypes.SALES_DATA)

        sales_df = df[df['Sales Qty'] > 0].copy()
        returns_df = df[df['Sales Qty'] < 0].copy()

        fig = ChartBuilder.plot_kde_comparison(
            series_list=[
                {'series': sales_df['Unit Price'], 'label': 'Sales', 'color': 'blue'},
                {'series': returns_df['Unit Price'], 'label': 'Returns', 'color': 'red'}
            ],
            title='Unit Price Distribution: Sales vs Returns',
            xlabel='Unit Price'
        )
        return fig
    
    def discount_distribution(self):
        df = self.app_container.dataset.get_data(DataTypes.SALES_DATA)
        discounted_sales_df = df[(df['Sales Qty'] > 0) & (df['Effective Disc %'] > 0)]

        chart = ChartBuilder(
            df=discounted_sales_df,
            chart_type=ChartType.HIST,
            y='Effective Disc %',
            title='Distribution of Effective Discount %',
            xlabel='Effective Discount %',
            ylabel='Number of Sales',
            color='skyblue',
            legend=True,
            grid=True,
            export={
                'figsize': (10, 6),
                'bins': 50,
                'kde': True,
                'kde_color': 'darkblue',
                'kde_linewidth': 1,
                'hist_label': 'Histogram',
                'kde_label': 'KDE',
                'legend_loc': 'upper right'
            }
        )
        return chart.render()


    def analyze_sales(self):
        df = self.app_container.dataset.get_data(DataTypes.SALES_DATA)
        free_items_df = df[(df['Sales Qty'] > 0) & ( (df['Net Amount'].abs() < 10) | (df['Effective Disc %'] > 99))]
        return free_items_df

    def plot_sales_month(self):
        time_period="month"
        matrix, labels = self.app_container.dataset.get_sales_aggregate(time_period)
        fig = ChartBuilder.plot_heatmap(matrix, labels, time_period=time_period, cmap="Blues")
        return fig

    def plot_sales_quarter(self):
        time_period="quarter"
        matrix, labels = self.app_container.dataset.get_sales_aggregate(time_period)
        first_year = matrix.index.min()
        last_year = matrix.index.max()

        fig = ChartBuilder(
            df=matrix,
            chart_type=ChartType.GROUPED_BAR,
            title=f"Quarterly Sales - ({first_year}-{last_year})",
            xlabel="Quarter",
            ylabel="Sales (₹)",
            legend=True,
            export={"labels": labels}
        ).render()

        return fig
    
    def process(self):
        print("Performing Sales Analysis...")    

        free_items_df = self.analyze_sales()

        fig_unit_price_distribution = self.unit_price_distribution()
        fig_discount_distribution = self.discount_distribution()
        fig_monthly_sales = self.plot_sales_month()
        fig_quarterly_sales = self.plot_sales_quarter()
        df = self.app_container.dataset.get_margin_data()
        fig_sku_velocity = ChartBuilder.plot_sku_velocity(df)
        fig_sku_velocity.show()

        self.save_report(data=[("Free Items", free_items_df),],
                               figures=[("Unit Price Distribution", fig_unit_price_distribution),
                                        ("Discount Distribution", fig_discount_distribution),
                                        ("Monthly Sales", fig_monthly_sales),
                                        ("Quarterly Sales", fig_quarterly_sales),
                                        ("SKU Velocity", fig_sku_velocity)])
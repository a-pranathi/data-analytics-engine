'''
File: analyze_statistics.py
Author: Pranathi Ayyadevara
Description:
    Computes high-level summary metrics across the dataset, including SKU counts, value distributions, and basic aggregates.
    Used to establish baseline diagnostics and validate data integrity.
'''

import pandas as pd
from analyzers.analyze import Analyze
from common.constants import *

class AnalyzeStatistics(Analyze):
    def __init__(self, app_container):
        super().__init__(app_container)
        self.analyzer_type = AnalyzerType.STATISTICS
        self.output_file = self.app_container.config.get_analyzer_output_file(self.analyzer_type)

    def compute_basic_stats(self):
        rows = []
        for datatype in DataTypes:
            df = self.app_container.dataset.get_data(datatype)
            numeric_cols = df.select_dtypes(include='number').columns

            for col in numeric_cols:
                mean_val = df[col].mean()
                median_val = df[col].median()
                mode_series = df[col].mode()
                mode_val = mode_series.iloc[0] if not mode_series.empty else None

                rows.append({
                    "Dataset": datatype.name,
                    "Column": col,
                    "Mean": round(mean_val, 2) if pd.notnull(mean_val) else None,
                    "Median": round(median_val, 2) if pd.notnull(median_val) else None,
                    "Mode": round(mode_val, 2) if pd.notnull(mode_val) else None
                })

        return pd.DataFrame(rows)

    def __get_descriptive_statistics(self, df, dfname, selected_columns):
        stats_df = df[selected_columns].describe().transpose()
        stats_df.index.name = 'metric'
        stats_df['dataset'] = dfname
        sum_values = df[selected_columns].sum(numeric_only=True)
        stats_df['sum'] = sum_values
        stats_df = stats_df.reset_index()
        stats_df = stats_df[['dataset', 'metric', 'count', 'sum'] +
                            [col for col in stats_df.columns if col not in ['dataset', 'metric', 'count', 'sum']]]
        return stats_df
        
    def compute_descriptive_statistics(self):

        combined_stats = pd.DataFrame()

        # description stats for opening data
        df = self.app_container.dataset.get_data(DataTypes.OPENING_STOCK)
        selected_columns = df.select_dtypes(include='number').columns.tolist()
        stats = self.__get_descriptive_statistics(df, "Opening Stock", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])

        # description stats for closing data
        df = self.app_container.dataset.get_data(DataTypes.CLOSING_STOCK)
        selected_columns = df.select_dtypes(include='number').columns.tolist()
        stats = self.__get_descriptive_statistics(df, "Closing Stock", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])

        # description stats for purchase data
        df = self.app_container.dataset.get_data(DataTypes.PURCHASE_DATA)
        selected_columns = df.select_dtypes(include='number').columns.tolist()
        stats = self.__get_descriptive_statistics(df, "Purchase", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])

        # description stats for purchase return data
        df = self.app_container.dataset.get_data(DataTypes.PURCHASE_RETURN_DATA)
        selected_columns = df.select_dtypes(include='number').columns.tolist()
        stats = self.__get_descriptive_statistics(df, "Purchase Returns", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])

        # description stats for stock verification data
        df = self.app_container.dataset.get_data(DataTypes.STOCK_VERIFICATION_DATA)
        selected_columns = df.select_dtypes(include='number').columns.tolist()
        stats = self.__get_descriptive_statistics(df, "Stock Verification", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])

        # description stats for sales data
        df = self.app_container.dataset.get_data(DataTypes.SALES_DATA)

        # separate sales and returns
        sales_df = df[df['Sales Qty'] > 0].copy()
        returns_df = df[df['Sales Qty'] < 0].copy()

        # descriptive metrics for sales and returns
        selected_columns = ['Sales Qty', 'Retail Price', 'Retail Value', 'Bill Level Disc. Amt.',
                         'Net Amount', 'Unit Price', 'Effective Disc %']

        stats = self.__get_descriptive_statistics(sales_df, "Sales", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])

        stats = self.__get_descriptive_statistics(returns_df, "Returns", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])


        # description stats for expense data
        df = self.app_container.dataset.get_data(DataTypes.EXPENSE_DATA)
        selected_columns = df.select_dtypes(include='number').columns.tolist()
        stats = self.__get_descriptive_statistics(df, "Monthly Expense", selected_columns)
        combined_stats = pd.concat([combined_stats, stats])

        self.app_container.dataset.set_statistics(combined_stats)
        return combined_stats
    
    def compute_descriptive_statistics_old(self):

        # description stats for sales data
        df = self.app_container.dataset.get_data(DataTypes.SALES_DATA)
        
        # separate sales and returns
        sales_df = df[df['Sales Qty'] > 0].copy()
        returns_df = df[df['Sales Qty'] < 0].copy()

        # descriptive statistics
        selected_cols = ['Sales Qty', 'Retail Price', 'Retail Value', 'Bill Level Disc. Amt.',
                         'Net Amount', 'Unit Price', 'Effective Disc %']

        stats_sales = sales_df[selected_cols].describe().transpose()
        stats_sales.index.name = 'Metric'
        stats_sales['Dataset'] = 'Sales'
        sum_values = sales_df[selected_cols].sum(numeric_only=True)
        stats_sales['sum'] = sum_values
        stats_sales = stats_sales.reset_index()

        stats_sales = stats_sales[['Dataset', 'Metric'] + [col for col in stats_sales.columns if col not in ['Dataset', 'Metric']]]

        stats_returns = returns_df[selected_cols].describe().transpose()
        stats_returns.index.name = 'Metric'
        stats_returns['Dataset'] = 'Returns'
        sum_values = returns_df[selected_cols].sum(numeric_only=True)
        stats_returns['sum'] = sum_values
        stats_returns = stats_returns.reset_index()        

        stats_returns = stats_returns[['Dataset', 'Metric'] + [col for col in stats_returns.columns if col not in ['Dataset', 'Metric']]]

        df = self.app_container.dataset.get_data(DataTypes.OPENING_STOCK)
        stats_opening_stock = df.describe().transpose()
        stats_opening_stock.index.name = 'Metric'
        stats_opening_stock['Dataset'] = 'Opening Stock'
        sum_values = df.sum(numeric_only=True)
        stats_opening_stock['sum'] = sum_values
        stats_opening_stock = stats_opening_stock.reset_index()        

        stats_opening_stock = stats_opening_stock[['Dataset', 'Metric'] + [col for col in stats_opening_stock.columns if col not in ['Dataset', 'Metric']]]

        df = self.app_container.dataset.get_data(DataTypes.CLOSING_STOCK)
        stats_closing_stock = df.describe().transpose()
        stats_closing_stock.index.name = 'Metric'
        stats_closing_stock['Dataset'] = 'Closing Stock'
        sum_values = df.sum(numeric_only=True)     
        stats_closing_stock['sum'] = sum_values
        stats_closing_stock = stats_closing_stock.reset_index()        

        stats_closing_stock = stats_closing_stock[['Dataset', 'Metric'] + [col for col in stats_closing_stock.columns if col not in ['Dataset', 'Metric']]]


        combined_stats = pd.concat([stats_sales, stats_returns, stats_opening_stock, stats_closing_stock])
        print(combined_stats)
        return combined_stats

    def profit_calculation(self):
        df = self.app_container.dataset.get_statistics()
        
        sales_net = df[(df['dataset'] == 'Sales') & (df['metric'] == 'Net Amount')]['sum'].values[0]
        returns_net = df[(df['dataset'] == 'Returns') & (df['metric'] == 'Net Amount')]['sum'].values[0]
        opening_stock_balance = df[(df['dataset'] == 'Opening Stock') & (df['metric'] == 'Closing Bal.Val')]['sum'].values[0]
        closing_stock_balance = df[(df['dataset'] == 'Closing Stock') & (df['metric'] == 'Closing Bal.Val')]['sum'].values[0]
        purchase_net = df[(df['dataset'] == 'Purchase') & (df['metric'] == 'Net Amount')]['sum'].values[0]
        purchase_return_net = df[(df['dataset'] == 'Purchase Returns') & (df['metric'] == 'Net Amount')]['sum'].values[0]
        expense = df[(df['dataset'] == 'Monthly Expense') & (df['metric'] == 'expense')]['sum'].values[0]

        print("Profit=(Sales+Customer Returns+Closing Stock+Returned Stock)−(Opening Stock+Purchases+Expenses)")
        print("Sum values for sales_net, returns_net, opening_stock_balance, closing_stock_balance, purchase_net, purchase_return_net, expense")
        print(f"{sales_net}, {returns_net}, {opening_stock_balance}, {closing_stock_balance}, {purchase_net}, {purchase_return_net}, {expense}")
        profit = ((sales_net + returns_net + closing_stock_balance + purchase_return_net) - 
                (opening_stock_balance + purchase_net + expense))
        print(f"Profit/loss: {profit}")
            
    def process(self):
        print("Computing Statistics...")        
        result = self.compute_descriptive_statistics()
        self.save_report(result)
'''
File: dataset.py
Author: Pranathi Ayyadevara
Description:
    Singleton class that stores all data.
    Cache of all input data, cleaned and ready to use. Also caches computed columns and consolidated datasets.
'''

import pandas as pd
from common.constants import *
import numpy as np
class Dataset():
    _instance = None
    _initialized = False

    def __new__(cls, app_container=None):
        if not cls._instance:
            cls._instance = super(Dataset, cls).__new__(cls)
        return cls._instance

    def __init__(self, app_container=None):
        if not self._initialized:
            print("Preparing datasets...")
            self.app_container = app_container
            self.__data = {}
            self.__margin_data = None
            self._statistics = None
            self._sales_aggregate = None
            self.__date_format = "%d/%m/%Y %I:%M:%S %p"
            pd.set_option('future.no_silent_downcasting', True)
            self.__load_data()
            self.__preprocess_data()
            self.__compute_data()      
            self.__class__._initialized = True

    def __load_data(self):
        config = self.app_container.config
        for key, item in config.get_data_files().items():
            filepath = config.input_path + item
            self.__data[key] = pd.read_csv(filepath, low_memory=False, keep_default_na=False, na_values=[""])
        pd.set_option('display.float_format', '{:.2f}'.format)

    def __preprocess_data(self):
        # remove grnd total column in opening stock
        df = self.__data[DataTypes.OPENING_STOCK]
        df.drop(df[df['Item Description'] == 'Grand Total : '].index, inplace=True)

        # set the numeric columns for opening stock
        numeric_cols = ['Cost Price', 'Retail Price', 'Closing Bal.Qty', 'Closing Bal.Val']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # update opening stock dataframe for future use
        self.__data[DataTypes.OPENING_STOCK] = df

        # remove grnd total column in closing stock
        df = self.__data[DataTypes.CLOSING_STOCK]
        df.drop(df[df['Item Description'] == 'Grand Total : '].index, inplace=True)

        # set the numeric columns for closing stock
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # update closing stock dataframe for future use
        self.__data[DataTypes.CLOSING_STOCK] = df

        # remove grnd total column in purchase data
        df = self.__data[DataTypes.PURCHASE_DATA]
        df.drop(df[df['Particulars'] == 'Grand Total'].index, inplace=True)

        # compute unit price for purchase data
        df['Unit Price'] = df['Net Amount'] / df['Purchase Qty']
            
        # set the numeric columns for purchase 
        numeric_cols = ["Retail Price","Purchase Qty","Net Amount"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # set remarks column as string
        df = df.astype({'Alt. Purchase Qty': str, 'Remarks': str})

        # update purchase dataframe for future use
        self.__data[DataTypes.PURCHASE_DATA] = df

        # remove grnd total column in purchase return data
        df = self.__data[DataTypes.PURCHASE_RETURN_DATA]
        df.drop(df[df['Particulars'] == 'Grand Total'].index, inplace=True)

        # compute unit price for purchase return data
        df['Unit Price'] = df['Net Amount'] / df['Purch. Return Qty']

        # set the numeric columns for purchase return
        numeric_cols = ["Retail Price","Purch. Return Qty","Net Amount"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df = df.astype({'Remarks': str})

        # update purchase return dataframe for future use
        self.__data[DataTypes.PURCHASE_RETURN_DATA] = df

        # remove the grand total line from the sales data
        df = self.__data[DataTypes.SALES_DATA]
        df.drop(df[df['Voucher No'] == 'Grand Total : '].index, inplace=True)

        # set the numeric columns for sales data
        numeric_cols = ['Sales Qty', 'Bill Level Disc. Amt.', 'Bill Level Disc. Per.',
                        'Net Amount', 'Retail Price', 'Closing Stock']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')        
        df["Voucher Date"] = pd.to_datetime(df["Voucher Date"], format=self.__date_format, errors="coerce")
        df["Voucher Key"] = df["Voucher No"].astype(str) + "_" + df["Voucher Date"].dt.year.astype(str)

        # correct the product name
        product_map_df = self.__data[DataTypes.PRODUCT_MAPPING_DATA]

        product_map = dict(zip(
                product_map_df["Product"].str.upper().str.strip(),
                product_map_df["Corrected Product"].str.upper().str.strip()
            ))        
        # Normalize and substitute directly
        df["Product"] = (
            df["Product"].str.upper().str.strip()
            .map(product_map)
            .fillna(df["Product"].str.upper().str.strip())
        )
        #  compute useful columns
        df['Retail Value'] = df['Sales Qty'] * df['Retail Price']
        df['Unit Price'] = df['Net Amount'] / df['Sales Qty']
        df['Effective Disc %'] = (df['Bill Level Disc. Amt.'] / df['Retail Value']) * 100

        #  update sales data for future use
        self.__data[DataTypes.SALES_DATA] = df

        # no changes to expense data as it is manual data entry

        # remove grnd total column from stock verification data
        df = self.__data[DataTypes.STOCK_VERIFICATION_DATA]
        df.drop(df.index[-1], inplace=True)        

        # set the numeric columns for opening stock
        numeric_cols = ['Retail Price', 'Book Stock', 'Trans Qty. (Phy Stk Qty)', 'Difference Qty', 'Physical Stock Value', 'Difference Value']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # set remarks column as string
        df = df.astype({'Difference Value': str, 'Remarks': str})

        # update opening stock dataframe for future use
        self.__data[DataTypes.STOCK_VERIFICATION_DATA] = df

    def __compute_data(self):
        opening_df = self.__data[DataTypes.OPENING_STOCK] 
        closing_df = self.__data[DataTypes.CLOSING_STOCK]
        sales_df = self.__data[DataTypes.SALES_DATA]
        purchase_df = self.__data[DataTypes.PURCHASE_DATA]
        purchase_return_df = self.__data[DataTypes.PURCHASE_RETURN_DATA]

        # Step 1: Prepare Opening Stock
        opening_df = opening_df.rename(columns={
            'Stock No': 'SKU',
            'Closing Bal.Qty': 'Opening_Qty',
            'Cost Price': 'Opening_Cost',
            'Retail Price': 'Opening_Retail_Price'
        })

        opening_summary = (
            opening_df.drop(columns='SKU')  # exclude grouping column to avoid warning
            .groupby(opening_df['SKU'])     # group by SKU explicitly
            .apply(lambda x: pd.Series({
                'Opening_Qty': x['Opening_Qty'].sum(),
                'Opening_Cost': (x['Opening_Qty'] * x['Opening_Cost']).sum() / x['Opening_Qty'].sum(),
                'Opening_Retail_Price': (x['Opening_Qty'] * x['Opening_Retail_Price']).sum() / x['Opening_Qty'].sum()
            }))
            .reset_index()
        )

        # Step 2: Prepare Closing Stock
        closing_df = closing_df.rename(columns={
            'Stock No': 'SKU',
            'Closing Bal.Qty': 'Closing_Qty',
            'Cost Price': 'Closing_Cost',
            'Retail Price': 'Closing_Retail_Price'
        })
        
        closing_summary = (
            closing_df.drop(columns='SKU')  # exclude grouping column
            .groupby(closing_df['SKU'])     # group by SKU explicitly
            .apply(lambda x: pd.Series({
                'Closing_Qty': x['Closing_Qty'].sum(),
                'Closing_Cost': (x['Closing_Qty'] * x['Closing_Cost']).sum() / x['Closing_Qty'].sum(),
                'Closing_Retail_Price': (x['Closing_Qty'] * x['Closing_Retail_Price']).sum() / x['Closing_Qty'].sum()
            }))
            .reset_index()
        )

        # Step 3: Aggregate Purchase Data
        purchase_df = purchase_df.rename(columns={'Stock No': 'SKU'})

        purchase_summary = purchase_df.groupby('SKU').agg({
            'Purchase Qty': 'sum',
            'Net Amount': 'sum'
        }).rename(columns={'Purchase Qty': 'Purchase_Qty', 'Net Amount': 'Purchase_Value'})


        purchase_summary = (purchase_df.drop(columns='SKU')  # exclude grouping column
            .groupby(purchase_df['SKU'])     # group by SKU explicitly
            .apply(lambda x: pd.Series({
                'Purchase_Qty': x['Purchase Qty'].sum(),
                'Purchase_Value': x['Net Amount'].sum(),
                'Purchase_Retail_Price': (
                    (x['Purchase Qty'] * x['Retail Price']).sum() / x['Purchase Qty'].sum()
                    if x['Purchase Qty'].sum() != 0 else np.nan
                )
            }))
            .reset_index()
        )

        # Step 4: Aggregate Purchase Returns
        purchase_return_df = purchase_return_df.rename(columns={'Stock No': 'SKU'})
        purchase_return_summary = purchase_return_df.groupby('SKU').agg({
            'Purch. Return Qty': 'sum',
            'Net Amount': 'sum'
        }).rename(columns={'Purch. Return Qty': 'Return_Qty', 'Net Amount': 'Return_Value'})

        # Step 5: Aggregate Sales Data (sales + returns)
        sales_df = sales_df.rename(columns={'Stock No': 'SKU'})
        sales_df['Net_Qty'] = sales_df['Sales Qty']
        sales_df['Net_Value'] = sales_df['Net Amount']

        sales_summary = sales_df.groupby('SKU').agg({
            'Net_Qty': 'sum',
            'Net_Value': 'sum'
        }).rename(columns={'Net_Qty': 'Sales_Qty', 'Net_Value': 'Sales_Value'})

        # Step 6: Merge All Sources
        df = opening_summary.merge(closing_summary, on='SKU', how='outer')
        df = df.merge(sales_summary, on='SKU', how='outer')
        df = df.merge(purchase_summary, on='SKU', how='outer')
        df = df.merge(purchase_return_summary, on='SKU', how='outer')

        # Step 7: Fill NaNs with 0
        df.fillna({
            'Opening_Qty': 0,
            'Closing_Qty': 0,
            'Sales_Qty': 0,
            'Sales_Value': 0,
            'Purchase_Qty': 0,
            'Purchase_Value': 0,
            'Return_Qty': 0,
            'Return_Value': 0
        }, inplace=True)


        # Step 8: Compute Net Purchase Cost
        df['Net_Purchase_Qty'] = df['Purchase_Qty'] - df['Return_Qty']
        df['Net_Purchase_Cost'] = df['Purchase_Value'] - df['Return_Value']

        # Step 9: Compute Unit Cost
        df['Unit_Cost'] = df['Net_Purchase_Cost'] / df['Net_Purchase_Qty'].replace(0, pd.NA)
        df['Unit_Cost'] = pd.to_numeric(df['Unit_Cost'], errors='coerce')        
        df['Unit_Cost'] = df['Unit_Cost'].fillna(df['Opening_Cost'])        

        # Step 10: Compute Unit Selling Price
        df['Unit_Selling_Price'] = df['Sales_Value'] / df['Sales_Qty'].replace(0, pd.NA)

        # Step 11: Realized Margin
        df['Realized_Margin'] = (df['Unit_Selling_Price'] - df['Unit_Cost']) * df['Sales_Qty']

        # Step 12: Unrealized Margin
        #df['Retail_Price'] = df['Closing_Retail_Price'].combine_first(df['Opening_Retail_Price'])
        df['Retail_Price'] = (df['Closing_Retail_Price'].combine_first(df['Purchase_Retail_Price']).combine_first(df['Opening_Retail_Price']))
        df['Unrealized_Margin'] = df['Closing_Qty'] * (df['Retail_Price'] - df['Closing_Cost'])

        # Step 13: add brand and product for SKU identification 
        sku_meta = pd.concat([opening_df[['SKU', 'Brand', 'Product']],
                              purchase_df[['SKU', 'Brand', 'Product']],
                              sales_df[['SKU', 'Brand', 'Product']]])
        sku_meta = sku_meta.groupby('SKU').agg({'Brand': 'first', 'Product': 'first'}).reset_index()        
        output = df.merge(sku_meta, on='SKU', how='left')

        # Step 14: Final Output
        output = output[['SKU', 'Brand', 'Product'] + [col for col in output.columns if col not in ['SKU', 'Brand', 'Product']]]

        # Step 15: Save the result for future use
        self.__margin_data = output

    def get_data(self, datatype):
        return self.__data[datatype]
    
    def get_all_data(self):
        return self.__data
    
    def set_statistics(self, statistics):
        self._statistics = statistics

    def get_statistics(self):
        return self._statistics
    
    def get_margin_data(self):
        return self.__margin_data
    
    def get_aggregate_column(self, datatype, column):
        return self.__data[datatype][column].sum()
    
    def get_sales_aggregate(self, time_period="month"):
        df = self.__data[DataTypes.SALES_DATA]
        date_col="Voucher Date"
        value_col="Net Amount"
        df = df.dropna(subset=[date_col, value_col])

        dt = df[date_col]
        first_date = dt.min()
        last_date  = dt.max()

        if pd.isna(first_date) or pd.isna(last_date):
            raise ValueError("No valid dates found in dataset")

        first_year = first_date.year
        last_year  = last_date.year

        # --- Step 1: Create buckets (calendar-based) ---
        df["Year"] = dt.dt.year

        if time_period == "month":
            df["Period"] = dt.dt.month
            labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            n_periods = 12
            first_period = first_date.month
            last_period  = last_date.month

        elif time_period == "quarter":
            df["Period"] = dt.dt.quarter
            labels = ["Q1","Q2","Q3","Q4"]
            n_periods = 4
            first_period = pd.Period(first_date, freq="Q").quarter
            last_period  = pd.Period(last_date,  freq="Q").quarter

        elif time_period == "halfyear":
            df["Period"] = np.where(dt.dt.month <= 6, 1, 2)
            labels = ["H1","H2"]
            n_periods = 2
            first_period = 1 if first_date.month <= 6 else 2
            last_period  = 1 if last_date.month  <= 6 else 2

        elif time_period == "year":
            df["Period"] = 1
            labels = ["Year"]
            n_periods = 1
            first_period = 1
            last_period  = 1

        else:
            raise ValueError("time_period must be one of: 'month', 'quarter', 'halfyear', 'year'")

        years   = list(range(first_year, last_year + 1))
        periods = list(range(1, n_periods + 1))

        # --- Step 2: Initialize all buckets to NaN ---
        matrix = pd.DataFrame(np.nan, index=years, columns=periods, dtype=float)

        # --- Step 3: Aggregate and assign values ---
        agg = df.groupby(["Year", "Period"], dropna=True)[value_col].sum()

        for (y, p), val in agg.items():
            if y in matrix.index and p in matrix.columns:
                matrix.loc[y, p] = float(val)

        # Strict boundary blanking
        if first_year in matrix.index:
            for p in periods:
                if p < first_period:
                    matrix.loc[first_year, p] = np.nan

        if last_year in matrix.index:
            for p in periods:
                if p > last_period:
                    matrix.loc[last_year, p] = np.nan

        return matrix, labels
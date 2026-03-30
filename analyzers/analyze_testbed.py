'''
File: analyze_testbed.py
Author: Pranathi Ayyadevara
Description:
    	Sandbox module for experimental diagnostics, prototype logic, and 
        validation of new analytical frameworks before production rollout.
'''

import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import zscore
import seaborn as sns
from common.constants import *
from analyzers.analyze import Analyze
import plotly.graph_objects as go
import numpy as np
from rapidfuzz import process, fuzz
import re
import pandas as pd
from rapidfuzz import process, fuzz
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
import re
import pandas as pd
import re
import pandas as pd
import phonetics


class AnalyzeTestBed(Analyze):
    def __init__(self, app_container):
        super().__init__(app_container)
        self.analyzer_type = AnalyzerType.TEST_BED
        self.output_file = self.app_container.config.get_analyzer_output_file(self.analyzer_type)


    def auto_clean_products(self, df, product_col="Product", count_col="Count of Product"):
        def normalize(s):
            s = str(s).lower().strip()
            s = re.sub(r"[^\w\s]", " ", s)
            s = re.sub(r"\s+", " ", s)
            return s

        df = df.copy()
        df["_normalized"] = df[product_col].apply(normalize)

        # Step 1: phonetic code using metaphone
        df["_phonetic"] = df["_normalized"].apply(lambda x: phonetics.metaphone(x.split()[0]))

        # Step 2: choose canonical per phonetic cluster
        if count_col in df.columns:
            canonical = df.groupby("_phonetic").apply(
                lambda g: g.loc[g[count_col].idxmax(), "_normalized"]
            )
        else:
            canonical = df.groupby("_phonetic")["_normalized"].apply(lambda g: g.iloc[0])

        df["Clean Product"] = df["_phonetic"].map(canonical)

        df.drop(columns=["_normalized", "_phonetic"], inplace=True)
        return df

    def process(self):
        print("Welcome to the test bed...")


        #canonical_dict
        file_name = self.app_container.config.input_path + "product_mapping.csv"
        print(file_name)
        df = pd.read_csv(file_name)
        cleaned_df = self.auto_clean_products(df, product_col="Product", count_col="Count of Product")

        self.save_report(cleaned_df)
   
        '''
        df = self.app_container.dataset.get_data(DataTypes.SALES_DATA)

        sales_df = df[df['Sales Qty'] > 0].copy()
        returns_df = df[df['Sales Qty'] < 0].copy()
        #sales_df = df[(df['Sales Qty'] > 0) & (df['Effective Disc %'] > 0)].copy()
        #returns_df = df[df['Sales Qty'] < 0].copy()
        discounted_sales_df = df[(df['Sales Qty'] > 0) & (df['Effective Disc %'] > 0)]


        plt.figure(figsize=(10, 6))
        sns.kdeplot(sales_df['Unit Price'], label='Sales', shade=True, color='blue')
        sns.kdeplot(returns_df['Unit Price'], label='Returns', shade=True, color='red')
        plt.title('Unit Price Distribution: Sales vs Returns')
        plt.xlabel('Unit Price')
        plt.ylabel('Density')
        plt.legend()
        plt.grid(True)
        plt.show()        


        numeric_cols = df.select_dtypes(include='number').columns.tolist()        


        plt.figure(figsize=(8, 4))
        sns.boxplot(x=discounted_sales_df['Effective Disc %'], color='lightgreen')
        #sns.boxplot(x=returns_df['Effective Disc %'], color='red')
        plt.title('Box Plot of Effective Discount %')
        plt.xlabel('Effective Discount %')
        plt.grid(True)
        plt.show()
        
        # Compute Z-scores
        z_scores = df[numeric_cols].apply(zscore)

        print("z-scores")

        # Plot Z-scores for each column
        plt.figure(figsize=(12, 6))
        for col in numeric_cols:
            plt.plot(z_scores[col], label=col)


        plt.axhline(y=3, color='r', linestyle='--', label='Z = +3')
        plt.axhline(y=-3, color='r', linestyle='--', label='Z = -3')
        plt.title("Z-Score Outlier Detection")
        plt.xlabel("Row Index")
        plt.ylabel("Z-Score")
        plt.legend()
        plt.tight_layout()
        plt.show()

        for col in numeric_cols:
            plt.figure(figsize=(6, 1.5))
            sns.boxplot(x=df[col])
            plt.title(f"Boxplot: {col}")
            plt.tight_layout()
            plt.show()

        print("\n")

        # Combine both conditions (if needed)
        free_items = df[
            (df['Sales Qty'] > 0) & (
            (df['Net Amount'].abs() < 10) |
            (df['Effective Disc %'] > 99)
            )]

        # View or export
        print('free items:')
        print(free_items[['Voucher No', 'Product', 'Sales Qty', 'Retail Value', 'Net Amount', 'Effective Disc %']])

        discounted_sales_df = df[(df['Sales Qty'] > 0) & (df['Effective Disc %'] > 0)]

        plt.figure(figsize=(10, 6))
        sns.histplot(discounted_sales_df['Effective Disc %'], bins=50, kde=True, color='skyblue')
        plt.title('Distribution of Effective Discount %')
        plt.xlabel('Effective Discount %')
        plt.ylabel('Number of Sales')
        plt.grid(True)
        plt.show()
        

        from statsmodels.distributions.empirical_distribution import ECDF
        import numpy as np

        ecdf = ECDF(discounted_sales_df['Unit Price'])
        x = np.linspace(0, discounted_sales_df['Unit Price'].max(), 500)

        plt.figure(figsize=(10, 5))
        plt.plot(x, ecdf(x), color='darkblue')
        plt.xlabel('Unit Price')
        plt.ylabel('Cumulative Share of Transactions')
        plt.title('ECDF of Unit Price')
        plt.grid(True)
        plt.show()

        print("swarmplot")
        try:
            sns.swarmplot(x='Category', y='Unit Price', data=discounted_sales_df, size=3)
            plt.title('Unit Price Distribution by Category')
            plt.grid(True)
            plt.show()
        except  Exception as e:
            print(e)
        
        plt.figure(figsize=(10, 4))
        plt.title('Box Plot of Unit Price (Sales Only)')
        plt.xlabel('Unit Price')
        plt.grid(True)

        sns.boxplot(x=discounted_sales_df['Unit Price'], color='lightblue')
        plt.show()

        sns.violinplot(x=discounted_sales_df['Unit Price'], color='lightblue')
        plt.show()

        sns.stripplot(x=discounted_sales_df['Unit Price'], color='darkblue', alpha=0.5)
        plt.show()

        plt.figure(figsize=(8, 4))
        sns.boxplot(x=sales_df['Effective Disc %'], color='lightgreen')
        plt.title('Box Plot of Effective Discount %')
        plt.xlabel('Effective Discount %')
        plt.grid(True)
        plt.show()

        plt.figure(figsize=(10, 6))
        sns.histplot(discounted_sales_df['Retail Value'], bins=50, kde=True, color='green')
        plt.title('Distribution of Retail Value (Sales Only)')
        plt.xlabel('Retail Value')
        plt.ylabel('Number of Sales')
        plt.grid(True)
        plt.show()

        returns_df = df[df['Sales Qty'] < 0]

        plt.figure(figsize=(10, 6))
        sns.kdeplot(sales_df['Unit Price'], label='Sales', shade=True, color='blue')
        sns.kdeplot(returns_df['Unit Price'], label='Returns', shade=True, color='red')
        plt.title('Unit Price Distribution: Sales vs Returns')
        plt.xlabel('Unit Price')
        plt.ylabel('Density')
        plt.legend()
        plt.grid(True)
        plt.show()
        '''
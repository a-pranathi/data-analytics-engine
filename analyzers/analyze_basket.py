'''
File: analyze_basket.py
Author: Pranathi Ayyadevara
Description:
    Analyzes customer purchase behavior at the basket level, surfacing co-purchase patterns,
    SKU affinities, and potential bundling opportunities.
'''

from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import pandas as pd
from analyzers.analyze import Analyze
from common.chart_builder import ChartBuilder
from common.constants import *

class AnalyzeBasket(Analyze):
    def __init__(self, app_container):
        super().__init__(app_container)
        self.analyzer_type = AnalyzerType.BASKET
        self.output_file = self.app_container.config.get_analyzer_output_file(self.analyzer_type)

    def analyze_basket(self):
        df_sales = self.app_container.dataset.get_data(DataTypes.SALES_DATA)

        # Group products by voucher number
        basket = df_sales.groupby("Voucher Key")["Product"].apply(list).tolist()

        # Clean basket: remove NaNs and convert all items to strings
        cleaned_basket = [
            [str(item) for item in transaction if pd.notnull(item)]
            for transaction in basket
        ]
    
        # Encode transactions
        te = TransactionEncoder()
        te_ary = te.fit(cleaned_basket).transform(cleaned_basket)
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

        # Generate frequent itemsets and rules
        frequent_itemsets = apriori(df_encoded, min_support=0.01, use_colnames=True)
        rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)

        return rules

    def process(self):
        print("Performing Market Basket Analysis...")        
        rules = self.analyze_basket()
        fig_one_to_one, fig_may_to_one = ChartBuilder.plot_rules(rules)
        
        self.save_report(data=[("Basket Modelling", rules)],
                               figures=[("One to One Network", fig_one_to_one),
                                        ("Many to One Network", fig_may_to_one)])
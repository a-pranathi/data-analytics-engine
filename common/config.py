'''
File: config.py
Author: Pranathi Ayyadevara
Description:
    Singleton class that stores all configuration.
    Configuration for the application, folder locations, file names and analyzer mappings
'''

from common.constants import *

class Config():
    _instance = None
    _initialized = False

    def __new__(cls, app_container=None):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self, app_container=None):
        if not self._initialized:
            self.app_container = app_container
            self.__load_config()
            self.__class__._initialized = True

    def __load_config(self):
        # App info
        self.app_name = "Data Analysis"
        self.version = "1.0"
        self.owner = "Pranathi Ayyadevara"

        self.input_path = "input/"
        self.output_path = "output/"
        
        self.__datafiles = {
            DataTypes.OPENING_STOCK : "opening_stock.csv",
            DataTypes.CLOSING_STOCK : "closing_stock.csv",
            DataTypes.PURCHASE_DATA : "purchase_data.csv",
            DataTypes.SALES_DATA : "sales_data.csv",
            DataTypes.EXPENSE_DATA : "expense_data.csv",
            DataTypes.PURCHASE_RETURN_DATA : "purchase_return_data.csv",
            DataTypes.STOCK_VERIFICATION_DATA : "stock_verification_data.csv",
            DataTypes.PRODUCT_MAPPING_DATA: "product_mapping_data.csv"
            }

        self.__analyzerfiles = {
            AnalyzerType.STATISTICS : {
                ValueNames.CLASS : "AnalyzeStatistics",
                ValueNames.OUTPUT_FILE: "result_statistics",
            },
            AnalyzerType.BASKET : {
                ValueNames.CLASS : "AnalyzeBasket",
                ValueNames.OUTPUT_FILE: "result_basket",
            },
            AnalyzerType.MARGIN : {
                ValueNames.CLASS : "AnalyzeMargin",
                ValueNames.OUTPUT_FILE: "result_margin",
            },                                    
            AnalyzerType.PROFIT : {
                ValueNames.CLASS : "AnalyzeProfit",
                ValueNames.OUTPUT_FILE: "result_profit",
            },
            AnalyzerType.SALES : {
                ValueNames.CLASS : "AnalyzeSales",
                ValueNames.OUTPUT_FILE: "result_sales",
            },
            AnalyzerType.INVENTORY : {
                ValueNames.CLASS : "AnalyzeInventory",
                ValueNames.OUTPUT_FILE: "result_inventory",
            },                 
            AnalyzerType.TEST_BED : {
                ValueNames.CLASS : "AnalyzeTestBed",
                ValueNames.OUTPUT_FILE: "result_test_bed",
            },
        }

    def get_data_files(self):
        return self.__datafiles
    
    def get_analyzer_files(self):
        return self.__analyzerfiles
    
    def get_analyzer_output_file(self, analyzertype):
        return self.output_path + self.__analyzerfiles[analyzertype][ValueNames.OUTPUT_FILE]
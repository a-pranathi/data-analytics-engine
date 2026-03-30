'''
File: constants.py
Author: Pranathi Ayyadevara
Description:
    Declaration of all constants used through out the application
'''
from enum import Enum

class DataTypes(Enum):
    OPENING_STOCK = "opening_stock"
    CLOSING_STOCK = "closing_stock"
    PURCHASE_DATA = "purchase_data"
    SALES_DATA = "sales_data"
    EXPENSE_DATA = "expense_data"
    PURCHASE_RETURN_DATA = "purchase_return_data"
    STOCK_VERIFICATION_DATA = "stock_verification_data"
    PRODUCT_MAPPING_DATA = "product_mapping_data"

class AnalyzerType(Enum):
    STATISTICS = 1
    BASKET = 2
    MARGIN = 3
    PROFIT = 4
    SALES = 5
    INVENTORY = 6
    TEST_BED = 7

    @classmethod
    def ALL(cls):
        return {item.value for item in cls}
    
class ValueNames(Enum):
    CLASS = "class"
    INPUT_FILE = "input_file"
    OUTPUT_FILE = "output_file"
    INSTANCE = "instance"

class ChartType:
    LINE = "line"
    BAR = "bar"
    BARH = "barh"
    SCATTER = "scatter"
    PIE = "pie"
    HIST = "hist"
    AREA = "area"
    BOX = "box"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    STACKED_BAR = "stacked_bar"
    GROUPED_BAR = "grouped_bar"
    THREE_D = "3d"

    ALL = {
        LINE,
        BAR,
        BARH,
        SCATTER,
        PIE,
        HIST,
        AREA,
        BOX,
        VIOLIN,
        HEATMAP,
        STACKED_BAR,
        GROUPED_BAR,
        THREE_D,
    }
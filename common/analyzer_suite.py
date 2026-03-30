'''
File: app_container.py
Author: Pranathi Ayyadevara
Description:
    Singleton class that is caches all analyzers.
    All analyzers are initialized and ready to use.
'''

from common.constants import *

from analyzers.analyze_basket import AnalyzeBasket
from analyzers.analyze_inventory import AnalyzeInventory
from analyzers.analyze_margin import AnalyzeMargin
from analyzers.analyze_profit import AnalyzeProfit
from analyzers.analyze_sales import AnalyzeSales
from analyzers.analyze_statistics import AnalyzeStatistics
from analyzers.analyze_testbed import AnalyzeTestBed

class AnalyzerSuite():
    _instance = None
    _initialized = False

    def __new__(cls, app_container=None):
        if not cls._instance:
            cls._instance = super(AnalyzerSuite, cls).__new__(cls)
        return cls._instance

    def __init__(self, app_container=None):
        if not self._initialized:
            self.app_container = app_container
            self.__analyzers = {}
            self.__load_analyzers()
            self.__class__._initialized = True
        
    def __load_analyzers(self):
        config = self.app_container.config
        for key, item in config.get_analyzer_files().items():
            cls = globals()[item[ValueNames.CLASS]]
            self.__analyzers[key] = cls(self.app_container)

    def get_analyzer(self, analyzer_type):
        return self.__analyzers[analyzer_type]
'''
File: app_container.py
Author: Pranathi Ayyadevara
Description:
    Singleton class that is the container of the application.
    Caches configuration, datasets and analyzer suite
'''

from common.config import Config
from common.dataset import Dataset
from common.analyzer_suite import AnalyzerSuite
from common.constants import *

class AppContainer():
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(AppContainer, cls).__new__(cls)
            cls._instance.setup()
        return cls._instance
    
    def setup(self):
        self.config = Config(self)
        self.dataset = Dataset(self)
        self.analyzer_suite = AnalyzerSuite(self)
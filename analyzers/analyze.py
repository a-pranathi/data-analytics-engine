'''
File: analyze.py
Author: Pranathi Ayyadevara
Description:
    	Base class for all analyzers.
        caputres the common logic with standard interface definitions. 
'''

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
from common.constants import *

class Analyze():
    def __init__(self, app_container):
        self.app_container = app_container
        self.analyzer_type = None
        self.output_file = None

    def process(self):
        print("From analyze process...")
    
    def fig_to_bytes(self, fig):
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        return buf

    def write_to_excel(self,
        filename: str,
        dataframes: list[tuple[str, pd.DataFrame]] = None,
        figures: list[tuple[str, plt.Figure]] = None,
        graph_sheet_name: str = 'Graphs'):

        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            workbook = writer.book

            # Write DataFrames
            if dataframes:
                for sheet_name, df in dataframes:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Write Figures
            if figures:
                worksheet = workbook.add_worksheet(graph_sheet_name)
                row = 1
                for caption, fig in figures:
                    img_data = self.fig_to_bytes(fig)
                    with Image.open(img_data) as img:
                        width_px, height_px = img.size
                    row_height = height_px * 0.75
                    col_width = width_px / 7
                    worksheet.set_row(row + 1, row_height)
                    worksheet.set_column(1, 1, col_width)
                    worksheet.write(row, 0, caption)
                    worksheet.insert_image(row + 1, 1, '', {'image_data': img_data})
                    #row += int(row_height / 15) + 3
                    row += 2


    def save_report_old(self, data: dict | pd.DataFrame | list[tuple[str, pd.DataFrame]] = None,
                    figures: list[tuple[str, plt.Figure]] = None):        
        # Normalize data input
        if isinstance(data, dict):
            df = pd.DataFrame.from_dict(data, orient='index')
            dataframes = [('Sheet1', df)]
        elif isinstance(data, pd.DataFrame):
            dataframes = [('Sheet1', data)]
        elif isinstance(data, list):
            dataframes = data
        else:
            dataframes = []

        # Decide format
        if figures or len(dataframes) > 1:
            self.write_to_excel(f'{self.output_file}.xlsx', dataframes, figures)
        elif dataframes:
            name, df = dataframes[0]
            df.to_csv(f'{self.output_file}.csv', index=True)

    def save_report(self, data: dict | pd.Series | pd.DataFrame | list[tuple[str, pd.DataFrame]] = None,
                    figures: list[tuple[str, plt.Figure]] = None):        
        # Normalize data input
        if isinstance(data, dict):
            df = pd.DataFrame.from_dict(data, orient='index')
            dataframes = [('Sheet1', df)]
        elif isinstance(data, pd.Series):
            df = data.to_frame()
            dataframes = [('Sheet1', df)]
        elif isinstance(data, pd.DataFrame):
            dataframes = [('Sheet1', data)]
        elif isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                df = pd.DataFrame(data)
                dataframes = [('Sheet1', df)]
            elif all(isinstance(item, tuple) and isinstance(item[1], pd.DataFrame) for item in data):
                dataframes = data
            else:
                raise ValueError("List input must be a list of dicts or (name, DataFrame) tuples.")
        else:
            dataframes = []

        # Decide format
        if figures or len(dataframes) > 1:
            self.write_to_excel(f'{self.output_file}.xlsx', dataframes, figures)
        elif dataframes:
            name, df = dataframes[0]
            df.to_csv(f'{self.output_file}.csv', index=True)
        else:
            raise ValueError("No data provided to save.")
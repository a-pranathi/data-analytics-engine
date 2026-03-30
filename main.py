'''
File: main.py
Author: Pranathi Ayyadevara
Description:
    Main class, entry point to the command line interface.
'''

from common.constants import *
from common.app_container import AppContainer

def print_options():
    print("\nWelcome to the Data Analysis Engine. Please select the Analyzer type you are interested in...\n")
    print("Available options:")
    for analyzer in AnalyzerType:
        print(f"{analyzer.value}. {analyzer.name}")
    print("\nType the analyzer number of your choice, or enter 'exit' to quit.")

def main():
    app_container = AppContainer()
    print_options()

    while True:
        user_input = input(">> ").strip().lower()
        if user_input == "exit":
            print("Goodbye!")
            break
        try:
            selected_value = int(user_input)
            if selected_value not in AnalyzerType.ALL():
                print(f"Option {selected_value} is Invalid. Please try again or enter exit to quit!")
                print_options()
            else:
                selected = AnalyzerType(selected_value)
                print(f"Selected Analyzer type: {selected.name}")
                app_container.analyzer_suite.get_analyzer(selected).process()                
                print("✅ Analysis complete. Results saved to the output folder.")
        except ValueError:
            print("Invalid option selected. Please try again or enter exit to quit!")
            print_options()
        except Exception as e:
            print(e)
            print("An error has occured! Please check the log...")
            print_options()

if __name__ == "__main__":
    main()
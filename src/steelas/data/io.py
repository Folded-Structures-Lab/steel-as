
import os
import pandas as pd

def import_section_library(filename: str, skiprows: int | list[int] | None = [1]) -> pd.DataFrame:
    """
    Imports a section library from a CSV file located at 'steelas/data/{filename}.csv'.

    Returns:
        pd.DataFrame: A DataFrame containing the contents of the section library CSV file.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    cwd = os.path.dirname(__file__) 
    dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
    lib_path = os.path.join(dir, f'data/{filename}.csv')
    #return csv without unit row
    return pd.read_csv(lib_path, skiprows=skiprows)

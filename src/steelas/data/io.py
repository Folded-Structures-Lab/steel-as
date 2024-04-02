import os
import pandas as pd
from enum import StrEnum


class MemberLibrary(StrEnum):
    OpenSections = "data/AUS_open_sections.csv"
    HollowSections = "data/AUS_hollow_sections.csv"


def import_section_library(
    filename: str | MemberLibrary, skiprows: int | list[int] | None = [1]
) -> pd.DataFrame:
    """
    Imports a section library from a CSV file located at 'steelas/data/{filename}.csv'.

    Returns:
        pd.DataFrame: A DataFrame containing the contents of the section library CSV file.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """

    if isinstance(filename, MemberLibrary):
        filename = filename.value
    else:
        filename = f"data/{filename}.csv"

    # cwd = os.path.dirname(__file__)
    dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lib_path = os.path.join(dir, filename)
    # return csv without unit row
    return pd.read_csv(lib_path, skiprows=skiprows)


def get_section_from_library(
    library: MemberLibrary, lookup_val: str, lookup_col: str = "section"
) -> dict:
    """
    Returns a single row of section parameters from section library, based on lookup
    value and lookup column.

    """

    sec_df = import_section_library(library)
    selected_item = sec_df[sec_df[lookup_col] == lookup_val]
    if len(selected_item) > 1:
        raise ValueError(f"Error: non-unique {lookup_col}: {lookup_val}")

    if len(selected_item) == 0:
        raise ValueError(f"Error: no sections with {lookup_col} equal to {lookup_val}")
    return selected_item.iloc[0].to_dict()


nomenclature_AS4100 = {
    "param": ("description", "(Cl X.X, Cl Y.Y)"),
}


def report(
    obj,
    attribute_names: str | list[str] | None = None,
    exclude_attribute_names: list[str] | None = None,
    report_type: str = "print",
    with_name: bool = True,
    # with_nomenclature: bool = False,
    # with_clause: bool = False,
) -> None:
    # convert single-value attribute to list
    if attribute_names is None:
        attribute_names = list(obj.__annotations__.keys())
    if not isinstance(attribute_names, list):
        attribute_names = [attribute_names]
    if exclude_attribute_names is not None:
        # NOTE: could do this more elegantly
        all_attrs = attribute_names
        attribute_names = []
        for a in all_attrs:
            if a not in exclude_attribute_names:
                attribute_names.append(a)

    if report_type == "print":
        # print out attributes
        if hasattr(obj, "__class__") and with_name:
            print("\n")
            # name = obj.name if hasattr(obj, "name") else ""
            print(f"{obj.__class__.__name__} Attributes:")

        for att in attribute_names:
            # get attribute val from self, self.sec, or self.mat
            att_val = None
            if hasattr(obj, att):
                att_val = getattr(obj, att)
            if att_val is not None:
                prefix = ""
                # if att in nomenclature_AS4100:
                #     # check it attribute defined in nomenclature dictionary
                #     nom, clause = nomenclature_AS4100[att]
                #     if with_nomenclature:
                #         # add nomenclature
                #         prefix = prefix + " " + nom
                #     if with_clause:
                #         # add clause
                #         prefix = prefix + " " + clause
                print(f"    {att}{prefix} = {att_val}")
            # else:
            # print(f"Unknown attribute {att}")

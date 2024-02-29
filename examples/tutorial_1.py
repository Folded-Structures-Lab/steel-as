"""Quick start example for steelas"""

from steelas.member.geometry import SectionGeometry
from steelas.data.io import import_section_library

# Define a section geometry from the data library
sec_df = import_section_library("AUS_open_sections")
sec_dict = sec_df[sec_df["section"] == "1200WB423"].iloc[0].to_dict()
geom = SectionGeometry.from_dict(**sec_dict)
print("\nGeometry from library:")
print(geom)

# Define a custom section geometry
geom_dict2 = {
    "section": "user_PFC",
    "sec_type": "PFC",
    "d": 380,
    "b": 100,
    "t_f": 17.5,
    "t_w": 10,
    "r_1": 14,
}
print("\nGeometry from user input - PFC:")
geom_user = SectionGeometry(**geom_dict2)
print(geom_user)

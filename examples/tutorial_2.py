"""Example steelas code for defining geometric and material properties"""


############################
# 1. Define a Steel Section
############################

from steelas.data.io import (
    get_section_from_library,
    import_section_library,
    MemberLibrary,
)
from steelas.member.geometry import SectionGeometry

# EG 1A
print("\n Example 1A: Define a steel section from library import")

open_section_library = MemberLibrary.OpenSections
open_section_parameters = get_section_from_library(open_section_library, "250UC72.9")
geom = SectionGeometry.from_dict(**open_section_parameters)
geom.report()

# EG 1B
print("\n Example 1B: Define a custom steel section")
section_parameters = {
    "section": "user_PFC",
    "sec_type": "PFC",
    "d": 380,
    "b": 100,
    "t_f": 17.5,
    "t_w": 10,
    "r_1": 14,
}
user_geom = SectionGeometry(**section_parameters)
user_geom.report()

# EG 1C
print("\n Example 1C: Define a steel section from unique library name")

hollow_section_library = MemberLibrary.HollowSections
hollow_section_df = import_section_library(hollow_section_library)
print(f"Available sections in the {hollow_section_library}:")
print(hollow_section_df)

hollow_section_parameters = get_section_from_library(
    library=hollow_section_library, lookup_val="65x35x2RHS (C350)", lookup_col="name"
)
geom2 = SectionGeometry.from_dict(**hollow_section_parameters)
geom2.report()

# ############################
# # 2. Define a Steel Material
# ############################

from steelas.member.material import SteelMaterial, SteelMaterialType, SteelGrade

# EG 2A
print("\n Example 2A: Define a steel material property from Australian Standards")
mat = SteelMaterial(
    name="AS3679 hot-rolled section property",
    grade=SteelGrade.GR300,
    mat_type=SteelMaterialType.HotRolledSection,
    t=10,
)
mat.report()

# EG 2B
print("\n Example 2B: Define a steel material property from lirbary import.")

# open and hollow section parameters from EG1
mat2 = SteelMaterial.from_dict(**open_section_parameters)
mat2.report()
mat3 = SteelMaterial.from_dict(**hollow_section_parameters)
mat3.report()

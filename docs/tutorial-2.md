
# Geometry and Material

Python code for the following examples are available in the Github repository [examples folder](https://github.com/Folded-Structures-Lab/steel-as/tree/main/examples/tutorial_2.py). 

## Define a steel profile
*steelas* solves the geometric properties of a structural section profile using the *SectionGeometry* class in the *member.geometry* module. A profile can be imported from a library of 'standard' Australian steel section sizes [(link here)](https://github.com/Folded-Structures-Lab/steel-as/blob/main/src/steelas/data/) using *data.io* methods. Properties can be accessed as attributes of the created section. 
```
from steelas.data.io import MemberLibrary, get_section_from_library
from steelas.member.geometry import SectionGeometry

print("\n Example 1A: Define a steel section from library import")
open_section_library = MemberLibrary.OpenSections
open_section_parameters = get_section_from_library(open_section_library, "250UC72.9 (GR300)")
geom = SectionGeometry.from_dict(**open_section_parameters)
geom.report()
```

Custom sections can be defined directly:
```
# define a custom section
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
```
The shape_type attribute defines a particular shape to use for calculating section properties.

## Define a steel material

A steel material property is similarly defined using the *SteelMaterial* class in the *member.material* module. The *SteelGrade* and *SteelMaterialType* classes contain constants of available material grades and types, respectively.

```
from steelas.member.material import SteelGrade, SteelMaterial, SteelMaterialType

# EG 2A
print("\n Example 2A: Define a steel material property from Australian Standards")
mat = SteelMaterial(
    name="AS3679 hot-rolled section property",
    grade=SteelGrade.GR300,
    mat_type=SteelMaterialType.HotRolledSection,
    t=10,
)
mat.report()
```

Steel materials for a particular steel section can be defined directly from the same library imports used to create section profiles above:

```
from steelas.data.io import MemberLibrary, import_section_library, get_section_from_library
from steelas.member.material import SteelMaterial

# EG2B
# open and hollow section parameters from EG1
mat2 = SteelMaterial.from_dict(**open_section_parameters)
mat2.report()

# hollow section section example
hollow_section_library = MemberLibrary.HollowSections
hollow_section_df = import_section_library(hollow_section_library)
print(f"Available sections in the {hollow_section_library}:")
print(hollow_section_df)

hollow_section_parameters = get_section_from_library(
    hollow_section_library, "65x35x2RHS (C350)"
)
mat3 = SteelMaterial.from_dict(**hollow_section_parameters)
mat3.report()
```



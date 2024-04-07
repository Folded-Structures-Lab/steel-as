
# Section and Member Capacities

Python code for the following examples are available in the Github repository [examples folder](https://github.com/Folded-Structures-Lab/steel-as/tree/main/examples/tutorial_3.py). 

Several examples on this page are sourced from the *Steel Designers' Handbook* (available from [Australian Steel Institute](https://www.steel.org.au/resources/book-shop/steel-designers-handbook/)), written by B. Gorenc, R. Tinyou, R., & A. Syam. This handbook provides detailed guidance and additional information on the design of Australian steel structures. 


## Slenderness
Section slenderness is evaluated in the *SteelSlenderness* class from input geometric and material property classes:
```
from steelas.member.geometry import SectionGeometry
from steelas.member.material import SteelMaterial
from steelas.member.slenderness import SteelSlenderness
from steelas.data.io import MemberLibrary, get_section_from_library

# section slenderness is evaluated from input geometric and material properties
sec_params = get_section_from_library(MemberLibrary.OpenSections, "460UB74.6 (GR300)")
geom = SectionGeometry.from_dict(**sec_params)
mat = SteelMaterial.from_dict(**sec_params)

slenderness = SteelSlenderness(geom=geom, mat=mat)
slenderness.report()

print(f"Form factor for {slenderness.name} = {slenderness.k_f}")
print("(ANS = 0.948, 7th Ed. Hot Rolled and Structural Steel Products)")
```

Section geometric, material, and slenderness properties can all be derived from input library section information for typical steel sections. The *SteelSection* class creates a section directly, storing the above properties as attributes:

```
from steelas.member.member import SteelSection
sec = SteelSection.from_library(MemberLibrary.OpenSections, "460UB74.6 (GR300)")
sec.report()
```

## Member Design Capacities

As introduced in the [Quick Start](tutorial-1.md) section, *steelas* creates a structural member using  the *SteelMember* class. The member class defines general AS4100 section and member design attributes and methods and is intended to evaluate the design capacities of structural steel. The current toolbox version including evaluation of tension, compression, bending, and shear capacities.

For evaluation of section and member design capacities, a SteelMember is simply created from an input SteelSection. 


## Tension Capacity

The nominal tensile axial capacity of steel members is evaluated as per AS 4100 Clause 7.2 as:
$$
\phi N_{t} = min (\phi A_t f_y, \phi 0.85 k_t A_n f_u)
$$
Input and evaluation of tension design parameters using *steelas* is detailed further with reference to the following example.

* Example 7.1 (Part 4), Steel Designers' Handbook
> Determine the tensile axial capacity for a 250UC89.5 Grade 300 section.

```
from steelas.member.member import SteelSection, SteelMember

# Create a structural member to evaluate section capacities
sec = SteelSection.from_library(MemberLibrary.OpenSections, "250UC89.5 (GR300)")
member = SteelMember(section=sec)

# tension capacity
print(f"\nTension capacity for {member.name}:")
member.report(attribute_names=["phi", "N_t", "phiN_t"], with_name=False)
print("(ANS: phiN_t = 2870 kN)")
```
The *member.report()* method is used to print a formatted report of the requested attribute names.


## Compression Capacity

The design compressive section capacity of a steel member evaluated as per AS 4100 Clause 6.2 as:
$$
\phi N_s = \phi k_f A_n f_y
$$

The design compressive member capacity is evaluated as per AS4100 Clause 6.3 as:
$$
\phi N_c = \phi \alpha_c N_s 
$$

Input and evaluation of compression design parameters using *steelas* is detailed further with reference to the following example.

*Example 6.2, Steel Designers' Handbook
> Determine the section and member compressive capacities for a 200 x 200 x 5.0 SHS Grade 
> C450L0 section, with effective length 3.8m.
```
from steelas.member.member import SteelSection, SteelMember

# Create a structural member to evaluate section capacities
sec = SteelSection.from_library(MemberLibrary.HollowSections, "200x5SHS (C450)")
member = SteelMember(section=sec, l_ex=3800, l_ey=3800)

print(f"\nNominal section compression capacity for {member.name}: {member.N_s} kN")
print("(ANS: N_s = 1340 kN)\n")

print(f"\nMember compression capacity for {member.name}: {member.phiN_c} kN")
print("(ANS: phiN_c = 1050 kN)\n")

print(f"\nSlenderness reduction factor, x axis: {member.alpha_cx}")
print(f"Slenderness reduction factor, y axis: {member.alpha_cy}")
print("(ANS: alpha_c = 0.876)\n")
```


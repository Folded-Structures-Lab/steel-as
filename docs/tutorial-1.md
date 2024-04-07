
# Quick Start

Python code for the following examples are available in the Github repository [examples folder](https://github.com/Folded-Structures-Lab/steel-as/tree/main/examples/tutorial_1.py). 

*steelas* can be used to determine the material properties, section properties, and design capacities for structural members as per Australian Standard AS4100:2020 (Steel Structures).

A typical operation is shown in the below example. Section and material properties are first defined from library import. A structural member is then defined from section, material, and design information. See the following pages for additional information. 

```
from steelas.member.member import SteelSection, SteelMember
from steelas.data.io import MemberLibrary

# Create a steel section from the library
section = SteelSection.from_library(MemberLibrary.OpenSections, "1200WB423 (GR300)")
section.report()

# Calculate section capacities
sm = SteelMember(section=section)
sm.report(attribute_names=["phiN_t", "phiN_s", "phiV_v", "phiM_sx", "phiM_sy"])

# Calculate member capacities
sm = SteelMember(section=section, l_ex=21000, l_ey=4000, l_eb=0, alpha_m=1)
sm.report()
print(sm.phiN_c)
```
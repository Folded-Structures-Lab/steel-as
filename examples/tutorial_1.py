"""Quick start example for steelas"""

from steelas.member.member import SteelSection, SteelMember
from steelas.data.io import MemberLibrary

# Create a steel section from the library
section = SteelSection.from_library(MemberLibrary.OpenSections, "1200WB423")
section.report()

# Calculate section capacities
sm = SteelMember(section=section)
sm.report(attribute_names=["phiN_t", "phiN_s", "phiV_v", "phiM_sx", "phiM_sy"])

# Calculate member capacities
sm = SteelMember(section=section, l_ex=21000, l_ey=4000, l_eb=0, alpha_m=1)
sm.report(attribute_names=["phiN_c"])
sm.report()

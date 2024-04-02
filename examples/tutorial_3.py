"""Example steelas code for evaluation of section slenderness and section capacities."""

from steelas.member.geometry import SectionGeometry
from steelas.member.material import SteelMaterial
from steelas.member.slenderness import SteelSlenderness
from steelas.data.io import MemberLibrary, get_section_from_library


#########################
# Section Slenderness
#########################

print("EG3 Evaluate slenderness factor kf")

# section slenderness is evaulated from input geometric and material properties
sec_params = get_section_from_library(MemberLibrary.OpenSections, "460UB74.6")
geom = SectionGeometry.from_dict(**sec_params)
mat = SteelMaterial.from_dict(**sec_params)

slenderness = SteelSlenderness(geom=geom, mat=mat)
slenderness.report()


#########################
# Section Capacities
#########################

print("EGX Evaluate section capacities")

from steelas.member.member import SteelSection, SteelMember

# create a steel section directly with geometric, material, and slenderness properties.
sec = SteelSection.from_library(MemberLibrary.OpenSections, "460UB74.6")
sec.report()

# Create a structural member to evaluate section capacities
member = SteelMember(section=sec)

# tension capacity
print(f"\nTension capacity for {member.name}:")
member.report(attribute_names=["phi", "N_t", "phiN_t"], with_name=False)

# compression capacity
print(f"\nCompression capacity for {member.name}: phiN_s = {member.phiN_s} kN")

# bending capacity
print(f"\nX capacity: phiM_sx = {member.phiM_sx} kNm")
print(f"\nX capacity: phiM_sy = {member.phiM_sy} kNm")
print(f"\nShear capacity: phiV_v = {member.phiV_v} kN")
# print("(ANS: N_dt = 25.4 kN)")

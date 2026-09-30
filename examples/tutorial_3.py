"""Example steelas code for evaluation of section slenderness and section capacities."""

from steelas.member.geometry import SectionGeometry
from steelas.member.material import SteelMaterial
from steelas.member.slenderness import SteelSlenderness
from steelas.data.io import MemberLibrary, get_section_from_library


#########################
# Section Slenderness
#########################

print("EG2 Evaluate slenderness factor kf")

# section slenderness is evaulated from input geometric and material properties
sec_params = get_section_from_library(MemberLibrary.OpenSections, "460UB74.6 (GR300)")
geom = SectionGeometry.from_dict(**sec_params)
mat = SteelMaterial.from_dict(**sec_params)

slenderness = SteelSlenderness(geom=geom, mat=mat)
slenderness.report()

print(f"Form factor for {slenderness.name} = {slenderness.k_f}")
print("(ANS = 0.948, 7th Ed. Hot Rolled and Structural Steel Products)")

# create a steel section directly with geometric, material, and slenderness properties.
from steelas.member.member import SteelSection

sec = SteelSection.from_library(MemberLibrary.OpenSections, "460UB74.6 (GR300)")
sec.report()
print("\n #################### \n")


##############################
# Section Capacities - Tension
##############################

print("Example 7.1 (Part 4), Steel Designers' Handbook")
print("Determine the tensile axial capacity for a 250UC89.5 Grade 300 section.")

from steelas.member.member import SteelSection, SteelMember


# Create a structural member to evaluate section capacities
sec = SteelSection.from_library(MemberLibrary.OpenSections, "250UC89.5 (GR300)")
member = SteelMember(section=sec)

# tension capacity
print(f"\nTension capacity for {member.name}:")
member.report(attribute_names=["phi", "N_t", "phiN_t"], with_name=False)
print("(ANS: phiN_t = 2870 kN)")
print("\n #################### \n")

##############################################
# Section and Member Capacities - Compression
##############################################

print("Example 6.2, Steel Designers' Handbook\n")
print(
    "Determine the section and member compressive capacities for a 200 x 200 x 5.0 SHS Grade C450L0 section, with effective length 3.8m.\n"
)

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
print("\n #################### \n")

###################################################
# Section and Member Capacities - Combined Actions
###################################################

print("Combined actions, hand calculation\n")
print(
    "Determine the general and alternative combined actions capacities for a 3.0m 150UB18.0 Grade 300 beam-column, braced in-plane with k_e = 0.7, with N* = 50 kN compression, M_x* = 5 kNm, M_y* = 1 kNm, alpha_m = 1.3, beta_mx = 0.5, beta_my = 0, and no transverse load.\n"
)

sec = SteelSection.from_library(MemberLibrary.OpenSections, "150UB18.0 (GR300)")
member = SteelMember(
    section=sec,
    l=3000,
    l_ex=2100,
    l_ey=3000,
    l_eb=3000,
    l_z=3000,
    alpha_m=1.3,
    beta_mx=0.5,
    beta_my=0,
    transverse_load=False,
)

# design actions (kN, kNm), compression negative
N_star, M_x_star, M_y_star = -50, 5, 1

for alternative in (False, True):
    print(f"\nAlternative capacities: {alternative}")
    print(f"phiM_rx = {member.phi * member.M_rx(N_star, alternative):.3g} kNm")
    print(f"phiM_cx = {member.phi * member.M_cx(N_star, alternative):.3g} kNm")
    print(f"phiM_iy = {member.phi * member.M_iy(N_star, alternative):.3g} kNm")
    section_ratio = member.section_biaxial_ratio(N_star, M_x_star, M_y_star, alternative)
    member_ratio = member.member_biaxial_ratio(N_star, M_x_star, M_y_star, alternative)
    print(f"Section biaxial ratio = {section_ratio:.3g}")
    print(f"Member biaxial ratio = {member_ratio:.3g}")

print("\n(ANS general: phiM_rx = 35.9, phiM_cx = 13.8, phiM_iy = 4.46 kNm, ratios = 0.333, 0.365)")
print("(ANS alternative: phiM_rx = 38.9, phiM_cx = 36.3, phiM_iy = 4.77 kNm, ratios = 0.0972, 0.174)")

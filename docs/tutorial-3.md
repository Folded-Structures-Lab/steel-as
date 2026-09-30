
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

As introduced in the [Quick Start](tutorial-1.md) section, *steelas* creates a structural member using  the *SteelMember* class. The member class defines general AS4100 section and member design attributes and methods and is intended to evaluate the design capacities of structural steel. The current toolbox version including evaluation of tension, compression, bending, shear, and combined actions capacities.

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


## Combined Actions

Section and member capacities for combined axial force and bending are evaluated as per AS 4100 Section 8. The *SteelMember* methods below take the design axial force `N_star` (kN, tension positive and compression negative) and return nominal moment capacities (kNm), to be checked as $M^* \le \phi M$. The biaxial bending methods return an interaction ratio, which is satisfied if it does not exceed 1.

| Method | AS 4100 Clause | Description |
|---|---|---|
| `M_rx`, `M_ry` | 8.3.2, 8.3.3 | section moment capacity reduced by axial force |
| `section_biaxial_ratio` | 8.3.4 | section capacity, biaxial bending |
| `M_ix`, `M_iy` | 8.4.2 | in-plane member moment capacity |
| `M_ox` | 8.4.4 | out-of-plane member moment capacity |
| `M_cx` | 8.4.5 | lesser of `M_ix` and `M_ox` |
| `member_biaxial_ratio` | 8.4.5 | member capacity, biaxial bending |

For compression members, the general expressions are:
$$
M_{rx} = M_{sx} \left(1 - \frac{N^*}{\phi N_s}\right), \quad
M_{ix} = M_{sx} \left(1 - \frac{N^*}{\phi N_{cx}}\right), \quad
M_{ox} = M_{bx} \left(1 - \frac{N^*}{\phi N_{cy}}\right)
$$

For tension members, $\phi N_t$ replaces $\phi N_s$, $M_{ix} = M_{rx}$, and $M_{ox} = M_{bx} (1 + N^*/\phi N_t) \le M_{rx}$.

### Alternative Capacities

Passing `alternative=True` to the above methods uses the alternative (higher capacity) expressions where the section satisfies the clause requirements, and the general expressions otherwise:

| Clause | Sections | Requirements |
|---|---|---|
| 8.3.2(a) | UB, UC, WB, WC, RHS, SHS | compact about x-axis; tension, or compression with $k_f = 1$ |
| 8.3.2(b) | UB, UC, WB, WC, RHS, SHS | compact about x-axis; compression with $k_f < 1$ |
| 8.3.3(a) | UB, UC, WB, WC | compact about y-axis |
| 8.3.3(b) | RHS, SHS | compact about y-axis |
| 8.3.4 | UB, UC, WB, WC, RHS, SHS | compact about both axes |
| 8.4.2.2 | UB, UC, WB, WC, RHS, SHS | compact about the bending axis; compression with $k_f = 1$ |
| 8.4.4.1.2 | UB, UC, WB, WC | compact about x-axis; compression with $k_f = 1$; no transverse load; full or partially restrained both ends |

The alternative member capacities use the following *SteelMember* attributes:

| Attribute | Description |
|---|---|
| `l` | member length, required for Clause 8.4.2.2, where $N_c$ is limited to its value for $k_e = 1$ |
| `l_z` | distance between torsional restraints, required for Clause 8.4.4.1.2 |
| `beta_mx`, `beta_my` | ratio of end moments $\beta_m$, positive for reverse curvature (default -1, uniform moment) |
| `transverse_load` | set to `False` if the member has no transverse load (Clause 8.4.4.1.2) |
| `end_i_restraint`, `end_j_restraint` | set to `True` if the respective end is fully or partially restrained (Clause 8.4.4.1.2) |


Input and evaluation of combined actions using *steelas* is detailed further with reference to the following example, with answers from hand calculation.

> Determine the general and alternative combined actions capacities for a 3.0m 150UB18.0 Grade 300 beam-column, braced in-plane with $k_e = 0.7$, with $N^* = 50$ kN compression, $M_x^* = 5$ kNm, $M_y^* = 1$ kNm, $\alpha_m = 1.3$, $\beta_{mx} = 0.5$, $\beta_{my} = 0$, and no transverse load.
```
from steelas.member.member import SteelSection, SteelMember

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
```


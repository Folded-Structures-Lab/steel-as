
# Tension and Compression Capacity

Python code for the following examples are available in the Github repository [examples folder](https://github.com/Folded-Structures-Lab/timber-as/tree/main/examples/tutorial_3.py). 

Several examples on this page are sourced from the *Timber Design Handbook* ([Standards Australia HB 108 - 2013](https://infostore.saiglobal.com/en-us/standards/sa-hb-108-2013-119982_saig_as_as_251451/)), written by Geoffrey Boughton and Keith Crews.


## Member Design Capacities

As introduced in the [Quick Start](tutorial-1.md) section, *timberas* creates a structural member using *timberas.member* module classes. This module defines a parent class *TimberMember* with general AS1720.1 member design attributes and methods. Additional child classes (e.g. *BoardMember*) are defined for particular member with additional relevant methods (e.g. slenderness coefficients relevant only for rectangular members).

Member classes are primarily intended to evaluate the design capacities of structural timber, with the current toolbox version including evaluation of tension, compression, bending, and shear capacities.


## Tension Capacity

The design tensile capacity of timber members as per AS1720.1 Clause 3.4.1 is:
$$
N_{dt} = \phi k_1 k_4 k_6 f_t A_t
$$
Input and evaluation of tension design parameters using *timberas* is detailed further with reference to the following example.

*Example 3.3, Timber Design Handbook (page 188)*:
> 
> A 190 x 35 MGP10 member is to be used as an internal principal member in a Brisbane stadium. The member end connections introduce 2 x 22mm diameter holes through the cross-section of the member. Evaluate the design tensile capacity for:  
> (a) a 50+ years duration load only; and  
> (b) a wind load combination

Solution: 
```
from timberas.geometry import TimberSection as TS
from timberas.material import TimberMaterial as TM
from timberas.member import BoardMember, DurationFactorStrength

# create a section and remove bolt holes from section tensile area
sec = TS.from_library("190x35")
sec.A_t = sec.A_g - 2 * 22 * sec.b
print(sec.A_t)

# create a material and update properties from the section size
mat = TM.from_library("MGP10")
mat.update_from_section_size(sec.d)
print(mat.f_t)

# create a member
member = BoardMember(
    sec=sec, 
    mat=mat, 
    application_cat=2, 
    k_1=0.57, 
    high_temp_latitude=False
)

# output
member.report(["k_1", "N_dt"])
#(ANS: N_dt = 14.5 kN)"

# 3.3(b) update member load duration factor and output
member.update_k_1(DurationFactorStrength.FIVE_SECONDS)
member.report(["k_1", "N_dt"], with_nomenclature=True, with_clause=True)
```

Net cross-sectional area $A_t$ is a *TimberSection* attribute. It is calculated initially as equal to gross area $A_g$, but can be updated by user input:
```
# create a section and remove bolt holes from section tensile area
sec = TS.from_library("190x35")
sec.A_t = sec.A_g - 2 * 22 * sec.b
print(sec.A_t)
```
Characteristic tensile strength $f_t$ is a *TimberMaterial* attribute:
```
# create a material and update properties from the section size
mat = TM.from_library("MGP10")
mat.update_from_section_size(sec.d)
print(mat.f_t)
```
A *BoardMember* is created with a section, material, and additional input parameters:
```
# create a member
member = BoardMember(
    sec=sec, 
    mat=mat, 
    application_cat=2, 
    k_1=0.57, 
    high_temp_latitude=False
)
```
Remaining tension design parameters are derived from these inputs as follows:

- Capacity factor $\phi$ is evaluated from the application category (*application_cat*) parameter and material, as discussed above. 
- Load duration factor $k_1$ (Ref. Cl 2.4.1.1) is input directly. 
- Temperature/humidity effect factor $k_6$ (Ref Cl 2.4.3) is evaluated from the *high_temp_latitide* parameter (default = False for $k_6$ = 1.0),
- In-service moisture change (partial seasoning) factor $k_4$ (Ref Cl 2.4.2) is evaluated based on the $mat.seasoned$ attribute (True/False) and is only relevant ($k_4 != 1.0) for some use cases of unseasoned timber. This is discussed further in the bottom example on this page. 


The *member.report()* method is used to print a formatted report of the requested attribute names.
```
# output
member.report(["k_1", "N_dt"])
```

The *member.update_k_1()* method can be used to change the load duration factor and resolve member capacities:
```
# 3.3(b) update member load duration factor and output
member.update_k_1(DurationFactorStrength.FIVE_SECONDS)
member.report(["k_1", "N_dt"], with_nomenclature=True, with_clause=True)
```
The additional parameters of the *member.report()* function are used to enable additional detail in the printed report (attribute nomenclature and relevant clause(s) in AS1720.1). 

## Compression Capacity

The design compression capacity of timber member (parallel to grain) as per AS1720.1 Clause 3.3.1 is:
$$
N_{d,c} = \phi k_1 k_4 k_6 k_{12} f_c A_c
$$

The stability factor for lateral bucking under compression $k_{12}$ (Ref. Cl 3.3.3) accounts for the potential of buckling failure about $x$ or $y$ axes. Thus, *timberas* evaluates stability and compressive capacity about both axes, using then then minimum as the governing design compressive capacity:
$$
N_{d,cx} = \phi k_1 k_4 k_6 k_{12,x} f_c A_c
$$
$$
N_{d,cy} = \phi k_1 k_4 k_6 k_{12,y} f_c A_c
$$

Input and evaluation of compression design parameters using *timberas* is detailed further with reference to the following example.


*Example 4.1, Timber Design Handbook (page 235)*:
> 
> A 2.8m long, 190 x 35 MGP10 member is to be used as an internal principal member in a Brisbane stadium. Member end connections are bolted as per Example 3.3 and there is no intermediate lateral restraint in either direction.   

> (a) Evaluate the design compression capacity for a wind load combination.  
> (b) Compare the slenderness reduction factor S3 for pinned or semi-rigid end conditions.

Solution 4.1(a): 
```
from timberas.geometry import TimberSection as TS
from timberas.material import TimberMaterial as TM
from timberas.member import BoardMember, EffectiveLengthFactor

#create a section
sec = TS.from_library("190x35")

#create a material and update properties from the section size
mat = TM.from_library("MGP10")
mat.update_from_section_size(sec.d)

# assume pinned-pinned end fixity
g_13 = EffectiveLengthFactor.PINNED_PINNED

# create member
member_dict = {
    "sec": sec,
    "mat": mat,
    "application_cat": 2,
    "r": 1.0,
    "k_1": 1.0,
    "g_13": g_13,
    "L": 2800,
}
member = BoardMember(**member_dict)
# output
member.report(["g_13", "N_dcx", "N_dcy"])
member.report(["S3", "S4", "k_12_c", "N_dc"])
# (Ans: S3 = 14.7, S4 = 80, k_12_c = 0.042, N_dc = 3.54 kN)
```

Compression design parameters are derived from member inputs as follows:

- $\phi$, $k_1$, $k_4$, $k_6$ as described above for tension capacity.
- Cross-sectional column area $A_c$ is a *TimberSection* attribute. It is calculated initially as equal to gross area $A_g$, but can be updated by user input.  
- Characteristic tensile strength $f_c$ is a *TimberMaterial* attribute.
-  Stability factors for x-axis *k_12_x* and y-axis *k_12_y* buckling are derived from:
    - Material constant $\rho_C$ - requires a load-dependent ratio parameter $r$ (temporary design action / permanent design action).
    - Slenderness coefficients for x-axis *S_3* and y-axis *S_4* - requires member length *L* and effective length factor *g_13*. 
    - Intermediate lateral restraint will be discussed in the next section.

The effective length factor can be input as a numerical value, or using the *EffectiveLengthFactor* enum class, which includes factors for end restraint conditions listed in AS1720.1 Table 3.2. 

Effective length factors can also be input for both x and y directions using a dictionary input for *g_13*. For example, extending the above code for Solution 4.1(b):
```
#(b) update end fixity - assume as semi-rigid from bolt group
member.g_13 = {
    "x": EffectiveLengthFactor.BOLTED_END_RESTRAINT,
    "y": EffectiveLengthFactor.PINNED_PINNED,
}
# resolve member capacities
member.solve_capacities()
# output
member.report(["g_13", "S3", "N_dcx", "S4", "N_dcy"], with_nomenclature=False)
#(ANS S3 = 11.1)
```
The *member.solve_capacities()* method recalculates member capacities using the updated effective length factor. 


## Lateral Restraint

The following example is used to show further detail *timberas* usage for unseasoned member capacity evaluation and specification of lateral restraint against compressive buckling.

*Example 4.3, Timber Design Handbook (page 255)*:
> 
> Evaluate the design compression capacity of stud elements in a load-bearing timber stud wall, 
> for a governing self-weight (long-term duration) load-case. Studs are 150 x 50 unseasoned F7 
> timber and 3.3m high. Assume noggins are placed to provide lateral restraint:
> 
> (a) at mid-height; or  
> (b) at one-third and two-third height.


Solution 4.3:
```
from timberas.geometry import TimberSection as TS, ShapeType
from timberas.material import TimberMaterial as TM
from timberas.member import BoardMember, ApplicationCategory, EffectiveLengthFactor

#(a) stud wall, 1650mm noggins
member_dict = {
    "sec": TS(d=147, b=47, name="Nominal 150 x 50", shape_type=ShapeType.SINGLE_BOARD),
    "mat": TM.from_library("F7 Unseasoned Softwood"),
    "application_cat": ApplicationCategory.SECONDARY_MEMBER,
    "high_temp_latitude": False,
    "consider_partial_seasoning": True,
    "k_1": 0.57,
    "r": 0,
    "g_13": EffectiveLengthFactor.FRAMING_STUDS,
    "L": 3300,
    "L_a": {"x": None, "y": 1650},
}
member = BoardMember(**member_dict)
member.report(["L_ax", "L_ay", "k_4"])
member.report(["S3", "S4", "k_12_c", "N_dc", "N_dcx", "N_dcy"])
#(ANS: S3 = 20.1, S4 = 35.1, k_12_c = 0.139, N_dc = 7.05 kN)

#(b) increase capacity from additional lateral restraint L_ay = 1100 mm
member.L_a = {"x": None, "y": 1100}
member.solve_capacities()
member.report(["L_ax", "L_ay"])
member.report(["N_dcx", "N_dcy", "N_dc"])
#(ANS: N_dcx = 21.3, N_dcy = 15.9)

```

As the section will be used with an unseasoned material, minimum tolerance dimensions are used for creating the section property, rather than nominal dimensions:
```
"sec": TS(d=147, b=47, name="Nominal 150 x 50", shape_type=ShapeType.SINGLE_BOARD)
```

The partial seasoning factor $k_4$ becomes a relevant consideration for unseasoned timber. The *consider_partial_seasoning* parameter is used to including partial seasoning ($k_4 \geq 1.0) in member capacity evaluation:
```
"consider_partial_seasoning": True
```

The effective buckling length of compressive elements may be reduced with use of rigid restraints against lateral movement. Distance between lateral restraints is input with the *L_a* parameter:
```
"L_a": {"x": None, "y": 1650}
```
The input is a dictionary with values for restraint distances against buckling about x and y axes. If a `None` value is provided, lateral restraint distance is assumed as equal to member length *L*. If *L_a* is input as a single float value, i.e. not as a dictionary, the value is assumed as the restraint distance for both x and y directions.

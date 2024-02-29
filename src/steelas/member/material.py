# -*- coding: utf-8 -*-
"""
These scripts calculate AS steel material properties based on section geometry (used for plate components and sections)

@author: uqjgatta
"""

import numpy as np
from math import isnan
from dataclasses import dataclass
from typing import Callable


@dataclass(kw_only=True)
class SteelMaterial:
    grade: str = "GR300"
    mat_type: str = "HotRolledSection"
    name: str = ""
    f_y: float = 0  # yield stress used in design
    f_u: float = 0  # tensile strength used in design

    res_stress: str = "HR"

    # attr for closed sections
    t: float = np.nan  # plate thickness

    # attrs for open sections
    t_f: float = np.nan
    t_w: float = np.nan
    f_yw: float = np.nan

    def __post_init__(self):
        self.solve_mat()

    def solve_mat(self):
        if not isnan(self.t):
            self.f_y = self._f_y(self.t)
        if not isnan(self.t_f):
            self.f_y = self._f_y(self.t_f)
        if not isnan(self.t_w):
            self.f_yw = self._f_y(self.t_w)

        self.f_u = self._f_u()
        self.res_stress = self._res_stress()

    @property
    def density(self) -> int:
        """Density of Steel, kg/m^3"""
        return 7850
    
    @property
    def E(self) -> int:
        """Modulus of Elasticity, AS4100 Cl 2.2.4"""
        return 200000

    @property
    def G(self) -> int:
        """Shear modulus of Elasticity, AS4100 Cl 2.2.4"""
        return 80000

    @property
    def v(self) -> float:
        """Poisson's Ratio, AS4100 Cl 2.2.4"""
        return 0.25

    @property
    def alpha_T(self) -> float:
        """Coefficient of Thermal Expansion, AS4100 Cl 2.2.4"""
        return 11.7e-6

    def _fu_method(self) -> Callable:
        _, fu_method = material_type_functions(self.mat_type)
        return fu_method

    def _f_u(self) -> float:
        return self._fu_method()(self.grade)

    def _fy_method(self) -> Callable:
        fy_method, _ = material_type_functions(self.mat_type)
        return fy_method

    def _f_y(self, t) -> float:
        return self._fy_method()(self.grade, t)

    def _res_stress(self) -> str:
        match self.mat_type:
            case "HollowSection":
                r = "CF"
            # case 'HotRolledFlats'   -> Not Implemented AS1594
            case "HotRolledPlate":
                r = "HR"
            case "HotRolledSection":
                r = "HR"
            #'HotRolledBar'     -> Not Implemented AS3679.1
            #'PressurePlate'    -> AS3597
            case "WeldedSection":
                r = "HW"
        return r

    @classmethod
    def from_dict(cls, **kwargs):
        """construct object from attribute dict. overrides derived attribute values otherwise calculated in __post_init__"""
        o = cls()
        for k, v in kwargs.items():
            # note - @property items are in hasattr but not in __annotations__)
            # if hasattr(o, k) and (k in cls.__annotations__):
            if k in o.__dict__:  # note - __dict__ includes parent class attrs
                setattr(o, k, v)

        if isnan(o.f_y) | isnan(o.f_yw):
            # if material yield strengths are not present from cls() and dictionary override, add them here
            o.solve_mat()

        return o


# -----------------------------
#    AS1163 Hollow Sections
# -----------------------------


def AS1163_fy(grade: str, t: float = np.nan) -> int:
    """returns the yield stress fy of steel material grades as per
    AS1163 (pressure vessel steel)"""

    # NOTE - t input is unused - added to suppress as typehint error

    # AS4100 TABLE 2.1
    match grade:
        case "C450":
            fy = 450
        case "C350":
            fy = 350
        case "C250":
            fy = 250
        case _:
            raise ValueError("unknown material grade")
    return fy


def AS1163_fu(grade: str, t: float = np.nan) -> int:
    """returns the tensile strength fu of steel material grades as per
    AS1163 (pressure vessel steel)"""

    # NOTE - t input is unused - added to suppress as typehint error

    # AS4100 TABLE 2.1
    match grade:
        case "C450":
            fu = 500
        case "C350":
            fu = 430
        case "C250":
            fu = 320

        case _:
            raise ValueError("unknown material grade")
    return fu


# -----------------------------
#   AS1594 Hot-Rolled Flats
# -----------------------------

# -----------------------------------------
# AS3678 Hot-Rolled Plates and Floorplates
# -----------------------------------------


def AS3678_fy(grade: str, t: float = np.nan) -> int:  # add grade as variable
    """returns the yield stress fy of steel material grades as per
    AS3678 (hot-rolled plates, floor plates, and slabs"""

    if t is np.nan:
        raise ValueError("please provide a plate thickness t")

    # AS3678 in AS4100 TABLE 2.1
    if grade == "GR450":
        if t <= 20:
            fy = 450
        elif t <= 32:
            fy = 420
        elif t <= 50:
            fy = 400

    if grade == "GR400":
        if t <= 12:
            fy = 400
        elif t <= 20:
            fy = 380
        elif t <= 80:
            fy = 360

    elif grade == "GR350":
        if t <= 12:
            fy = 360
        elif t <= 20:
            fy = 350
        elif t <= 80:
            fy = 340
        elif t <= 150:
            fy = 330

    elif grade == "WR350":
        if t <= 50:
            fy = 340

    elif grade == "GR300":
        if t <= 8:
            fy = 320
        elif t <= 12:
            fy = 310
        elif t <= 20:
            fy = 300
        elif t <= 50:
            fy = 280
        elif t <= 80:
            fy = 270
        elif t <= 150:
            fy = 260

    elif grade == "GR250":
        if t <= 8:
            fy = 280
        elif t <= 12:
            fy = 260
        elif t <= 50:
            fy = 250
        elif t <= 80:
            fy = 240
        elif t <= 150:
            fy = 230

    elif grade == "GR200":
        if t <= 12:
            fy = 200

    else:
        raise ValueError("unknown material grade")

    return fy


def AS3678_fu(grade: str, t: float = np.nan) -> int:
    """returns the tensile strength f_u of steel material grades as per
    AS3678 (hot-rolled plates, floor plates, and slabs)"""

    # NOTE - t input is unused - added to suppress as typehint error

    # AS3678 in AS4100 TABLE 2.1
    match grade:
        case "GR450":
            raise NotImplementedError  # thickness-dependent
        case "GR400":
            fu = 480
        case "GR350":
            fu = 450
        case "WR350":
            fu = 450
        case "GR300":
            fu = 430
        case "GR250":
            fu = 410
        case "GR200":
            fu = 300
        case _:
            raise ValueError("unknown material grade")
    return fu


# --------------------------------------
# AS3679.1 Hot-Rolled Bars and Sections
# --------------------------------------


def AS3679_sections_fy(grade: str, t: float = np.nan) -> int:
    """returns the yield stress fy of steel material grades as per
    AS3679.1 (hot-rolled sections and bars)"""

    if t is np.nan:
        raise ValueError("please provide a plate thickness t")

    # AS3679.1 in AS4100 TABLE 2.1
    if grade == "GR350":
        if t <= 11:
            fy = 360
        elif t < 40:
            fy = 340
        elif t >= 40:
            fy = 330
    elif grade == "GR300":
        if t < 11:
            fy = 320
        elif t <= 17:
            fy = 300
        elif t > 17:
            fy = 280
    else:
        raise ValueError("unknown material grade")
    return fy


def AS3679_sections_fu(grade: str, t: float = np.nan) -> int:
    """returns the tensile strength fu of steel material grades as per
    AS3679.1 (hot-rolled sections and bars)"""

    # NOTE - t input is unused - added to suppress as typehint error

    # AS3679.1 in AS4100 TABLE 2.1
    match grade:
        case "GR350":
            fu = 480
        case "GR300":
            fu = 440
        case _:
            raise ValueError("unknown material grade")
    return fu


# -----------------------------
# AS3597 Pressure Vessel Steel
# -----------------------------


def AS3597_fy(grade: str, t: float = np.nan) -> int:
    """returns the yield stress fy of steel material grades as per
    AS3597 (pressure vessel steel)"""

    # AS3597 in AS4100 TABLE 2.1
    match grade:
        case "PR500":
            fy = 500
        case "PR600":
            fy = 600
        case "PR700":
            if t is not None:
                if t <= 5:
                    fy = 650
                elif t < 65:
                    fy = 690
                elif t >= 110:
                    fy = 620
            else:
                raise ValueError("please provide material thickness")
        case _:
            raise ValueError("unknown material grade")
    return fy


def AS3597_fu(grade: str, t: float = np.nan) -> int:
    """returns the tensile strength fu of steel material grades as per
    AS3597 (pressure vessel steel)"""

    # AS3679.1 in AS4100 TABLE 2.1
    match grade:
        case "PR500":
            fu = 590
        case "PR600":
            fu = 690
        case "PR700":
            if t is not None:
                if t <= 5:
                    fu = 750
                elif t < 65:
                    fu = 790
                elif t >= 110:
                    fu = 720
            else:
                raise ValueError("please provide material thickness")
        case _:
            raise ValueError("unknown material grade")
    return fu


# ----------------
#   Functions
# ----------------


def material_type_functions(mat_type: str) -> tuple[Callable, Callable]:
    """returns functions for fy and fu from given material type
    'HollowSection'    -> AS1163
    'HotRolledFlats'   -> Not Implemented AS1594
    'HotRolledPlate'   -> AS3678
    'HotRolledSection' -> AS3679.1
    'HotRolledBar'     -> Not Implemented AS3679.1
    'PressurePlate'    -> AS3597
    'WeldedSection'    -> Not Implemented AS3679.2 (uses HotRolledPlates)
    AS1594, AS3679_bars Not Implemeted
    """

    match mat_type:
        case "HollowSection":
            fy_method = AS1163_fy
            fu_method = AS1163_fu
        case "HotRolledPlate":
            fy_method = AS3678_fy
            fu_method = AS3678_fu
        case "HotRolledSection":
            fy_method = AS3679_sections_fy
            fu_method = AS3679_sections_fu
        case "PressurePlate":
            fy_method = AS3597_fy
            fu_method = AS3597_fu
        case "WeldedSection":
            # uses HotRolledPlate
            fy_method = AS3678_fy
            fu_method = AS3678_fu

    return fy_method, fu_method


def calc_mat_prop(mat_type, grade, t):
    if "Section" in mat_type or "Bar" in mat_type:
        f_y = AS3679_sections_fy(grade, t)
        f_u = AS3679_sections_fu(grade)
    elif "Plate" in mat_type:
        f_y = AS3678_fy(grade, t)
        f_u = AS3678_fu(grade)
    return f_y, f_u


def main():
    f_y, f_u = calc_mat_prop("HotRolledSection", "GR300", 8)
    print("\nMaterial lookup functions:")
    print(f_y, f_u)

    m = SteelMaterial(grade="GR300", mat_type="HotRolledSection", t=10)
    print("\nClosed section steel materials:")
    print(m)

    m2 = SteelMaterial(grade="GR300", mat_type="HotRolledSection", t_f=12, t_w=8)
    print("\nOpen section steel materials:")
    print(m2)

    from pathlib import Path
    import pandas as pd

    path = Path(__file__)
    input_data = str(path.parent.parent) + "\\input_data\\AUS_open_sections.csv"

    section_df = pd.read_csv(input_data, skiprows=[1])
    section_df = section_df.apply(pd.to_numeric, errors="ignore").fillna(0)
    section_dict = section_df.iloc[2].to_dict()

    mat3 = SteelMaterial.from_dict(**section_dict)
    print("\nMaterial from library lookup:")
    print(mat3)


if __name__ == "__main__":
    main()

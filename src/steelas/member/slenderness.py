# -*- coding: utf-8 -*-
"""
Created on Wed Jun  1 09:05:37 2022

@author: uqjgatta
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple
import numpy as np
from math import pi, isnan, floor, log10

# from structuraldesigntoolbox.
from steelas.member.material import SteelMaterial
from steelas.member.geometry import SectionGeometry
from steelas.data.io import report


@dataclass(kw_only=True)
class SteelSlenderness:
    # AS4100 Cl 5.2.2, 5.2.3, 5.2.5, 5.2.5
    geom: SectionGeometry | None = None
    mat: SteelMaterial | None = None
    # TODO - don't store geom and mat as attrs?

    name: str = ""  # section name  (shape + material)
    section: str = ""  # section shape
    grade: str = ""  # material

    components_x: list[PlateComponent] = field(default_factory=list, repr=False)
    components_y: list[PlateComponent] = field(default_factory=list, repr=False)
    # compression components
    components_c: list[PlateComponent] = field(default_factory=list, repr=False)

    compact_x: str = field(repr=False, default="")
    compact_y: str = field(repr=False, default="")

    lam_s_x: float = field(repr=False, default=0)  # section slenderness
    lam_sp_x: float = field(repr=False, default=0)  # section slenderness
    lam_sy_x: float = field(repr=False, default=0)  # section slenderness

    lam_s_y: float = field(repr=False, default=0)  # section slenderness
    lam_sp_y: float = field(repr=False, default=0)  # section slenderness
    lam_sy_y: float = field(repr=False, default=0)  # section slenderness

    Z_ex: float = 0
    Z_ey: float = 0
    k_f: float = 0
    A_e: float = 0

    alpha_b: float = 0
    web_shear_yield_governs: bool = True
    alpha_v: float = 0

    slender_section_type_x: int = 1  # determines which equation in Cl 5.2.5 is used

    # round values to a number of significant figures
    sig_figs: int = 3

    def __post_init__(self):
        if self.geom is not None and self.mat is not None:
            self.name = self.geom.name
            self.grade = self.mat.grade
            self.section = self.geom.section
            match self.geom.sec_type:
                case "UB" | "UC" | "WB" | "WC":
                    components_method = i_section_components
                case "PFC" | "TFB":
                    components_method = c_section_components
                case "SHS" | "RHS":
                    components_method = rhs_section_components
                case "CHS":
                    components_method = chs_section_components
                case "BT" | "CT":
                    components_method = t_section_components
                case "RectPlate":
                    components_method = rect_section_components
                case other:
                    raise NotImplementedError(
                        f"section type {self.geom.sec_type} not available"
                    )
            self.components_x, self.components_y, self.components_c = components_method(
                self.geom, self.mat
            )
            self.solve_slenderness()

            # round to sig figs
            if self.sig_figs:
                for k, v in list(self.__dict__.items()):
                    if isinstance(v, (float, int)) and (not isnan(v)) and (v != 0):
                        setattr(
                            self,
                            k,
                            round(v, self.sig_figs - int(floor(log10(abs(v)))) - 1),
                        )

    def solve_slenderness(self):
        # compact_x
        # compact_y

        # AS4100 Cl5.2.2.
        # lam_sp and lam_sy are values from element with greatest lam_s = lem_e/lam_ey
        max_lam_e_ratio = 0
        for p in self.components_x:
            if p.lam_e_ratio > max_lam_e_ratio:
                max_lam_e_ratio = p.lam_e_ratio
                self.lam_s_x = p.lam_e
                self.lam_sp_x = p.lam_ep
                self.lam_sy_x = p.lam_ey

                if isinstance(p, RingComponent):
                    self.slender_section_type_x = 3
                elif p.edge_sup == "One" and p.load_type == "CompToTens":
                    self.slender_section_type_x = 2
                else:
                    self.slender_section_type_x = 1

        max_lam_e_ratio = 0
        for p in self.components_y:
            if p.lam_e_ratio > max_lam_e_ratio:
                max_lam_e_ratio = p.lam_e_ratio
                self.lam_s_y = p.lam_e
                self.lam_sp_y = p.lam_ep
                self.lam_sy_y = p.lam_ey

                # slender section type for y components not implemented

        self.Z_ex = self._Z_ex()
        self.Z_ey = self._Z_ey()
        self.A_e = self._A_e()
        self.k_f = self._k_f()
        self.alpha_b = self._alpha_b()
        self.web_shear_yield_governs = self._web_shear_yield_governs()
        self.alpha_v = self._alpha_v()

    def report(self, **kwargs) -> None:
        report(
            self,
            exclude_attribute_names=[
                "geom",
                "mat",
                "components_x",
                "components_y",
                "components_c",
            ],
            **kwargs,
        )

    def _A_e(self):
        A_e = 0
        A_e += self.geom.A_g
        for p in self.components_c:
            A_e -= p.A_v
        #    A_e += p.A_e
        return A_e

    def _k_f(self) -> float:
        return self.A_e / self.geom.A_g

    def _Z_ex(self) -> float:
        # AS4100 Cl5.2
        if self.lam_s_x <= self.lam_sp_x:
            self.compact_x = "C"
            return self._Z_excompact
        elif self.lam_s_x <= self.lam_sy_x:
            self.compact_x = "N"
            return self._Z_exnoncompact
        else:
            self.compact_x = "S"
            return self._Z_exslender

    def _Z_ey(self) -> float:
        # AS4100 Cl 5.2
        if self.lam_s_y <= self.lam_sp_y:
            self.compact_y = "C"
            return self._Z_eycompact
        elif self.lam_s_y <= self.lam_sy_y:
            self.compact_y = "N"
            return self._Z_eynoncompact
        else:
            self.compact_y = "S"
            return self._Z_eyslender

    @property
    def _Z_excompact(self) -> float:
        # AS4100 Cl 5.2.3
        return min(self.geom.S_x, 1.5 * self.geom.Z_x)

    @property
    def _Z_eycompact(self) -> float:
        # AS4100 Cl 5.2.3
        return min(self.geom.S_y, 1.5 * self.geom.Z_y)

    @property
    def _Z_exnoncompact(self) -> float:
        # AS4100 Cl 5.2.4
        return self.geom.Z_x + (self.lam_sy_x - self.lam_s_x) / (
            self.lam_sy_x - self.lam_sp_x
        ) * (self._Z_excompact - self.geom.Z_x)

    @property
    def _Z_eynoncompact(self) -> float:
        # AS4100 Cl 5.2.4
        return self.geom.Z_y + (self.lam_sy_y - self.lam_s_y) / (
            self.lam_sy_y - self.lam_sp_y
        ) * (self._Z_eycompact - self.geom.Z_y)

    @property
    def _Z_exslender(self) -> float:
        # AS4100 Cl 5.2.5
        # TODO - do this properly
        if self.slender_section_type_x == 1:
            if self.geom.sec_type not in ["RHS", "SHS"]:
                z = self.geom.Z_x * self.lam_sy_x / self.lam_s_x
            else:
                # https://www.steelforlifebluebook.co.uk/explanatory-notes/bs5950/effective-properties/
                # BS 5950-1 3.6.2.2?
                d = self.geom.d
                b = self.geom.b
                t = self.geom.t
                A = self.geom.A_g

                eps = (275 / self.mat.f_y) ** 0.5

                k = b - 35 * t * eps - 5 * t

                y_xeff = (A * d - k * t**2) / (2 * (A - k * t))
                A_eff = A - k * t
                I_ex = (
                    self.geom.I_x
                    - k * t**3 / 12
                    - k * t * (d / 2 - t / 2) ** 2
                    - A_eff * (y_xeff - d / 2) ** 2
                )

                z = I_ex / y_xeff

        elif self.slender_section_type_x == 2:
            z = self.geom.Z_x * (self.lam_sy_x / self.lam_s_x) ** 2
        elif self._web_shear_slenderness_ratio == 3:
            raise NotImplementedError("Slender CHS sections not implemented")
        return z

    @property
    def _Z_eyslender(self) -> float:
        # AS4100 Cl 5.2.5
        # TODO - do this properly
        if self.geom.sec_type not in ["RHS", "SHS"]:
            Z_ey = self.geom.Z_y * self.lam_sy_y / self.lam_s_y
        else:
            # https://www.steelforlifebluebook.co.uk/explanatory-notes/bs5950/effective-properties/
            # BS 5950-1 3.6.2.2?
            d = self.geom.d
            b = self.geom.b
            t = self.geom.t
            A = self.geom.A_g

            eps = (275 / self.mat.f_y) ** 0.5
            k = d - 35 * t * eps - 5 * t

            x_xeff = (A * b - k * t**2) / (2 * (A - k * t))
            A_eff = A - k * t
            I_ey = (
                self.geom.I_y
                - k * t**3 / 12
                - k * t * (b / 2 - t / 2) ** 2
                - A_eff * (x_xeff - b / 2) ** 2
            )

            Z_ey = I_ey / x_xeff

        return Z_ey

    def _alpha_b(self) -> float:
        """AS4100 Table 6.3.3A, member section constant"""
        return self._member_section_constant(geom=self.geom, k_f=self.k_f)

    @staticmethod
    def _member_section_constant(geom: SectionGeometry, k_f: float = 0) -> float:
        """AS4100 Table 6.3.3(A) and 6.3.3(B)"""
        if k_f < 1:
            # T6.3.3(B)
            match geom.sec_type:
                case "SHS" | "RHS" | "CHS":
                    a = -0.5
                case "UB" | "UC":
                    t_f = geom.t_f
                    a = 0 if t_f <= 40 else 0.5
                case "WB" | "WC":
                    t_f = geom.t_f
                    a = 0.5 if t_f <= 40 else 1.0
                case other:
                    a = 1.0
        else:  # k_f = 1
            # T6.3.3(A)
            match geom.sec_type:
                case "SHS" | "RHS" | "CHS":
                    a = -1
                    # NOTE: stress relief considerations not implemented
                case "UB" | "UC" | "TFB":
                    t_f = geom.t_f
                    a = 0 if t_f <= 40 else 1.0
                case "PFC" | "BT" | "CT":
                    a = 0.5
                case "WB" | "WC":
                    a = 0.0  # AISC Des. Cap. Tables T6.1
                    # t_f = geom.t_f
                    # a = 0.5 if t_f <= 40 else 1.0
                case other:
                    a = 0.5
                    # raise NotImplementedError(
                    #    f'section {geom.sec_type} not implemented for alpha_b - See T6.3.3(A)')
        return a

    def _web_shear_yield_governs(self) -> bool:
        """AS4100 Cl 5.11.2 web shear slenderness limit check for sections with approximatly uniform web shear stress distribution"""
        web_shear_slenderness_ratio = self._web_shear_slenderness_ratio()

        if web_shear_slenderness_ratio <= 1:
            return False
        else:
            return True

    def _web_shear_slenderness_ratio(self) -> bool:
        """AS4100 Cl 5.11.2 web shear slenderness ratio for sections with approximatly uniform web shear stress distribution"""
        r1 = self.geom.d_p / self.geom.t_w
        if "f_yw" in self.mat.__dict__:
            r2 = 82 / (self.mat.f_yw / 250) ** 0.5
        else:
            r2 = 82 / (self.mat.f_y / 250) ** 0.5
        return r2 / r1

    def _alpha_v(self) -> float:
        """AS4100 5.11.5.1 unstiffened web shear buckling reduction factor"""
        return min((self._web_shear_slenderness_ratio()) ** 2, 1)

    @classmethod
    def column_order(cls) -> list[str]:
        """specifies the reported attributes when output to dataframe"""
        k = list(cls.__annotations__.keys())

        # lam_s_x,  lam_sp_x,  lam_sy_x,  lam_s_y,  lam_sp_y, lam_sy_y,

        n = [
            "section",
            "grade",
            "compact_x",
            "compact_y",
            "Z_ex",
            "Z_ey",
            "k_f",
            "A_e",
            #'lam_s_x', 'lam_sp_x',  'lam_sy_x',  'lam_s_y',  'lam_sp_y', 'lam_sy_y',
            "alpha_b",
            "web_shear_yield_governs",
            "alpha_v",
        ]
        return n  # + [x for x in k if x not in n]

    @classmethod
    def from_dict(cls, **kwargs):
        o = cls()
        # all_ann = cls.__annotations__
        for k, v in kwargs.items():
            # note - @property items are in hasattr but not in __annotations__)
            if hasattr(o, k):  # and (k in cls.__annotations__):
                setattr(o, k, v)
        return o


def i_section_components(geom: SectionGeometry, mat: SteelMaterial):
    """populate components required for slenderness evaluation"""

    # major axis bending
    c_flange_x = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    # TODO - ask ASI about f_y vs f_yf in web slenderness check
    # verification data uses f_y
    # c_web_x = PlateComponent(b=geom.d_1,  t=geom.t_w, f_y=mat.f_yw,
    #                         edge_sup='Both', load_type='CompToTens', res_stress=mat.res_stress)
    c_web_x = PlateComponent(
        b=geom.d_1,
        t=geom.t_w,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    components_x = [c_flange_x, c_web_x]

    # minor axis bending
    c_flange_y = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    # note - web never governs as unsupported outstand width is zero
    # c_web_y = PlateComponent(b=0,  t=self.t_w, f_y = self.f_yw, edge_sup = 'Both', load_type = 'CompToTens', res_stress = self.res_stress)
    components_y = [c_flange_y]  # , c_web_y]

    # compression
    c_flange_c = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    # TODO - as above, f_y vs f_yw in web slenderness check
    c_web_c = PlateComponent(
        b=geom.d_1,
        t=geom.t_w,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    components_c = [c_web_c] + [c_flange_c] * 4

    return components_x, components_y, components_c


def c_section_components(geom: SectionGeometry, mat: SteelMaterial):
    """populate components required for Cee section slenderness evaluation"""

    # major axis bending
    c_flange_x = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    # TODO - ask ASI about f_y vs f_yf in web slenderness check
    # verification data uses f_y
    # c_web_x = PlateComponent(b=geom.d_1,  t=geom.t_w, f_y=mat.f_yw,
    #                         edge_sup='Both', load_type='CompToTens', res_stress=mat.res_stress)
    c_web_x = PlateComponent(
        b=geom.d_1,
        t=geom.t_w,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    components_x = [c_flange_x, c_web_x]

    # minor axis bending
    c_flange_y = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    # note - web never governs as unsupported outstand width is zero
    # f_yw, or f_y
    # note - c_section dir_1 assumed as tension in the web element
    # c_web_y = PlateComponent(b=geom.d_1,  t=geom.t_w, f_y=mat.f_y,
    #                         edge_sup='Both', load_type='UniformComp', res_stress=mat.res_stress)
    components_y = [c_flange_y]  # , c_web_y]

    # compression
    c_flange_c = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    # TODO - as above, f_y vs f_yw in web slenderness check
    c_web_c = PlateComponent(
        b=geom.d_1,
        t=geom.t_w,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    components_c = [c_web_c] + [c_flange_c] * 2

    return components_x, components_y, components_c


def t_section_components(geom: SectionGeometry, mat: SteelMaterial):
    """populate components required for t-section (stem up) slenderness evaluation"""

    # major axis bending
    # c_flange_x = PlateComponent(b=geom.b_ff,  t=geom.t_f, f_y=mat.f_y,
    #                            edge_sup='One', load_type='UniformComp', res_stress=mat.res_stress)
    c_web_x = PlateComponent(
        b=geom.d_1,
        t=geom.t_w,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    components_x = [c_web_x]

    # minor axis bending
    c_flange_y = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    components_y = [c_flange_y]  # , c_web_y]

    # compression
    c_flange_c = PlateComponent(
        b=geom.b_ff,
        t=geom.t_f,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    # TODO - as above, f_y vs f_yw in web slenderness check
    c_web_c = PlateComponent(
        b=geom.d_1,
        t=geom.t_w,
        f_y=mat.f_y,
        edge_sup="One",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    components_c = [c_web_c] + [c_flange_c] * 2

    return components_x, components_y, components_c


def rhs_section_components(geom: SectionGeometry, mat: SteelMaterial):
    # solve slenderness
    c_flange_x = PlateComponent(
        b=geom.b_ff,
        t=geom.t,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    c_web_x = PlateComponent(
        b=geom.d_1,
        t=geom.t,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    components_x = [c_flange_x, c_web_x]

    c_flange_y = PlateComponent(
        b=geom.b_ff,
        t=geom.t,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="CompToTens",
        res_stress=mat.res_stress,
    )
    c_web_y = PlateComponent(
        b=geom.d_1,
        t=geom.t,
        f_y=mat.f_y,
        edge_sup="Both",
        load_type="UniformComp",
        res_stress=mat.res_stress,
    )
    components_y = [c_flange_y, c_web_y]

    # compression
    # PlateComponent(b=self.b_ff,  t=self.t, f_y = self.f_y, edge_sup = 'Both', load_type = 'UniformComp', res_stress = self.res_stress)
    c_flange_c = c_flange_x
    # PlateComponent(b=self.d_1,  t=self.t_w, f_y = self.f_yw, edge_sup = 'Both', load_type = 'UniformComp', res_stress = self.res_stress)
    c_web_c = c_web_y
    components_c = [c_web_c] * 2 + [c_flange_c] * 2

    return components_x, components_y, components_c


def rect_section_components(geom: SectionGeometry, mat: SteelMaterial):
    # solve slenderness
    print(
        "NOTE: AS 4100 does not contain provisions for slenderness of rectangular plates unsupported at both ends - slenderness is not checked (section assumed as compact and k_f =1)"
    )
    components_x = []
    components_y = []
    components_c = []

    return components_x, components_y, components_c


def chs_section_components(
    geom: SectionGeometry, mat: SteelMaterial
) -> Tuple[list[RingComponent], list[RingComponent], list[RingComponent]]:
    # solve slenderness
    c_ring = RingComponent(d_o=geom.d, t=geom.t, f_y=mat.f_y, res_stress=mat.res_stress)
    components_x = [c_ring]
    components_y = [c_ring]
    components_c = [c_ring]

    return components_x, components_y, components_c


def plate_element_slenderness_limit(
    edge_support: str, load_type: str, res_stress: str
) -> Tuple(float, float, float):
    """
    AS4100 Table 5.2 and 6.2.4 - Values of plate element slenderness limits
    Returns:
        lam_ep plasticity limit,
        lam_ey yield limit bending,
        lam_ed deformation limit


    Parameters:
    edge_support = 'One' or 'Both'
    load_type = 'UniformComp', 'CompToTens', or 'CHS'
    res_stress = 'SR', HR', 'LW', 'CF', or 'HW'
    """
    # TODO -> make this a static method of PlateElement?
    if edge_support == "One":
        if load_type == "UniformComp":
            match res_stress:
                case "SR":
                    val = (10, 16, 35)
                case "HR":
                    val = (9, 16, 35)
                case "LW" | "CF":
                    val = (8, 15, 35)
                case "HW":
                    val = (8, 14, 34)
        elif load_type == "CompToTens":
            match res_stress:
                case "SR":
                    val = (10, 25, np.nan)
                case "HR":
                    val = (9, 25, np.nan)
                case "LW" | "CF" | "HW":
                    val = (8, 22, np.nan)
    elif edge_support == "Both":
        if load_type == "UniformComp":
            match res_stress:
                case "SR" | "HR":
                    val = (30, 45, 90)
                case "LW" | "CF":
                    val = (30, 40, 90)
                case "HW":
                    val = (30, 35, 90)
        elif load_type == "CompToTens":
            val = (82, 115, np.nan)
    return val


def ring_element_slenderness_limit(res_stress: str) -> Tuple(
    float, float, float, float
):
    """
    AS4100 Table 5.2 - Values of chs element slenderness limits
    Returns:
        lam_ep plasticity limit,
        lam_ey yield limit,
        lam_eyc yield limit compression,
        lam_ed -> not implemented

    Parameters:
    res_stress = 'SR', HR', 'LW', 'CF', or 'HW'
    """
    # TODO -> make this a static method of RingElement?
    # NOTE Table 5.2 and 6.2.4 lam_ey different for CHS sections
    match res_stress:
        case "SR" | "HR" | "CF":
            val = (50, 120, 82, np.nan)
        case "LW" | "HW":
            val = (42, 120, 82, np.nan)
    return val


@dataclass(kw_only=True)
class PlateComponent:
    """AS4100 Cl5.2.2 Section slenderness - plate components
    AS4100 Cl 6.2.3 Plate element slenderness for compression
    """

    b: float  # clear width of element from supported edge/edges
    t: float  # element thickness
    f_y: float  # element yield stress
    edge_sup: str  # element edge support
    res_stress: str  # section residual stress type
    load_type: str  # element load type

    lam_ey: float = field(init=False)  # element yield limit
    lam_ep: float = field(init=False)  # element plasticity limit
    lam_e: float = field(init=False)  # component slenderness limit
    lam_e_ratio: float = field(init=False)  # component slenderness ratio

    b_e: float = field(init=False)  # plate element effective width Cl 6.2.4
    A_v: float = field(init=False)
    A_e: float = field(init=False)

    def __post_init__(self):
        self.lam_ep, self.lam_ey, _ = plate_element_slenderness_limit(
            self.edge_sup, self.load_type, self.res_stress
        )
        self.lam_e = float(self.b / self.t * (self.f_y / 250) ** 0.5)
        self.lam_e_ratio = self.lam_e / self.lam_ey

        # AS4100 Cl 6.2.4
        self.b_e = min(1, self.lam_ey / self.lam_e) * self.b
        self.A_e = self.b_e * self.t
        self.A_v = (self.b - self.b_e) * self.t
        # CHS -> Not implemented


@dataclass(kw_only=True)
class RingComponent:
    """AS4100 Cl 5.2.2 Section slenderness - chs components
    AS4100 Cl 6.2.3 chs element slenderness for compression
    """

    d_o: float  # clear width of element from supported edge/edges
    t: float  # element thickness
    f_y: float  # element yield stress
    res_stress: str  # section residual stress type

    lam_ey: float = field(init=False)  # element yield limit, bending
    lam_eyc: float = field(init=False)  # element yield limit, compression
    lam_ep: float = field(init=False)  # element plasticity limit
    lam_e: float = field(init=False)  # component slenderness limit
    lam_e_ratio: float = field(init=False)  # component slenderness ratio

    d_e: float = field(init=False)  # plate element effective width Cl 6.2.4
    # A_v: float = field(init=False)
    # A_e: float = field(init=False)

    def __post_init__(self):
        self.lam_ep, self.lam_ey, self.lam_eyc, _ = ring_element_slenderness_limit(
            self.res_stress
        )
        self.lam_e = float(self.d_o / self.t * (self.f_y / 250))
        self.lam_e_ratio = self.lam_e / self.lam_ey

        # AS4100 Cl 6.2.4
        self.d_e = self.d_o * min(
            1, (self.lam_eyc / self.lam_e) ** 0.5, (3 * self.lam_eyc / self.lam_e) ** 2
        )

        # NOTE: unsure if this is the correct effective area calculation
        r_o = self.d_o / 2
        r_i = r_o - self.t
        A_n = pi * (r_o + r_i) * (r_o - r_i)

        r_e = self.d_e / 2
        r_ie = r_e - self.t
        self.A_e = pi * (r_e + r_ie) * (r_e - r_ie)
        self.A_v = A_n - self.A_e


def main():
    from pathlib import Path
    import pandas as pd

    path = Path(__file__)
    input_data = str(path.parent.parent) + "\\input_data\\AUS_open_sections.csv"

    section_df = pd.read_csv(input_data, skiprows=[1])
    section_df = section_df.apply(pd.to_numeric, errors="ignore").fillna(0)
    section_dict = section_df.iloc[2].to_dict()

    geom = SectionGeometry._solve_new(section_dict)
    mat = SteelMaterial.from_dict(**section_dict)

    slenderness = SteelSlenderness(geom=geom, mat=mat)
    print("\nSlenderness attributes for a given section, as per AS4100:")
    print(slenderness)


if __name__ == "__main__":
    main()

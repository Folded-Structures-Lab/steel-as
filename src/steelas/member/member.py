from __future__ import annotations
# Script to calculate the capacity of few different steel sections

# for pi in member buckling
import numpy as np
from dataclasses import dataclass, field
from math import isnan, floor, log10

from steelas.data.io import get_section_from_library, MemberLibrary
from steelas.member.material import SteelMaterial
from steelas.member.geometry import SectionGeometry
from steelas.member.slenderness import SteelSlenderness
from steelas.data.io import report


def reference_buckling_moment(section: SteelSection, l_eb: int) -> float:
    if section.sec_type in ["UB", "UC", "WB", "WC", "PFC"]:
        # AS4100 Cl5.6.1.1 open section with equal flanges
        # Eq 5.6.1.1(3)
        M_o = (
            (np.pi**2 * section.mat.E * section.geom.I_y / l_eb**2)
            * (
                section.mat.G * section.geom.J
                + (np.pi**2 * section.mat.E * section.geom.I_w / l_eb**2)
            )
        ) ** 0.5
    elif section.sec_type in ["RHS", "SHS", "CHS"]:
        # AS4100 Cl5.6.1.4 hollow sections, I_w = 0 #NOTE - THIS IS SAME FORMULA AS ABOVE BUT WITH I_w =0
        M_o = (
            (np.pi**2 * section.mat.E * section.geom.I_y / l_eb**2)
            * (section.mat.G * section.geom.J)
        ) ** 0.5
    else:
        raise NotImplementedError
        # angle sections Cl 5.6.1.3
    # Nmm_to_kn_m = 1/1e6
    return M_o  # * Nmm_to_kn_m


@dataclass(kw_only=True)
class SteelSection:
    geom: SectionGeometry | dict
    mat: SteelMaterial | dict
    slenderness: SteelSlenderness | dict | None

    # TODO solve steel slenderness if not provided?
    def __post_init__(self):
        if type(self.geom) is dict:
            self.geom = SectionGeometry.from_dict(**self.geom)
        if type(self.mat) is dict:
            self.mat = SteelMaterial.from_dict(**self.mat)
        if type(self.slenderness) is dict:
            self.slenderness = SteelSlenderness.from_dict(**self.slenderness)

        if self.slenderness is None:
            self.slenderness = SteelSlenderness(geom=self.geom, mat=self.mat)
        self.slenderness.geom = self.geom
        self.slenderness.mat = self.mat

    def report(self, **kwargs) -> None:
        report(self.geom, **kwargs)
        report(self.mat, **kwargs)
        report(
            self.slenderness,
            exclude_attribute_names=[
                "geom",
                "mat",
                "components_x",
                "components_y",
                "components_c",
            ],
            **kwargs,
        )

    # ----------------
    # Geometry Attrs
    # ----------------
    @property
    def sec_type(self):
        return self.geom.sec_type

    @property
    def A_g(self):
        return self.geom.A_g

    @property
    def A_n(self):
        return self._A_n()

    def _A_n(self):
        return self.geom.A_g

    @property
    def A_w(self):
        return self.geom.A_w

    @property
    def r_x(self):
        return self.geom.r_x

    @property
    def r_y(self):
        return self.geom.r_y

    # ----------------
    # Material Attrs
    # ----------------
    #  f_u f_y f_yw k_f
    @property
    def f_u(self):
        return self.mat.f_u

    @property
    def f_y(self):
        return self.mat.f_y

    @property
    def f_yw(self):
        return self.mat.f_yw

    # @property
    # def k_f(self):
    #     return self.mat.k_f

    # ----------------
    # Slenderness Attrs
    # ----------------
    # Z_ex Z_ey k_f alpha_b web_shear_yield_governs alpha_v

    @property
    def section_name(self):
        return self.slenderness.section

    @property
    def material_name(self):
        return self.slenderness.grade

    @property
    def Z_ex(self):
        return self.slenderness.Z_ex

    @property
    def Z_ey(self):
        return self.slenderness.Z_ey

    @property
    def k_f(self):
        return self.slenderness.k_f

    @property
    def alpha_b(self):
        return self.slenderness.alpha_b

    @property
    def web_shear_yield_governs(self):
        return self.slenderness.web_shear_yield_governs

    @property
    def alpha_v(self):
        return self.slenderness.alpha_v

    @property
    def shear_stress_uniformity(self):
        return self.geom.shear_stress_uniformity

    @classmethod
    def from_library(
        cls, library: MemberLibrary, lookup_val: str, lookup_col: str = "section"
    ) -> SteelSection:
        section_dict = get_section_from_library(
            library, lookup_val=lookup_val, lookup_col=lookup_col
        )
        return cls.from_section_dict(section_dict)

    """creates a new SteelSection from library import"""

    @classmethod
    def from_section_dict(cls, section_dict: dict):
        """builds geometry, material, and section classes from section_dict"""
        geom = SectionGeometry.from_dict(**section_dict)
        mat = SteelMaterial.from_dict(**section_dict)
        return cls(geom=geom, mat=mat, slenderness=None)


@dataclass
class SteelMember:
    section: SteelSection  # includes geom and material and slenderness attrs
    name: str = field(init=False, default="")
    section_name: str = ""  # temp
    material_name: str = ""  # temp
    l_ex: float = 0
    l_ey: float = 0
    l_eb: float = 0

    end_i_restraint: bool = True  # True if end is full or partially restraint
    end_j_restraint: bool = True  # True if end is full or partially restraint

    # AS1720 Table 3.4, Members subject to bending, axial compression or tension
    phi: float = 0.9

    # AS4100 S5.1
    M_sx: float = 0
    M_bx: float = 0
    M_sy: float = 0
    V_v: float = 0
    alpha_m: float = 1  # AS4100 Cl 5.6.1.1 Moment modification factor

    # AS4100 S6.1
    N_s: float = 0
    N_cx: float = 0
    N_cy: float = 0

    # AS4100 S7.1
    N_t: float = 0
    k_t: float = 1  # AS4100 Cl 7.3 end force distribution factor for tensile members

    # Capacities
    phiN_t: float = 0
    phiN_c: float = 0
    phiN_s: float = 0
    phiV_v: float = 0
    phiM_sx: float = 0
    phiM_sy: float = 0
    phiM_x: float = 0
    phiM_y: float = 0

    # round values to a number of significant figures
    sig_figs: int = 3

    def __post_init__(self):
        N_to_kN = 1 / 1e3
        Nmm_to_kn_m = 1 / 1e6

        self.name = self.section.section_name + " (" + self.section.material_name + ")"

        self.section_name = self.section.section_name
        self.material_name = self.section.material_name

        self.M_sx = self._M_sx() * Nmm_to_kn_m
        self.M_bx = self._M_bx() * Nmm_to_kn_m
        self.M_sy = self._M_sy() * Nmm_to_kn_m

        self.N_s = self._N_s() * N_to_kN
        self.N_cx = self._N_cx() * N_to_kN
        self.N_cy = self._N_cy() * N_to_kN

        self.V_v = self._V_v() * N_to_kN

        self.N_t = self._N_t() * N_to_kN

        self.phiN_s = self.phi * self.N_s
        self.phiN_t = self.phi * self.N_t
        self.phiV_v = self.phi * self.V_v
        self.phiM_bx = self.phi * min(self.M_bx, self.M_sx)
        # self.phiM_bx = self.phi * self.M_bx
        self.phiM_y = self.phi * self.M_sy
        self.phiM_sx = self.phi * self.M_sx
        self.phiM_sy = self.phi * self.M_sy

        self.phiN_c = self.phi * min(self.N_s, self.N_cx, self.N_cy)

        # round to sig figs
        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if isinstance(v, (float, int)) and (not isnan(v)) and (v != 0):
                    setattr(
                        self, k, round(v, self.sig_figs - int(floor(log10(abs(v)))) - 1)
                    )

    def report(self, **kwargs) -> None:
        report(self, exclude_attribute_names=["section"], **kwargs)

    # ------------------------------------------------------------------------
    # AS4100 Section 5 Members Subject to Bending ----------------------------
    # ------------------------------------------------------------------------

    def _M_sx(self) -> float:
        """AS4100 Cl 5.2.1 Ms nominal section moment capacity"""
        return self.section.Z_ex * self.section.f_y

    def _M_sy(self) -> float:
        """AS4100 Cl 5.2.1 Ms nominal section moment capacity"""
        return self.section.Z_ey * self.section.f_y

    def _M_bx(self) -> float:
        """AS4100 Cl 5.6, member capacity of segments without full lateral restraint"""
        if self.l_eb > 0:
            if self.end_i_restraint and self.end_j_restraint:
                # AS4100 Cl 5.6.1 boths ends are fully or partially restrained
                return min(self.alpha_m * self.alpha_sx * self._M_sx(), self._M_sx())
            elif self.end_i_restraint or self.end_j_restraint:
                # AS4100 Cl 5.6.2 only one end is fully or partially restrained
                raise NotImplementedError
                # return min(self.alpha_sx * self.M_sx, self.M_sx)
            else:
                raise ValueError("both ends are unrestrained")
        else:
            return self._M_sx()

    # @property
    def alpha_s(self, M_s: float, M_oa: float) -> float:
        """AS4100 Cl 5.6.1.1(iv) slenderness reduction factor, section of constant cross-section"""
        return 0.6 * (((M_s / M_oa) ** 2 + 3) ** 0.5 - M_s / M_oa)
        # return slenderness_reduction_factor(self.section, M_s, M_oa)

    @property
    def alpha_sx(self) -> float:
        """AS4100 Cl 6.6.1.1(iv) slenderness reduction factor"""
        return self.alpha_s(self._M_sx(), self.M_oa)

    @property
    def M_oa(self) -> float:
        """AS4100 Cl 5.6.1.1(iv) M_oa = M_o or value determined from elastic buckling analysis"""
        return self.M_o

    @property
    def M_o(self) -> float:
        """AS4100 Cl 5.6.1 M_o reference buckling moment"""
        return reference_buckling_moment(self.section, self.l_eb)

    # ------------------------------------------------------------------------
    # AS4100 Section 6 Members subject to axial compression
    # ------------------------------------------------------------------------M_bx

    def _N_s(self) -> float:
        """AS4100 Cl 6.2.1 Nominal section capacity"""
        return self.section.k_f * self.section.A_n * self.section.f_y

    def _N_cx(self) -> float:
        """AS4100 Cl 6.3.3 Nominal section capacity (x axis) of a member of constant cross-section subject to flexural bending"""
        if self.l_ex > 0:
            return self.alpha_cx * self._N_s()
        else:
            return self._N_s()

    def _N_cy(self) -> float:
        """AS4100 Cl 6.3.3 Nominal section capacity (y axis) of a member of constant cross-section subject to flexural bending"""
        if self.l_ey > 0:
            return self.alpha_cy * self._N_s()
        else:
            return self._N_s()

    @staticmethod
    def alpha_c(xi: float, lam: float) -> float:
        """AS4100 Cl 6.3.3 member slenderness reduction factor, compression"""
        return xi * (1 - (1 - (90 / (xi * lam)) ** 2) ** 0.5)

    @property
    def alpha_cx(self) -> float:
        """AS4100 Cl 6.3.3 member slenderness reduction factor, compression x-axis"""
        return self.alpha_c(self.xi_x, self.lam_x)

    @property
    def alpha_cy(self) -> float:
        """AS4100 Cl 6.3.3 member slenderness reduction factor, compression y-axis"""
        return self.alpha_c(self.xi_y, self.lam_y)

    @staticmethod
    def xi(lam: float, eta: float) -> float:
        """AS4100 Cl 6.3.3 calculation parameter"""
        # NOTE (2*(lam/90)**2) is equal to zero if lam = 0
        # lam = 0 if l_ex or l_ey = 0
        # length != 0 checked in _N_cx and _N_cy
        return ((lam / 90) ** 2 + 1 + eta) / (2 * (lam / 90) ** 2)

    @property
    def xi_x(self) -> float:
        """AS4100 Cl 6.3.3 calculation parameter, x-axis"""
        eta_x = self.eta(self.lam_x)
        return self.xi(self.lam_x, eta_x)

    @property
    def xi_y(self):
        """AS4100 Cl 6.3.3 calculation parameter, y-axis"""
        eta_y = self.eta(self.lam_y)
        return self.xi(self.lam_y, eta_y)

    @staticmethod
    def eta(lam: float) -> float:
        """AS4100 Cl 6.3.3 calculation parameter"""
        return max(0.00326 * (lam - 13.5), 0)

    @property
    def lam_x(self) -> float:
        """AS4100 Cl 6.3.3 slenderness reduction parameter, x-axis"""
        alpha_ax = self.alpha_a(self.lam_nx)
        return self.lam_nx + alpha_ax * self.section.alpha_b

    @property
    def lam_y(self) -> float:
        """AS4100 Cl 6.3.3 slenderness reduction parameter, y-axis"""
        alpha_ay = self.alpha_a(self.lam_ny)
        return self.lam_ny + alpha_ay * self.section.alpha_b

    @property
    def lam_nx(self) -> float:
        """AS4100 Cl 6.3.3 modified member slenderness, x-axis"""
        l = (self.l_ex / self.section.r_x) * (
            self.section.k_f * self.section.f_y / 250
        ) ** 0.5
        return l

    @property
    def lam_ny(self) -> float:
        """AS4100 Cl 6.3.3 modified member slenderness, y-axis"""
        return (self.l_ey / self.section.r_y) * (
            self.section.k_f * self.section.f_y / 250
        ) ** 0.5

    @staticmethod
    def alpha_a(lam_n: float) -> float:
        """AS4100 Cl 6.3.3 calculation parameter"""
        return 2100 * (lam_n - 13.5) / (lam_n**2 - 15.3 * lam_n + 2050)

    # ------------------------------------------------------------------------
    # AS4100 Section 7 Members subject to axial tension-----------------------
    # ------------------------------------------------------------------------

    def _N_t(self) -> float:
        """AS4100 Cl 7.2 Nominal section capacity, axial tension"""
        N_t = min(
            self.section.A_g * self.section.f_y,
            0.85 * self.k_t * self.section.A_n * self.section.f_u,
        )
        return N_t

    # ------------------------------------------------------------------------
    # AS4100 Section combined actions ---------
    # ------------------------------------------------------------------------

    def M_ix(self, N_star, l_ex):
        if N_star <= 0:
            return self.M_sx() * (1 + N_star / (self.phi["N_c"] * self.N_cx(l_ex)))
        else:
            return None

    def M_iy(self, N_star, l_ey):
        if N_star <= 0:
            return self.M_sy() * (1 + N_star / (self.phi["N_c"] * self.N_cy(l_ey)))
        else:
            return None

    def M_rx(self, N_star):
        return self.M_sx() * (1 - abs(N_star) / (self.phi["N_s"] * self.N_t()))

    def M_ox(self, N_star, l_eb, l_ey, alpha_m):
        if N_star <= 0:
            # compression
            return self.M_bx(l_eb, alpha_m) * (
                1 + N_star / (self.phi["N_c"] * self.N_cy(l_ey))
            )
        else:
            # tension
            return min(
                self.M_bx(l_eb, alpha_m)
                * (1 + N_star / (self.phi["N_c"] * self.N_t())),
                self.M_rx(N_star),
            )

    def M_cx(self, N_star, l_ex, l_ey, l_eb, alpha_m):
        try:
            return min(self.M_ix(N_star, l_ey), self.M_ox(N_star, l_eb, l_ey, alpha_m))
        except:
            return self.M_ox(N_star, l_eb, l_ey, alpha_m)

    # shear calculations -----------------------------------------------------

    # shear calcs depend on the section shape so it can't be generic
    # def V_v(self): # pragma: no cover
    #     raise NotImplementedError

    def _V_v(self):
        """AS4100 Cl 5.11.1 shear capacity of web"""
        if self.section.shear_stress_uniformity == 1:
            # approximately uniform shear stress distribution
            return self.V_u
        else:
            # non-uniform shear stress distribution
            return self.V_nu

    @property
    def V_u(self):
        """Cl 5.11.2 approximately uniform shear stress distribution"""
        if self.section.web_shear_yield_governs:
            return self.V_w
        else:
            return self.V_b

    @property
    def V_nu(self):
        """Cl 5.11.3 non-uniform shear stress distribution"""
        v_u = self.V_u
        v_nu = 2 * v_u / (0.9 + self.section.shear_stress_uniformity)
        return min(v_u, v_nu)

    @property
    def V_w(self) -> float:
        """AS4100 Cl 5.11.4 shear yield capacity"""
        if self.section.sec_type == "CHS":
            A_e = self.section.A_g
            return 0.36 * self.section.f_y * A_e
        else:
            # TODO: improve this - embed in SteelSection?
            if "f_yw" in self.section.mat.__dict__:
                return 0.6 * self.section.f_yw * self.section.A_w
            else:
                return 0.6 * self.section.f_y * self.section.A_w

    @property
    def V_b(self) -> float:
        """AS4100 Cl 5.11.5 shear buckling capacity"""
        # NOTE: only implemented for unstiffened web
        return self.section.alpha_v * self.V_w

    @classmethod
    def column_order(cls):
        n = [
            "name",  # 'l_ex', 'l_ey',
            "phiN_s",
            "phiN_t",
            "phiM_sx",
            "phiM_sy",
            "phiV_v",
            "section_name",
            "material_name",
        ]
        return n

    # @classmethod
    # #def from_dict(cls, attr_dict):
    # def from_dict(cls, **kwargs):
    #     o = cls()
    #     for k, v in kwargs.items():
    #         if hasattr(o, k):
    #             setattr(o, k, v)
    #     return o

    # @classmethod
    # def from_dict(cls, **kwargs):
    #     o = cls()
    #     for k, v in kwargs.items():
    #         # note - @property items are in hasattr but not in __annotations__)
    #         if hasattr(o, k) and (k in cls.__annotations__):
    #             if k == 'section' and type(v) == dict:
    #                 # this is limited to I-section
    #                 setattr(o, k, SteelISection.from_dict(**v))
    #             else:
    #                 setattr(o, k, v)
    #     return o


def main(): ...


if __name__ == "__main__":
    main()

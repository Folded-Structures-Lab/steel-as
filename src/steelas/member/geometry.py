# -*- coding: utf-8 -*-

"""
This module provides classes and functions to manage steel sections and their geometric properties.

Classes:
    SectionGeometry: TODO.

Functions:
    import_section_library(): Returns a DataFrame containing the section library defined
    in steelas/data/

"""

from __future__ import annotations

from math import floor, log10, isnan
from dataclasses import dataclass, field
from enum import StrEnum
import numpy as np

from steelas.shape import (
    circularhollow,
    rectangularhollow,
    ishape,
    cshape,
    tshape,
    rectangleplate,
)

from steelas.data.io import report


class SectionType(StrEnum):
    CHS = "CHS"
    RHS = "RHS"
    SHS = "SHS"
    WB = "WB"
    UB = "UB"
    UC = "UC"
    PFC = "PFC"
    BT = "BT"
    CT = "CT"
    RectPlate = "RectPlate"


# list section property keys
# open_section_keys = ['d', 'b', 't_f', 't_w', 'r']
# tfb_keys = ['d', 'b', 't_f', 't_w', 'r_r', 'r_f', 'alpha']
# rhs_keys = ['d', 'b', 't', 'r_out']
# chs_keys = ['d', 't']
# plate_keys = ['b', 'd']


@dataclass(kw_only=True)
class SectionGeometry:
    """
    Represents the geometric properties of a structural section.

    This class encapsulates the geometric dimensions and derived properties of various structural section types,
    such as I-shapes (WB, WC, UB, UC), Channels (PFC), Hollow Sections (RHS, SHS, CHS), and Plates. It provides
    functionality to calculate sectional properties based on the specified geometry, including area, moment of
    inertia, section modulus, and radius of gyration, among others.

    Attributes:
        name (str): A descriptive name for the section.
        section (str): The specific section designation.
        sec_type (str): The type of section (e.g., CHS, RHS, UB).
        d, b, t_f, t_w, t, r_1, r_2, alpha, r_o: Geometric dimensions of the section.
        A_g (float): Gross area of the section.
        I_x, I_y (float): Second moment of area about the x-axis and y-axis, respectively.
        S_x, S_y (float): Elastic section modulus about the x-axis and y-axis, respectively.
        Z_x, Z_y (float): Plastic section modulus about the x-axis and y-axis, respectively.
        r_x, r_y (float): Radius of gyration about the x-axis and y-axis, respectively.
        I_w (float): Warping constant.
        J (float): Torsional constant.
        x_c, y_c (float): Coordinates of the centroid, default to 0.
        sig_figs (int): Number of significant figures for rounding calculations, defaults to 4.
    """

    name: str = ""
    section: str = ""
    sec_type: str = ""

    d: float = np.nan
    b: float = np.nan
    t_f: float = np.nan
    t_w: float = np.nan
    t: float = np.nan
    r_1: float = np.nan
    r_2: float = np.nan
    alpha: float = np.nan
    r_o: float = np.nan

    A_g: float = np.nan
    I_x: float = np.nan
    I_y: float = np.nan
    S_x: float = np.nan
    S_y: float = np.nan
    Z_x: float = np.nan
    Z_y: float = np.nan
    r_x: float = np.nan
    r_y: float = np.nan
    I_w: float = np.nan
    J: float = np.nan

    x_c: float = 0
    y_c: float = 0

    # round values to a number of significant figures
    sig_figs: int = field(repr=False, default=4)

    def __post_init__(self):
        if self.sec_type != "":
            self.solve_shape()

    def report(self, **kwargs):
        return report(self, **kwargs)

    def solve_shape(self):
        if self.sec_type in ["CHS"]:
            shape_fn = circularhollow
        elif self.sec_type in ["RHS", "SHS"]:
            shape_fn = rectangularhollow
        elif self.sec_type in ["WB", "WC", "UB", "UC"]:
            shape_fn = ishape
        elif self.sec_type in ["PFC"]:
            shape_fn = cshape
            self.x_c = shape_fn.x_c(self)
        elif self.sec_type in ["BT", "CT"]:
            shape_fn = tshape
            self.y_c = shape_fn.y_c(self)
        elif self.sec_type in ["RectPlate"]:
            shape_fn = rectangleplate
        else:
            raise NotImplementedError(
                f"section type: {self.sec_type} has no shape function"
            )

        self.A_g = shape_fn.A_g(self)
        self.I_x = shape_fn.I_x(self)
        self.I_y = shape_fn.I_y(self)
        self.S_x = shape_fn.S_x(self)
        self.S_y = shape_fn.S_y(self)
        self.J = shape_fn.J(self)
        self.I_w = shape_fn.I_w(self)

        self.Z_x = self._Z_x()
        self.Z_y = self._Z_y()
        self.r_x = self._r_x()
        self.r_y = self._r_y()

        # round to sig figs
        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if isinstance(v, (float, int)) and (not isnan(v)) and (v != 0):
                    setattr(
                        self, k, round(v, self.sig_figs - int(floor(log10(abs(v)))) - 1)
                    )

    def _Z_x(self) -> float:
        return self.I_x / self.y_max

    def _Z_y(self) -> float:
        return self.I_y / self.x_max

    def _r_x(self) -> float:
        return (self.I_x / self.A_g) ** 0.5

    def _r_y(self) -> float:
        return (self.I_y / self.A_g) ** 0.5

    @property
    def x_max(self):
        # might not be valid for all sections
        # TODO -> PFC
        if self.sec_type in ["CHS"]:
            return self.d / 2
        elif self.sec_type in ["PFC"]:
            x_c = cshape.x_c(self)
            return max(x_c, self.b - x_c)
        else:
            return self.b / 2

    @property
    def y_max(self):
        # might not be valid for all sections
        if self.sec_type in ["BT", "CT"]:
            y_c = tshape.y_c(self)
            return max(y_c, self.d - y_c)
        else:
            return self.d / 2

    @classmethod
    def from_dict(cls, **kwargs):
        o = cls()
        # all_ann = cls.__annotations__
        for k, v in kwargs.items():
            # note - @property items are in hasattr but not in __annotations__)
            if hasattr(o, k):  # and (k in cls.__annotations__):
                setattr(o, k, v)

        if isnan(o.A_g):
            # if section properties aren't created in cls() or by dictionary override, add them here
            o.solve_shape()
        return o

    @property
    def d_1(self):
        """clear depth between flanges for open sections, ignoring fillets or welds"""
        match self.sec_type:
            case "UB" | "UC" | "PFC" | "TFB":
                # NOTE: d_1 is not equal to d_w
                # d_w used for web shear calcluation, d_1 used for web slenderness calculation
                d = self.d - 2 * self.t_f
            case "BT" | "CT":
                d = self.d - self.t_f
            case "WB" | "WC":
                d = self.d - 2 * self.t_f
            case "SHS" | "RHS":
                d = self.d - 2 * self.t
            case "RectPlate":
                d = self.d
            case other:
                raise ValueError("unknown section type")
        # return self.d_w
        return d

    @property
    def A_w(self) -> float:
        """area of web elements"""
        match self.sec_type:
            case "UB" | "UC" | "WB" | "WC" | "PFC" | "TFB":
                a = self.d_w * self.t_w
            case "BT" | "CT":
                # NOTE: eg calcs for web shear in coped section design use d_w as = d_1
                # (web depth excluding flange)
                # A_w is scaled in FeaturedMember class by d_1 / d_1
                a = self.d_w * self.t_w
            case "SHS" | "RHS":
                a = 2 * self.d_p * self.t
            case "RectPlate":
                a = self.d * self.b
            case other:
                raise NotImplementedError(
                    f"A_w not implemented for section type {self.sec_type}"
                )
        return a

    @property
    def d_w(self):
        """clear depth between flanges for RHS, SHS sections, ignoring radii"""
        match self.sec_type:
            case "RHS" | "SHS":
                d = self.d - 2 * self.t
            case "CHS":
                d = self.d
            case "UB" | "UC" | "PFC" | "TFB" | "BT" | "CT":
                d = self.d
            case "WB" | "WC":
                d = self.d - 2 * self.t_f
            case "RectPlate":
                d = self.d
            case other:
                raise ValueError("unknown section type")
        return d

    @property
    def d_p(self):
        """clear transverse dimension of a web panel"""
        if self.sec_type in ["UB", "UC", "PFC", "TFB", "WB", "WC", "BT", "CT"]:
            return self.d_1
        else:
            return self.d_w

    @property
    def b_ff(self):
        """clear width of flange for steel sections"""
        match self.sec_type:
            case "RHS" | "SHS":
                d = self.b - 2 * self.t
            case "UB" | "UC" | "TFB" | "WB" | "WC" | "BT" | "CT":
                d = (self.b - self.t_w) / 2
            case "PFC":
                # NOTE - should this be /2?
                d = (self.b - self.t_w) / 2
            case "RectPlate":
                d = 0
            case other:
                raise ValueError("unknown section type")
        return d

    @property
    def Q_c(self) -> float:
        match self.sec_type:
            case "BT" | "CT":
                if self.y_c >= (self.t_f + self.r_1):
                    q = (
                        self.b * self.t_f * (self.y_c - 0.5 * self.t_f)
                        + 0.4292
                        * self.r_1**2
                        * (self.y_c - self.t_f - 0.223 * self.r_1)
                        + self.t_w * (self.y_c - self.t_f) ** 2 / 2
                    )
                elif self.y_c >= self.t_f:
                    q = (
                        self.b * self.t_f * (self.y_c - 0.5 * self.t_f)
                        + self.t_w * (self.y_c - self.t_f) ** 2 / 2
                    )
                    # ignore fillet
                    #
                else:
                    raise NotImplementedError(
                        "Q_c calculation for n.a. within flange of tee-section not implemented"
                    )
                # NOTE: ignore section radius
                # q = self.b * self.t_f*(self.y_c - 0.5 * self.t_f) + \
                #    self.t_w * (self.y_c - self.t_f)**2/2
            case "RectPlate":
                q = self.b * self.d**2 / 8
            case other:
                raise ValueError(
                    f"Q_c not implemented for section type {self.sec_type}"
                )
        return q

    @property
    def shear_stress_uniformity(self) -> float:
        match self.sec_type:
            case "RHS" | "SHS" | "UB" | "UC" | "TFB" | "WB" | "WC" | "CHS" | "PFC":
                return 1.0
            case "BT" | "CT":
                return self.Q_c * self.d_1 / self.I_x
            case "RectPlate":
                # return 1.5
                return self.Q_c * self.d / self.I_x

            case other:
                raise ValueError(
                    f"unknown shear stress distribution for section type {self.sec_type}"
                )

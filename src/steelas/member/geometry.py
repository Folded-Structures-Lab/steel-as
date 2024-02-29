# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 23:59:06 2022

@author: joegattas
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from math import floor, log10, isnan

from dataclasses import dataclass, field

from structuralshapes import circularhollow, rectangularhollow, ishape, cshape, tshape, rectangleplate

# TODO IMPLEMENT TFB?
# INVESTIGATE PFC ERROR - x_C?



# list section property keys
# open_section_keys = ['d', 'b', 't_f', 't_w', 'r']
# tfb_keys = ['d', 'b', 't_f', 't_w', 'r_r', 'r_f', 'alpha']
# rhs_keys = ['d', 'b', 't', 'r_out']
# chs_keys = ['d', 't']
# plate_keys = ['b', 'd']


@dataclass(kw_only=True)
class SectionGeometry():
    name: str = ''
    section: str = ''
    sec_type: str = ''

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
        if self.sec_type != '':
            self.solve_shape()


    def solve_shape(self):
        if self.sec_type in ['CHS']:
            shape_fn = circularhollow
        elif self.sec_type in ['RHS', 'SHS']:
            shape_fn = rectangularhollow
        elif self.sec_type in ['WB','WC', 'UB' , 'UC']:
            shape_fn = ishape
        elif self.sec_type in ['PFC']:
            shape_fn = cshape
            self.x_c = shape_fn.x_c(self)
        elif self.sec_type in ['BT',  'CT' ]:
            shape_fn = tshape
            self.y_c = shape_fn.y_c(self)
        elif self.sec_type in ['RectPlate']:
            shape_fn = rectangleplate
        else:
            raise NotImplementedError(f'section type: {self.sec_type} has no shape function')

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
                    setattr(self, k, round(v, self.sig_figs -
                            int(floor(log10(abs(v))))-1))

    def _Z_x(self) -> float:
        return self.I_x / self.y_max

    def _Z_y(self)-> float:
        return self.I_y / self.x_max

    def _r_x(self) -> float:
        return (self.I_x / self.A_g) ** 0.5

    def _r_y(self) -> float:
        return (self.I_y / self.A_g) ** 0.5
    
    @property
    def x_max(self):
        #might not be valid for all sections
        #TODO -> PFC
        if self.sec_type in ['CHS']:
            return self.d/2
        elif self.sec_type in ['PFC']:
            x_c = cshape.x_c(self)
            return max(x_c, self.b-x_c)
        else:
            return self.b/2


    @property
    def y_max(self):
        #might not be valid for all sections
        if self.sec_type in ['BT', 'CT']:
            y_c = tshape.y_c(self)
            return max(y_c, self.d-y_c)
        else:
            return self.d/2
        
    @classmethod
    def from_dict(cls, **kwargs):
        o = cls()
        #all_ann = cls.__annotations__
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
        '''clear depth between flanges for open sections, ignoring fillets or welds'''
        match self.sec_type:
            case 'UB' | 'UC' | 'PFC' | 'TFB':
                # NOTE: d_1 is not equal to d_w
                # d_w used for web shear calcluation, d_1 used for web slenderness calculation
                d = self.d - 2 * self.t_f
            case 'BT' | 'CT':
                d = self.d - self.t_f
            case 'WB' | 'WC':
                d = self.d - 2 * self.t_f
            case 'SHS' | 'RHS':
                d = self.d - 2 * self.t
            case 'RectPlate':
                d = self.d
            case other:
                raise ValueError('unknown section type')
        # return self.d_w
        return d

    @property
    def A_w(self) -> float:
        '''area of web elements'''
        match self.sec_type:
            case 'UB' | 'UC' | 'WB' | 'WC' | 'PFC' | 'TFB':
                a = self.d_w * self.t_w
            case 'BT' | 'CT':
                # NOTE: eg calcs for web shear in coped section design use d_w as = d_1 (web depth exlcuding flange)
                # A_w is scaled in FeaturedMember class by d_1 / d_1
                a = self.d_w * self.t_w
            case 'SHS' | 'RHS':
                a = 2 * self.d_p * self.t
            case 'RectPlate':
                a = self.d * self.b
            case other:
                raise NotImplementedError(
                    f'A_w not implemented for section type {self.sec_type}')
        return a

    @property
    def d_w(self):
        '''clear depth between flanges for RHS, SHS sections, ignoring radii'''
        match self.sec_type:
            case 'RHS' | 'SHS':
                d = self.d - 2 * self.t
            case 'CHS':
                d = self.d
            case 'UB' | 'UC' | 'PFC' | 'TFB' | 'BT' | 'CT':
                d = self.d
            case 'WB' | 'WC':
                d = self.d - 2 * self.t_f
            case 'RectPlate':
                d = self.d
            case other:
                raise ValueError('unknown section type')
        return d

    @property
    def d_p(self):
        '''clear transverse dimension of a web panel'''
        if self.sec_type in ['UB', 'UC', 'PFC', 'TFB', 'WB', 'WC', 'BT', 'CT']:
            return self.d_1
        else:
            return self.d_w

    @property
    def b_ff(self):
        '''clear width of flange for steel sections'''
        match self.sec_type:
            case 'RHS' | 'SHS':
                d = self.b - 2 * self.t
            case 'UB' | 'UC' | 'TFB' | 'WB' | 'WC' | 'BT' | 'CT':
                d = (self.b - self.t_w)/2
            case 'PFC':
                #NOTE - should this be /2?
                d = (self.b - self.t_w)/2
            case 'RectPlate':
                d = 0
            case other:
                raise ValueError('unknown section type')
        return d

    @property
    def Q_c(self) -> float:
        match self.sec_type:
            case 'BT' | 'CT':
                if self.y_c >= (self.t_f + self.r_1):
                    q = self.b * self.t_f*(self.y_c - 0.5 * self.t_f) + \
                        0.4292*self.r_1**2 * (self.y_c - self.t_f - 0.223*self.r_1) + \
                        self.t_w * (self.y_c - self.t_f)**2/2
                elif self.y_c >= self.t_f:
                    q = self.b * self.t_f*(self.y_c - 0.5 * self.t_f) + \
                        self.t_w * (self.y_c - self.t_f)**2/2
                    # ignore fillet
                    #
                else:
                    raise NotImplementedError(
                        'Q_c calculation for n.a. within flange of tee-section not implemented')
                # NOTE: ignore section radius
                # q = self.b * self.t_f*(self.y_c - 0.5 * self.t_f) + \
                #    self.t_w * (self.y_c - self.t_f)**2/2
            case 'RectPlate':
                q = self.b * self.d ** 2 / 8
            case other:
                raise ValueError(
                    f'Q_c not implemented for section type {self.sec_type}')
        return q

    @property
    def shear_stress_uniformity(self) -> float:
        match self.sec_type:
            case 'RHS' | 'SHS' | 'UB' | 'UC' | 'TFB' | 'WB' | 'WC' | 'CHS' | 'PFC':
                return 1.0
            case 'BT' | 'CT':
                return self.Q_c * self.d_1 / self.I_x
            case 'RectPlate':
                # return 1.5
                return self.Q_c * self.d / self.I_x

            case other:
                raise ValueError(
                    f'unknown shear stress distribution for section type {self.sec_type}')

def main():
    from pathlib import Path
    path = Path(__file__)
    input_data = str(path.parent.parent)+'\\input_data\\AUS_open_sections.csv'

    section_df = pd.read_csv(input_data, skiprows=[1])
    section_df = section_df.apply(pd.to_numeric, errors='ignore').fillna(0)
    section_dict = section_df.iloc[91].to_dict()

    section_dict.pop('mat_type')
    section_dict.pop('grade')
    geom = SectionGeometry(**section_dict)

    print('\nGeometry from library lookup:')
    print(geom)

    geom_dict2 = {
        'section': 'user_PFC',
        'sec_type': 'PFC',
        'd': 380,
        'b': 100,
        't_f': 17.5,
        't_w': 10,
        'r_1': 14
    }
    print('\nGeometry from user input:')
    geom2 = SectionGeometry(**geom_dict2)
    print(geom2)


if __name__ == "__main__":
    main()

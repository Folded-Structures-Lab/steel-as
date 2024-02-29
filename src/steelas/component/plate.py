# -*- coding: utf-8 -*-
"""
Structural steel `Plate' Component Class
"""

#allows user classes in type hints
from __future__ import annotations 

from math import pi, floor, log10
import numpy as np
import json
from dataclasses import dataclass, field

from steelas.member.material import calc_mat_prop

@dataclass
class Plate():
    '''A class to represent a structural plate (2D)'''
    b_i: int = 200
    t_i: int = 10
    plate: str = 'Plate GR250'

    name: str = field(init = False)
    constr: str = field(init = False)
    plate_type: str = field(init = False)
    plate_grade: str = field(init = False)
    f_ui: int = field(init = False)
    f_yi: int = field(init = False)

    #round values to a number of significant figures
    sig_figs: int = field(repr=False, default = 3)


    def __post_init__(self):
        self.name = f'{self.b_i}mm x {self.t_i}mm {self.plate}'
        self.constr = json.dumps({"b_i": self.b_i, "t_i": self.t_i, "plate": self.plate})
        self.plate_type = self.plate[:-6]
        self.plate_grade = self.plate[-5:]
                
        try:
            self.f_yi, self.f_ui = calc_mat_prop(self.plate_type, self.plate_grade, self.t_i)
        except ValueError:
            self.f_yi, self.f_ui = np.nan, np.nan
        
        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if type(v) is float:
                    setattr(self, k, round(v, self.sig_figs-int(floor(log10(abs(v))))-1) )    
    


    @property
    def phi_shear(self) -> float:
        '''capacity factor for shear, AS4100:1998 Table 3.4'''
        return 0.9

    @property
    def phi_bending(self) -> float:
        '''capacity factor for bending, AS4100:1998 Table 3.4'''
        return 0.9

    @property
    def phi_bearing(self) -> float:
        '''capacity factor for ply bearing, AS4100:1998 Table 3.4'''
        return 0.9

    @property
    def phi_block_shear(self) -> float:
        '''capacity factor for block shear, ANSI/AISC 360-16 J4.3'''
        return 0.75

    #------bolt ply in bearing-----
    # def phiV_bb(self, d_f):
    #     #AS4100 9.3.2.4
    #     return self.phi_bearing * 3.2 * d_f * self.t_i * self.f_ui

    def phiV_bb(self, n_b, d_f, t_p, f_u): #!!! also apply to member
        '''ply in bearing (local bearing failure), AS4100 9.3.2.4(1)'''
        return n_b * self.phi_bearing * 3.2 * d_f * t_p * f_u
        
    # def phiV_bt(self, a_e):
    #     #AS4100 9.3.2.4
    #     return self.phi_bearing * a_e * self.t_i * self.f_ui #a_exi or a_eyi
    
    def phiV_bt(self, n_b, a_e, t_p, f_u): #!!! also apply to member
        '''ply in bearing (tear-out failure), AS4100 9.3.2.4(2)'''
        return n_b * self.phi_bearing * a_e * t_p * f_u #a_exi or a_eyi
    
    def phiV_v(self, d_i):
        '''plate shear capacity, AS4100:1998 CL 5.11.3, 5.11.4; ASI Handbook1 CL 5.4'''
        V_v = 0.5 * self.f_yi * d_i * self.t_i/1e3 #kN
        #source: AS4100:1998 CL 5.11.1
        return round(self.phi_shear * V_v, 2)
    
    def phiM_si(self, d_i): # can inherit from member_class.py
        '''plate moment capacity, AS4100 CL 5.2.1; ASI Handbook 1 CL 5.4'''
        M_si = self.f_yi * self.t_i * d_i**2/4
        return round(self.phi_bearing * M_si, 2)

    def phiM_si_ecc(self, d_i,e):
        '''plate moment capacity with eccentricity'''
        return self.phiM_si(d_i)/e/1e3 #kN
        
    # plate in block shear
    # def A_nt(self, l_t):
    #     return l_t * self.t_i
    
    def A_nt(self, l_t): # also apply to member
        '''net area in horizontal block shear, ASI Handbook1 Fig. 50'''
        return l_t * self.t_i
    
    # def A_gv(self, l_v):
    #     #source: ASI Handbook1 Fig. 50  
    #     return l_v * self.t_i
    
    def A_gv(self, l_v): #!!! also apply to member
        '''gross area in vertical direction block shear, ASI Handbook1 Fig. 50'''
        return l_v * self.t_i

    # def A_nt_singleV(self, l_t_singe, d_h): #edge only
    #     #source: ASI Handbook1 Fig. 50 
    #     return (l_t_single - 0.5 * d_h) * self.t_i


    # def A_nt_doubleV(self, l_t_double, d_h): #edge + middle area
    #     return (l_t_double - 1.5 * d_h) * self.t_i
        
    # def A_nt_N(self, l_t_N, n_p, d_h):
    #     return (l_t_N - (n_p - 1)*d_h)*self.t_i
        
    # def phiV_bs(self, l_t, l_v): 
    #     #source: ANSI/AISC 360-16 J4.3; ASI Handbook section 5.4
    #     V_bs = (self.A_nt(l_t) * self.f_ui + 0.6 * self.A_gv(l_v) * self.f_yi)/1e3 #kN
    #     return round(self.phi_block_shear * V_bs, 2)
    
    def phiV_bs(self, l_t, l_v): #!!! also apply to member
        '''plate block shear capacity, ANSI/AISC 360-16 J4.3; ASI Handbook section 5.4'''
        V_bs = (self.A_nt(l_t) * self.f_ui + 0.6 * self.A_gv(l_v) * self.f_yi)/1e3 #kN
        return round(self.phi_block_shear * V_bs, 2)
    
    
    @classmethod
    def from_dict(cls, **kwargs):
        '''construct object from attribute dict. overrides derived attribute values otherwise calculated in __post_init__ '''
        o = cls()
        for k, v in kwargs.items():
            if hasattr(o, k):
                setattr(o, k, v)
        return o  
        
    @classmethod
    def from_constr(cls, constructor_str: str) -> Plate:
        '''construct object from constructor string attribute '''
        attr_dict = json.loads(constructor_str)
        return Plate(**attr_dict)
    


def main():
    p = Plate(b_i = 130, t_i = 6, plate = 'Plate GR250')
    print(p, '\n')


if __name__ == "__main__":
    main()
                    
# -*- coding: utf-8 -*-
"""
Structural steel `Bolt' Component Class
"""

#allows user classes in type hints
from __future__ import annotations 

from math import pi, floor, log10
import json
from dataclasses import dataclass, field

@dataclass(kw_only = True)
class Bolt():  
    '''A class to represent a single structural bolt'''

    #data(input)
    d_f: float = 20 #bolt diameter
    bolt_cat: str = '8.8/S'
    threads_included: bool = True

    #data (output)
    name: str = field(init = False)
    bolt_des: str = field(init = False)
    
    #geometry
    d_h: float = field(init = False)
    a_e_min: float = field(init = False) 
    s_p_min: float = field(init = False)

    #capacity
    phiV_f: float  = field(init = False)
    phiN_tf: float  = field(init = False)

    #constructor
    constr: str = field(init= False)

    #round values to a number of significant figures
    sig_figs: int = field(repr=False, default = 3)

    def __post_init__(self):
   
        des = '(TI)' if self.threads_included else '(TX)'
        self.name = f'M{self.d_f} {self.bolt_cat} ' + des
        self.constr = json.dumps({"d_f": self.d_f, "bolt_cat": self.bolt_cat, "threads_included": self.threads_included})
        self.bolt_des = f'M{self.d_f}'
        
        self.d_h = self.d_f + (2 if self.d_f <= 24 else 3) #AS4100:1998 CL 14.3.5.2
        self.a_e_min = 1.5 * self.d_f #AS4100:1998 Table 9.6.2 machine flame cut, sawn or planed edge plates
        self.s_p_min = 2.5 * self.d_f #AS4100:1998 CL 9.6.1
        
        self.phiV_f = self.phi_shear * (self.V_fn if self.threads_included else self.V_fx)
        self.phiN_tf = self.phi_tension * self.N_tf   
    
        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if type(v) is float:
                    setattr(self, k, round(v, self.sig_figs-int(floor(log10(abs(v))))-1) )    
    
    @property
    def phi_shear(self) -> float:
        '''capacity factor for shear, AS4100 Table 3.4, AS4100 Cl 9.3.2.1'''
        return 0.8

    @property
    def phi_tension(self) -> float:
        '''capacity factor for tension, AS4100 Table 3.4, AS4100 Cl 9.3.2.2'''
        return 0.8 

    @property
    def P(self) -> float:
        '''bolt pitch, AS1275:1985 Table 3.2'''
        default_pitch = {12: 1.75, 16:2, 20:2.5, 24:3, 30:3.5, 36:4}
        if self.d_f not in default_pitch.keys():   
            raise ValueError('Unknown pitch for current bolt diameter')
        return default_pitch[self.d_f]


    @property
    def A_c(self)-> float:
        '''bolt core area, ASI Handbook1 Table 8; AS1275:1972 Cl 12a'''
        #D-1.22687 P = minor diameter of external threads (AS1275:1972 Cl 12a)
        #NOTE: should be updated to D-1.0825 as per AS1275:1985?
        return pi/4*(self.d_f-1.22687*self.P)**2

    @property
    def A_s(self)-> float:
        '''tensile stress area, ASI Handbook1 Table 8; AS1275:1985 Cl 1.7'''
        #D - 0.9382 P = mean of pitch and minor diameters
        #NOTE: included in AS1275:1985,  should be updated to 1.0825/2+.6495/2 = 0.866P?
        #see also 1275:1972 Cl A7
        return pi/4*(self.d_f-0.9382*self.P)**2

    @property
    def A_o(self) -> float:
        '''plain shank area, source: ASI Handbook 1 Table 8; AS1275:1985'''
        return pi/4*(self.d_f)**2

    @property 
    def f_uf(self) -> float:
        '''bolt tensile strength, property class 4.6 - AS1111.1:2000; property class 8.8 - AS/NZS1252:1996'''
        prop_class = self.bolt_cat[:3]
        f_uf = {'4.6': 400, '8.8': 830}
        if prop_class not in f_uf.keys():   
            raise ValueError('Unknown f_uf for current bolt category')      
        return f_uf[prop_class]
          

    @property
    def k_r(self) -> float:
        '''reduction factor for lap connection, AS4100 CL 9.3.2.1'''
        #for single bolt
        return 1.0
    
    @property
    def N_tf(self) -> float:
        '''bolt nominal capacity in tension, AS4100:1998 CL 9.3.2.2'''
        return self.A_s * self.f_uf/1e3 #kN
        
    @property
    def V_fx(self) -> float:
        '''bolt nominal capacity in shear (thread excluded), AS4100:1998 CL 9.3.2.1'''
        #A_v is the available shear area = A_o for thread excluded
        return 0.62 * self.f_uf * self.k_r * self.A_o/1e3
        
    @property
    def V_fn(self) -> float:
        '''bolt nominal capacity in shear (thread included), AS4100:1998 CL 9.3.2.1'''
        #A_v is the available shear area = A_c for thread included
        return 0.62 * self.f_uf * self.k_r * self.A_c/1e3
    
    @classmethod
    def from_dict(cls, **kwargs) -> Bolt:
        '''construct object from attribute dict. overrides derived attribute values otherwise calculated in __post_init__ '''
        o = cls()
        for k, v in kwargs.items():
            #note - @property items are in hasattr but not in __annotations__)
            if hasattr(o, k) and (k in cls.__annotations__):
                setattr(o, k, v)
        return o   

    @classmethod
    def from_constr(cls, constructor_str: str) -> Bolt:
        '''construct object from constructor string attribute '''
        attr_dict = json.loads(constructor_str)
        return Bolt(**attr_dict)
        

@dataclass(kw_only=True)
class BoltGroup2D():
    n_p: int = 7
    n_g: int = 2
    bolt: Bolt | str = field(default_factory=Bolt)
    s_p: int = 70 #pitch
    s_g: int = 70 #gauge
    #eccentric: bool = False
    #e: float = 0 
    name: str = field(init = False)
    constr: str = field(init=False)
    n_b: int = field(init = False)
    d_i_min: float = field(init = False) #minimum depth given by min. edge distance
    phiV_df: float = field(init = False)

    #round values to a number of significant figures
    sig_figs: int = field(repr=False, default = 3)


    def __post_init__(self):
        if type(self.bolt) is str:
            self.bolt = Bolt.from_constr(self.bolt)

        self.name = f'{self.n_p} x {self.n_g} ({self.s_p}p x {self.s_g}g) {self.bolt.name}'
        self.constr = json.dumps({"n_p": self.n_p, "n_g": self.n_g, "bolt": json.loads(self.bolt.constr), "s_p": self.s_p, "s_g": self.s_g})

        self.n_b = self.n_p * self.n_g
        self.d_i_min = 2 * self.a_e_min + self.d_hp #NOTE delete?
        self.phiV_df = self._phiV_df()

        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if type(v) is float:
                    setattr(self, k, round(v, self.sig_figs-int(floor(log10(abs(v))))-1) )    
    

    #---------geom constraint-----------------
    @property #duplicate
    def a_e_min(self): #a_ev or a_eh
        '''minumum bolt holes edge distance'''
        return 1.5 * self.bolt.d_f
    
    @property #duplicate
    def s_p_min(self):
        '''minimum pitch'''
        return 2.5 * self.bolt.d_f

    @property
    def d_hp(self) -> float:
        '''centre-to-centre depth between top-most and bottom-most bolt holes'''
        return (self.n_p-1) * self.s_p 

    @property
    def d_hg(self) -> float:
        '''centre-to-centre depth between inner-most and outer-most bolt holes'''
        return (self.n_g-1) * self.s_g         
    
    @property #duplicate
    def a_ex_bc(self): 
        '''horizontal plate tear-out length, bolt centre to adjacent hole edge'''
        return self.s_g - self.bolt.d_h/2 -1

    @property #duplicate
    def a_ey_bc(self): 
        '''vertical plate tear-out length, bolt centre to adjacent hole edge'''
        return self.s_p - self.bolt.d_h/2 - 1
    
    @property
    def bolt_name(self):
        '''generate unique bolt name'''
        return self.bolt.name

    @property
    def bolt_constr(self):
        '''generate constructor string'''
        return self.bolt.constr

    def a_ey(self, a_ev_e): 
        '''vertical plate tear-out length'''
        return min(a_ev_e - 1, self.a_ey_bc)  #min[vertical edge distance -1 , vertical hole edge to bolt centre]
    
    def a_ex(self, a_eh_e): 
        '''horizontal plate tear-out length'''
        return min(a_eh_e - 1, self.a_ex_bc) #min[horizontal edge distance -1, horizontal hole edge to bolt centre]
    
    
    #self.e = self.s_g1 + 0.5 * self.s_g if self.eccentric else 0
    
    #@property #duplicate
    #def a_eyb(self): #???
    #    return self.a_e3
        # if cope == 'O': return self.a_e3
        # elif cope == 'SWC': return min(self.a_e3, self.a_e4 -1)
        # elif cope == 'DWC': return min(self.a_e3, self.a_e4 -1, self.a_e5 - 1)
    
    #@property
    #def a_exb(self): #!!! a_e1=0 for non-eccentric (not applicable for end plate type)
    #    return min(self.a_e1 - 1, self.a_e2)
    

    @property #duplicate
    def x_max(self):
        return (self.n_g-1)* self.s_g /2
    
    @property #duplicate
    def y_max(self):
        return (self.n_p-1)* self.s_p /2
    
    @property #duplicate
    def r_max(self):
        return (self.x_max ** 2 + self.y_max ** 2)**0.5
    
    # def _cnrs(self): #duplicate
    #     #returns list of [x,y] coordinates for centre of each bolt
    #     cnrs = []
    #     cy = ((self.n_p-1) * self.s_p) / 2
    #     cx = ((self.n_g-1) * self.s_g) / 2
    #     for nx in range(self.n_g):
    #         for ny in range(self.n_p):
    #             cnrs.append([nx*self.s_g - cx,
    #                          ny*self.s_p - cy])
    #     return cnrs# [a for a in c]

    #----------bolt group shear geom----------
    # @property #duplicate
    # def L_j(self): #joint length
    #     return (self.n_p - 1)*self.s_p
    
    # @property #duplicate
    # def k_r(self):
    #     if self.L_j < 300: return 1
    #     elif self.L_j <= 1300: return 1.075 - self.L_j/4000
    #     elif self.L_j > 1300: return 0.75

    #----------plate block shear geom----------
    def l_vy(self, a_ev_e): #in vertical direction
        '''block shear path parallel to vertical shear force, ASI Handbook1 section 5.4 Figure 50, ASI Design Guide 4 Fig.14'''
        return (a_ev_e + self.d_hp) #a_e6(plate)/a_e4(member)
    
    def l_ty(self, a_eh_e): #in horizontal direction
        '''block shear path perpendicular to vertical shear force, ASI Handbook1 section 5.4 Figure 50'''
        # return (a_eh_e - 0.5*self.bolt.d_h ) #for 1D
        return (a_eh_e + self.s_g - 1.5*self.bolt.d_h) #for 2D
        # return (b_i - a_eh - 0.5*self.bolt.d_h) for both 1D&2D
    
    def l_vx(self, a_eh_e): #in horizontal direction
        '''block shear path parallel to horizontal tension force, ASI Handbook1 section 5.4 Figure 50'''
        return (self.s_g + a_eh_e) #a_e7(plate)/a_e1(member)
        
    @property #duplicate
    def l_tx(self): #in vertical direction
        '''block shear path perpendicular to horizontal tension force, ASI Handbook1 section 5.4 Figure 50'''
        return self.d_hp - (self.n_p - 1)*self.bolt.d_h

    def _phiV_df(self): #duplicate
        '''bolt group shear capacty, AS4100:1998 CL 9.3.2.1'''
        return round(self.n_b * self.bolt.phiV_f, 2)

    @classmethod
    def from_constr(cls, constructor_str: str):
        '''construct object from constructor string attribute '''
        attr_dict = json.loads(constructor_str)
        return BoltGroup2D(**attr_dict)

    @classmethod
    def from_dict(cls, **kwargs):
        o = cls()
        for k, v in kwargs.items():
            #note - @property items are in hasattr but not in __annotations__)
            # print(k)
            if hasattr(o, k): # and (k in cls.__annotations__):
                if k == 'bolt_constr':
                    setattr(o, 'bolt', Bolt.from_constr(v))    
                elif k in cls.__annotations__:
                    setattr(o, k, v)
        return o  


# @dataclass(kw_only=True)
# class BoltGroup2D(BoltGroup):
#     #----------section property----------
    @property
    def s_pg(self) -> float:
        return self.s_g / ((self.n_p - 1) * self.s_p)
    
    def Z_b(self, e):
        if self.n_p != 1:
            Z_1 = 2*e/self.s_g/(1 + 1/3 * ((self.n_p+1)/(self.n_p-1)) * (1/self.s_pg)**2)
            return 1 / ((1 + Z_1)**2 + (Z_1/self.s_pg)**2)**0.5 #if e=0 return 1
        elif self.n_p == 1:
            return 1/(1+2*e/self.s_g) #if e=0 return 1
    
    @property
    def I_bp(self):
        return self.n_g * self.n_p / 12 * (self.s_p ** 2 * (self.n_p ** 2 -1) + self.s_g ** 2 * (self.n_g ** 2 - 1))

    def Z_e(self,e):
        return self.s_p * (self.n_p+1) / (6 * e)
    
    def Z_eh(self, e): #double
        if self.n_p != 1: return self.I_bp/(e*(self.n_p-1)*self.s_p*self.n_p) #also equal to Z_e + 3*self.s_g**2/self.s_p/(6*e*(self.n_p-1))
        elif self.n_p == 1: return 0
    
    
    def Z_ev(self, e): #double
        if self.n_p != 1: return 1/(1 + self.n_p*e*self.s_g/self.I_bp) #if e=0 return 1
        elif self.n_p == 1: return self.s_g/(self.s_g + 2 * e) #if e=0 return 1
        
    #----------capacity----------
    def phiV_df_ecc(self, e): #duplicate
        #source: AS4100:1998 CL 9.3.2.1
        return round(self.Z_b(e) * self.n_b * self.bolt.phiV_f, 2)
    
    def phiV_bv_ecc(self, phiV_bf, phiV_ev, phiV_eh, e): #for eccentric use
        return min(self.phiV_df_ecc(e), self.Z_b(e) * phiV_bf, self.Z_ev(e) * phiV_ev, self.Z_eh(e) * phiV_eh)
    

def main():
    b = Bolt(d_f = 12, bolt_cat = '8.8/S', threads_included = False)
    print(b, '\n')

    bg_2d = BoltGroup2D(n_p = 7, n_g = 2, bolt = b, s_p = 70, s_g = 70)
    print(bg_2d, '\n')

if __name__ == "__main__":
    main()
                    
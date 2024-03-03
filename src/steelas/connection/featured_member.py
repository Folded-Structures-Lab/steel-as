"""
Featured Member Module

This module defines the FeaturedMember class, an extension of the SteelMember class from the steelas.member.member
module. It is designed to represent steel members with additional features that affect their structural properties,
such as coping. The module provides functionalities to apply these features to a base SteelMember object and
recalculate its structural capacities accordingly.

Classes:
    FeaturedMember: Extends SteelMember with additional features like coping and recalculates structural properties.
"""

from __future__ import annotations 
from dataclasses import dataclass, field
from math import isnan, floor, log10
from steelas.member.member import SteelSection, SteelMember
from copy import deepcopy

@dataclass(kw_only = True)
class FeaturedMember():
    """
    Represents a steel member with additional structural features applied, such as coping.

    This class extends a basic SteelMember object by incorporating modifications that impact its structural
    capacities. It allows for the specification of features like cope type, dimensions, and recalculates
    modified structural properties based on these features.

    Attributes: Attributes
        unfeatured_member (SteelMember): The base SteelMember object before feature application.
        features (str): Descriptive string of the applied features.
        cope_type (str): Type of coping applied ('O' for open, etc.).
        d_ct (float): Depth of top cope in mm.
        d_cb (float): Depth of bottom cope in mm, which may vary with plate depth.
        L_c (float): Length of the cope in mm.
        r_c (float): Radius of the cope in mm.
        name (str): Name or identifier for the featured member.
        section_name (str): Name of the steel section used.
        member (SteelMember): A deep copy of unfeatured_member, modified with specified features.
        phiM_ss (float): Modified moment capacity considering the features, in kN*m.
        phiV_ws (float): Modified shear capacity considering the features, in kN.
        sig_figs (int): Number of significant figures for rounding off calculations.
    """
    unfeatured_member: SteelMember = field(repr = False)
    
    features: str = ''

    cope_type: str = 'O'
    #coped parameters
    d_ct: float = 0 #NOTE d_ct using d_ct=35 for a=70 and d_ct=65 for a=100 capacity value copy from Tekla
    d_cb: float = 0 #standard bottom cope depth may vary with plate depth
    L_c: float = 0
    r_c: float = 0

    name: str = ''
    section_name: str = ''
    #sec_type: str = ''
    member: SteelMember = field(init=False)


    phiM_ss: float = 0
    phiV_ws: float = 0

    # round values to a number of significant figures
    sig_figs: int = field(repr = False, default = 3)

    def __post_init__(self):
        N_to_kN = 1/1e3
        Nmm_to_kn_m = 1/1e6

        #super().__post_init__()
        self._name_me()
        self.section_name = self.unfeatured_member.name

        #by default member as equal to unfeatured member (e.g. for no features)
        self.member = deepcopy(self.unfeatured_member)
        if self.cope_type in ['SWC', 'DWC']:
            #if coped, define new member based on coping type
            self._cope_me()


        # section bending capacity ignoring slenderness (for connection capacity evaluations)        
        M_ss = self._M_ss() * Nmm_to_kn_m
        self.phiM_ss = self.member.phi*M_ss 
        
        self.phiV_ws = self._V_ws()  #already scaled from V_v

        # round to sig figs
        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if isinstance(v, (float, int)) and (not isnan(v)) and (v != 0):
                    setattr(self, k, round(v, self.sig_figs -
                            int(floor(log10(abs(v))))-1))

    def _name_me(self):
        """udpates name and cope_type based on the listed features"""
        match self.features:
            case '' | 'O':
                self.features = 'O'
            case 'SWC' | 'DWC':
                self.cope_type = self.features
            case other: 
                raise ValueError(f'feature type {self.features} is unknown')
        self.name =  self.unfeatured_member.name + ' ' + self.features
        return self

    def _cope_me(self):
        """update coped section to new section type"""
        
        geom = self.member.section.geom
        if self.cope_type == 'SWC':
            if geom.sec_type == 'UB':
                geom.sec_type = 'BT'
            elif geom.sec_type == 'UC':
                geom.sec_type = 'BC'
            else:
                raise ValueError(f'unknown coped section type for original section type {geom.sec_type}')
            self.name = self.member.name + ' SWC'
            new_d = geom.d - self.d_ct
            #geom.solve_me?
        elif self.cope_type == 'DWC':
            if geom.sec_type in ['UB' , 'UC']:
                geom.sec_type = 'RectPlate'
            self.name = self.member.name + ' DWC'
            new_d = geom.d - self.d_ct - self.d_cb            
            geom.b = geom.t_w
        
        #self.sec_type = geom.sec_type
        mat = self.member.section.mat
        geom.d = new_d
        geom.name = self.name
        geom = geom.from_dict(**geom.__dict__)
        geom.solve_shape()
        ss = SteelSection(geom=geom, mat=mat, slenderness = None)
        self.member = SteelMember(ss)

    def _M_ss(self) -> float:
        """section bending capacity ignoring slenderness (for coped section capacity evaluation)"""
        return self.member.section.slenderness._Z_excompact * self.member.section.f_y

    def _V_ws(self) -> float:
        """section shear capacity - assumes web depth excluding flange"""
        return self.member.phiV_v * self.member.section.geom.d_1 / self.member.section.geom.d_w #incorrect d_1? if d=new_d, should not deduct t_f; d_w/d_1; phiV_v incorrect

    
    def phiV_wp(self,d_i): 
        """beam web in shear at end plate"""
        V_wp = self.member.phiV_v * d_i / self.member.section.geom.d_w #incorrect phiV_v
        V_wp = self.unfeatured_member.phiV_v * d_i / self.unfeatured_member.section.geom.d_w
        return V_wp

    @property
    def d(self): return self.member.section.geom.d

    @property
    def d_1(self): return self.member.section.geom.d_1

    # def d_ct_align(self,a, a_ev_e):#NOTE if re-calc using d_ct_align need make phiV_ws & phiM_ss as functions
    #     return a - a_ev_e

    # def d_cb_align(self, d_i): #NOTE DWC bot cope edge should be in aline with plate for FEP case (need decide plate depth first)
    #     """recalculate bottom cope depth for end plate"""
    #     return self.d - self.d_ct - d_i

    # def d_is(self, d_i) -> float:
    #     """end depth of the steel section, accounting for coping (SWC or DWC)"""
    #     if self.cope_type == 'O': return self.d
    #     elif self.cope_type == 'SWC': return self.d - self.d_ct
    #     elif self.cope_type == 'DWC': return self.d - self.d_ct - self.d_cb_align(d_i) #NOTE if align not required, use d_ct
    #     else: return ValueError('unknown cope_type')

    # def d_w(self, d_i) -> float:
    #     """depth of section web"""
    #     if self.cope_type == 'O': return self.d - 2*self.t_f
    #     elif self.cope_type == 'SWC': return self.d - self.d_ct - self.t_f
    #     elif self.cope_type == 'DWC': return self.d - self.d_ct - self.d_cb_align(d_i)
    #     else: return ValueError('unknown cope_type')

    """section capacity for DWC section moment capacity calculation"""
    # def K(self,d_i):
    #     xp = [0.25,0.3,0.4,0.5,0.6,0.75,1,1.5,2,3,4]
    #     xs = [16,13,10,6,4.5,2.5,1.3,0.8,0.6,0.5,0.425]
    #     if 2*self.L_c/self.d_w(d_i) > 4:
    #         K = 0.425
    #     else:
    #         K = np.interp(2*self.L_c/self.d_w(d_i),xp,xs)
    #     return K

    # def lam(self,d_i):
    #     return self.f_yw**0.5/438*1/self.K(d_i)*self.d_w(d_i)/(2*self.t_w)

    # def f_e(self,d_i):
    #     if self.lam(d_i) <= 0.7: f_e = 1
    #     elif 0.7 < self.lam(d_i) <= 1.41: f_e = 1.34 - 0.468*self.lam(d_i)
    #     else: f_e = 1.03/self.lam(d_i)**2
    #     return f_e
    
    # def f_d(self):
    #     return 3.5 - 7.5*(self.d_ct/self.d)
    
    # def f_cr(self,d_i):
    #     if self.d_ct <= 0.2*self.d and self.d_cb_align(d_i) <= 0.2*self.d and self.L_c <= 2*self.d:
    #         return 0.62*math.pi*2e5*self.t_w**2*self.f_d()/(self.L_c*self.d_w(d_i))
    #     else: #self.d_ct > 0.2*self.d and self.d_cb_DWC(d_i) > 0.2*self.d
    #         return self.f_yw * self.f_e(d_i)

    # def Z_x(self,d_i):
    #     return self.t_w*self.d_w(d_i)**2/6

    # def phiM_sd(self,d_i): 
    #     """for DWC only no provision for local buckling"""
    #     # return self.phi * self.f_cr(d_i) * self.Z_x(d_i)/1e6
    #     return 0.225* self.f_yw * self.t_w * self.d_w(d_i)**2/1e6 #NOTE assume buckling not assess

     
    # @property
    # def d_c_max(self):
    #      if self.cope_type == 'SWC': return 0.5*self.d
    #      elif self.cope_type == 'DWC': return 0.2*self.d

    # @property
    # def L_c_max(self):
    #     if self.d/self.t_w <= 900/(self.f_yw**0.5): return self.d
    #     else: return 730*10**6*self.d/(self.f_yw**1.5*(self.d/self.t_w)**3)
        
    def e_v(self,gap):
        """total gap between supporting and coped supported member"""
        return self.L_c + gap
    
    def phiV_cm(self,gap):
        #if self.cope_type == 'SWC':
        phiV_cm = self.phiM_ss/self.e_v(gap)*1000 #kN
       # elif self.cope_type == 'DWC':
            # Note - phiM_sd SHOULD be calculated in the featured member object as phiM_ss,
            # but haven't checked this yet
            # phiV_cm = self.phiM_sd(d_i)/self.e_v(gap)*1000 #kN
           # phiV_cm = self.phiM_ss/self.e_v(gap)*1000 #kN
        return phiV_cm
    
    def A_nt(self, l_t): # also apply to member
        """net area in horizontal block shear, ASI Handbook1 Fig. 50"""
        return l_t * self.member.section.geom.t_w
    
    def A_gv(self, l_v): #!!! also apply to member
        """gross area in vertical direction block shear, ASI Handbook1 Fig. 50"""
        return l_v * self.member.section.geom.t_w

    def phiV_bs(self, l_t, l_v): #!!! also apply to member
        """holed web block shear capacity, ANSI/AISC 360-16 J4.3; ASI Handbook section 5.4"""
        V_bs = (0.5*self.A_nt(l_t) * self.member.section.f_u + 0.6 * self.A_gv(l_v) * self.member.section.f_yw)/1e3 #kN
        return round(0.75 * V_bs, 2)
    


def main():
    section_dict = {'name': '610UB125 (GR300)', 'section': '610UB125', 'sec_type': 'UB', 'mat_type': 'HotRolledSection', 'grade': 'GR300', 'd': 611.6, 'b': 229, 't_f': 19.6, 't_w': 11.9, 'r_1': 14.0}
    ss = SteelSection.from_section_dict(section_dict)
    sm = SteelMember(section=ss)

    featured_member_dict = {
        'unfeatured_member': sm, 
        'features': 'SWC', 
        'd_ct': 65, 
        'L_c': 120, 
        'r_c': 10
        }
    
    # featured_member_dict = {
    #     'unfeatured_member': sm, 
    #     'features': 'DWC', 
    #     'd_ct': 50, 
    #     'd_cb': 55, 
    #     'L_c': 120, 
    #     'r_c': 10
    #     }    

    featured_member = FeaturedMember(**featured_member_dict)
    print(featured_member)
        
if __name__ == "__main__":
    main()
                    
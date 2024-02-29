# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 11:44:17 2022

@author: s4488545
"""
import numpy as np
from dataclasses import dataclass, field
from math import isnan, log10, floor, isinf
from typing import Callable

from steelas.component.bolt import BoltGroup2D
from steelas.component.weld import Weld
from steelas.component.plate import Plate
from steelas.connection.featured_member import FeaturedMember


@dataclass
class WSPConnection():
    #Va - weld to web in shear (supporting member to weld)
    #Vb - bolts shear + plate bearing + member bearing (supported member to bolts to plate)
    #Vc - plate shear (plate)
    #Vd - plate bending (plate)
    #Ve - plate block shear (plate)
    #Vf - supported member shear (supported member)
    #Vg - coped memebr block shear (supported member)
    #Vh - coped member bending (supported member)
    
    featured_member: FeaturedMember
    bolt_group: BoltGroup2D
    plate: Plate  # = Plate(180, 10, 'Plate GR250')
    weld: Weld  # = Weld(8, 'CFW', 'SP', 'E48XX')
    conn_type: str = 'WSP'

    a: int = 100
    a_ev_e: float = 35 #a_e6, vertical edge distance, bolt holt centre to edge (plate)
    a_eh_e1: float = 35 #a_e1, horizontal edge distance, bolt hole centre to edge (member)
    s_g1: float = 55 # horizontal edge distance, bolt hole centre to plate welded edge (plate)

    #TODO: ecc, derived property
    detailing_OK: bool = True
    d_i: float = field(init = False)
    e: float = field(init = False)
    a_eh_e: float = field(init = False)
    a_e4: float = field(init = False) # vertical edge distance, bolt hole centre to coped member top edge (member)
    a_e5: float = field(init = False) # vertical edge distance, bolt hole centre to coped member bottom edge (member)

    V_a: float = field(init = False)
    V_b: float = field(init = False)
    V_c: float = field(init = False)
    V_d: float = field(init = False)
    V_e: float = field(init = False)
    V_f: float = field(init = False)
    V_g: float = field(init = False)
    V_h: float = field(init = False)
    V_des_ASI: float = field(init = False)
    V_des_all: float = field(init = False)

    # round values to a number of significant figures
    sig_figs: int = 4

    def __post_init__(self):
        self.d_i = self.bolt_group.d_hp + 2 * self.a_ev_e
        self.e = self.s_g1 + 0.5 * self.bolt_group.s_g
        self.a_eh_e = self.plate.b_i - self.s_g1 - self.bolt_group.s_g #a_e7, horizontal edge distance, bolt hole to the unwelded edge (plate)
        self.gap = self.s_g1 - self.a_eh_e1

        if self.featured_member.cope_type in ['SWC', 'DWC']:
            self.a_e4 = self.a - self.featured_member.d_ct
        if self.featured_member.cope_type in ['DWC']:
            self.a_e5 = self.d_i - self.a_e4 - self.bolt_group.d_hp
            # self.featured_member.d - self.a - self.bolt_group.d_hp # - self.featured_member.d_cb or self.d_is(self.d_i) - self.a_e4 - self.bolt_group.d_hp

        self.b_l_min = self.featured_member.member.section.geom.t_w + self.plate.t_i #NOTE: min bolt length depends on supporting member & side plate only

        #DETAILING CHECKS
        # assume coped section top edge & bot edge in align with plate
        # bot cope depth recalculated using b_cb_align function based on plate depth
        # top cope depth can be recalculated from d_ct_align function but use d_ct=35 for a=70 and d_ct=65 for a=100
        # L_c_max, d_c_max detailing check not implmented
        # if not assume align, check plate depth & supported member depth vs. supporting member depth + L_c_max, d_c_max

        if self.featured_member.cope_type in ['SWC' , 'DWC']:
            #check section top cope edge in align with plate #check that cope depth + vertical edge distance equal to bolt hole vertical location
            if self.featured_member.d_ct != (self.a - self.a_ev_e):
                self.detailing_OK = False

        if self.a_ev_e < self.bolt_group.bolt.a_e_min:
            #detailing check: vertical edge distance
            self.detailing_OK = False

        if self.a_eh_e < self.bolt_group.bolt.a_e_min:
            #detailing check: horizontal edge distance
            self.detailing_OK = False
        
        self.d_i_min = 0.5 * self.featured_member.unfeatured_member.section.geom.d #NOTE d_i_min as field?
        if self.d_i < self.d_i_min:
            #detailing check: minimum plate depth relative to section depth
            self.detailing_OK = False

        self.t_w_min = 0.75 * self.plate.t_i #NOTE t_w_min as field?
        if self.weld.t_w < self.t_w_min:
            #detailing check: minimum weld leg relative to plate thickness
            self.detailing_OK = False
                    
        # #source: Design Guide 4 upper limit to plate depth
        # if self.featured_member.cope_type == 'O': #NOTE d_i_max as field?
        # self.d_i_max = self.featured_member.d_1 # - self.a + self.a_ev_e - \
        # self.featured_member.t_f #source: Design Guide 4 top gap plus plate depth <= member depth
        # elif self.featured_member.cope_type == 'SWC':
        #     self.d_i_max = self.featured_member.d - self.featured_member.d_ct - self.featured_member.t_f
        # elif self.featured_member.cope_type == 'DWC':
        #     self.d_i_max = self.featured_member.d - self.featured_member.d_ct - self.featured_member.t_f

        #depth limit for connection to fit between flanges (or depth after cope?)
        #d_i_max_2 = self.featured_member.d_1
        #depth limit for connection for fit within depth of featured section (NOTE: flange depth considered in d_i_max_1
        d_i_max_3 = self.featured_member.d
        #depth limit for detailing parameters - connection doesn't overhang bottom
        d_i_max_1 = self.featured_member.unfeatured_member.section.geom.d - self.a + self.a_ev_e
        #depth limit - connection fits between flanges
        d_i_max_2 = self.featured_member.unfeatured_member.section.geom.d_1


        #enforce top edge at top cope location?
        # if not isnan(self.featured_member.d_ct):
        #     if (self.a - self.a_ev_e) != self.featured_member.d_ct:
        #         self.detailing_OK = False

        if (self.a - self.a_ev_e) < self.featured_member.unfeatured_member.section.geom.t_f:
            # detailing check: top offset sufficient to clear top flange
            self.detailing_OK = False

        if (self.a - self.a_ev_e+self.d_i) > (self.featured_member.unfeatured_member.section.geom.d-self.featured_member.unfeatured_member.section.geom.t_f):
            # detailing check: bottom offset sufficient to clear bottom flange
            self.detailing_OK = False

        self.d_i_max = min(d_i_max_1,d_i_max_3)  # - self.a + self.a_ev_e - \


        if self.d_i > self.d_i_max:
            #detailing check: maximum plate depth relative to section depth
            self.detailing_OK = False
        
        # self.t_i_min = self.bolt_group.t_i_min(self.plate.f_ui)
        
        #CONNECTION CAPACITIES
        #Va - weld group + bolt group
        self.V_a = self.weld.V_a_ecc(self.d_i, self.e)
        
        #Vb - bolt group + plate + featured_member
        phiV_bf = min(self.plate.phiV_bb(self.bolt_group.n_b, self.bolt_group.bolt.d_f, self.plate.t_i, self.plate.f_ui),
                      self.plate.phiV_bb(self.bolt_group.n_b, self.bolt_group.bolt.d_f, self.featured_member.member.section.geom.t_w,
                      self.featured_member.member.section.mat.f_u))
        
        if self.featured_member.cope_type == 'SWC':
            a_ey_b = self.bolt_group.a_ey(self.a_e4)
        elif self.featured_member.cope_type == 'DWC':
            a_ey_b = self.bolt_group.a_ey(min(self.a_e4,self.a_e5))

        if self.featured_member.cope_type == 'O':
            phiV_ev = self.plate.phiV_bt(self.bolt_group.n_b, self.bolt_group.a_ey(self.a_ev_e), self.plate.t_i, self.plate.f_ui) #NOTE for uncoped
        elif self.featured_member.cope_type in ['SWC', 'DWC']:
            phiV_ev = min(self.plate.phiV_bt(self.bolt_group.n_b, self.bolt_group.a_ey(self.a_ev_e), self.plate.t_i, self.plate.f_ui),
                          self.plate.phiV_bt(self.bolt_group.n_b, a_ey_b, self.featured_member.member.section.geom.t_w, self.featured_member.member.section.mat.f_u))
        
        phiV_eh = min(self.plate.phiV_bt(self.bolt_group.n_b, self.bolt_group.a_ex(self.a_eh_e), self.plate.t_i, self.plate.f_ui),
                      self.plate.phiV_bt(self.bolt_group.n_b, self.bolt_group.a_ex(self.a_eh_e1), self.featured_member.member.section.geom.t_w, 
                      self.featured_member.member.section.mat.f_u))
        
        self.V_b = self.bolt_group.phiV_bv_ecc(phiV_bf/1000, phiV_ev/1000, phiV_eh/1000, self.e)
            
        #Vc - plate in shear
        self.V_c = self.plate.phiV_v(self.d_i)
        
        #Vd - plate in bending
        self.V_d = self.plate.phiM_si_ecc(self.d_i, self.e)
        
        #Ve - plate in block shear
        l_t_V_plate = self.bolt_group.l_ty(self.a_eh_e)
        l_v_V_plate = self.bolt_group.l_vy(self.a_ev_e)
        
        self.V_e = self.plate.phiV_bs(l_t_V_plate,l_v_V_plate)
        
        #Vf - member in shear
        self.V_f = self.featured_member.phiV_ws

        #Vg - coped member in block shear
        self.V_g = self._V_g()
        
        #Vh - coped member in bending
        self.V_h = self.featured_member.phiV_cm(self.gap)
        
        self.V_des_ASI = self._V_des_ASI()

        self.V_des_all = self._V_des_all()

        # round to sig figs
        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                #NOTE - isinf(v) for V_g = inf for uncoped sections
                if isinstance(v, (float, int)) and (not isnan(v)) and (v != 0) and (not isinf(v)):
                    setattr(self, k, round(v, self.sig_figs -
                            int(floor(log10(abs(v))))-1))
   
    def _V_g(self):
        if self.featured_member.cope_type in ['SWC','DWC']:
            l_t_V_member = self.bolt_group.l_ty(self.a_eh_e1)
            l_v_V_member = self.bolt_group.l_vy(self.a_e4)
            V_g = self.featured_member.phiV_bs(l_t_V_member, l_v_V_member)
        else:
            # V_g = np.inf
            V_g = np.nan
        return V_g

    def _V_des_ASI(self):
        if self.featured_member.cope_type == 'O':
            return min(self.V_a, self.V_b, self.V_c, self.V_d, self.V_e, self.V_f)
        else:
            return min(self.V_a, self.V_b, self.V_c, self.V_d, self.V_e, self.V_f, self.V_g)
    
    def _V_des_all(self):
        # if self.featured_member.cope_type == 'O':
        #     return min(self.V_a, self.V_b, self.V_c, self.V_d, self.V_e, self.V_f)
        # else:
        return min(self.V_a, self.V_b, self.V_c, self.V_d, self.V_e, self.V_f,self.V_g, self.V_h)
    
    @property
    def govern_cap(self):
        caps = {'V_a':self.V_a, 'V_b':self.V_b, 'V_c':self.V_c, 'V_d':self.V_d,
                'V_e':self.V_e, 'V_f':self.V_f, 'V_g':self.V_g, 'V_h':self.V_h}
        for k,v in caps.items():
            if self.V_des_all == v:
                return k

    @property
    def long_name(self) -> str:
        '''returns a (long) name string by concatenating member + component names'''
        n = f'{self.member_name}, {self.bolt_group_name}, {self.plate_name}, {self.weld_name}'
        return n

    def name_constr(self) -> Callable:
        '''returns a function that constructs a '''
        def nf(x): return f'{self.conn_type} {str(x)}'
        return nf

    def short_name(self, short_id: int | str) -> str:
        '''returns a short name string, using the defined name_constr function'''
        name_function = self.name_constr()
        return name_function(short_id)

    # component name index (for verification lookup use & database aggregation query local key)

    def get_attr_name(self, attr: str) -> str:
        if hasattr(self, attr):
            a = getattr(self, attr)
            if hasattr(a, 'name'):
                return a.name
            else:
                raise AttributeError(f'{attr} has no defined name attribute')
        else:
            raise AttributeError(f'Object has no attribute: {attr}')

    @property
    def bolt_group_name(self) -> str:
        return self.get_attr_name('bolt_group')

    @property
    def plate_name(self) -> str:
        return self.get_attr_name('plate')

    @property
    def weld_name(self) -> str:
        return self.get_attr_name('weld')

    @property
    def member_name(self) -> str:
        return self.get_attr_name('featured_member')

        
def main():
    # build components. note: below useds constr str to define bolt
    bolt_group_dict = {'n_p': 2, 'n_g': 2, 's_p': 70,
                       's_g': 70, 'bolt': '{"d_f": 20, "bolt_cat": "8.8/S", "threads_included": true}'}
    weld_dict = {'t_w': 8, 'weld_type': 'CFW',
                 'weld_cat': 'SP', 'weld_class': 'E48XX'}
    plate_dict = {'b_i': 180, 't_i': 10, 'plate': 'Plate GR250'}
    bolt_group = BoltGroup2D(**bolt_group_dict)
    weld = Weld(**weld_dict)
    plate = Plate(**plate_dict)

    # build featured members
    from steelas.member.member import SteelSection, SteelMember

    # section_dict = {'name': '530UB92.4 (GR300)', 'section': '530UB92.4', 'sec_type': 'UB', 'mat_type': 'HotRolledSection',
    #                 'grade': 'GR300', 'd': 533, 'b': 209, 't_f': 15.6, 't_w': 10.2, 'r_1': 14}
    # section_dict = {'name': '460UB82.1 (GR300)', 'section': '460UB82.1', 'sec_type': 'UB', 'mat_type': 'HotRolledSection',
    #                 'grade': 'GR300', 'd': 460.4, 'b': 191, 't_f': 16.0, 't_w': 9.9, 'r_1': 11.4}
    # section_dict = {'name': '360UB50.7 (GR300)', 'section': '360UB50.7', 'sec_type': 'UB', 'mat_type': 'HotRolledSection',
    #                 'grade': 'GR300', 'd': 355.6, 'b': 171, 't_f': 11.5, 't_w': 7.3, 'r_1': 11.4}
    section_dict = {'name': '250UB25.7 (GR300)', 'section': '250UB25.7', 'sec_type': 'UB', 'mat_type': 'HotRolledSection',
                    'grade': 'GR300', 'd': 248, 'b': 124, 't_f': 8, 't_w': 5, 'r_1': 12}
    ss = SteelSection.from_section_dict(section_dict)
    sm = SteelMember(section=ss)
    # featured_mem_dict = {'unfeatured_member': sm, 'features': 'DWC',
    #                      'd_ct': 65, 'd_cb': 53, 'L_c': 120, 'r_c': 10}
    # featured_mem_dict = {'unfeatured_member': sm, 'features': 'SWC',
    #                      'd_ct': 65, 'd_cb': 0.0, 'L_c': 120, 'r_c': 10}
    # featured_mem_dict = {'unfeatured_member': sm, 'features': 'DWC',
    #                      'd_ct': 65, 'd_cb': 51, 'L_c': 120, 'r_c': 10}
    featured_mem_dict = {'unfeatured_member': sm, 'features': 'SWC',
                            'd_ct': 65, 'd_cb': 0.0, 'L_c': 120, 'r_c': 10}
    featured_member = FeaturedMember(**featured_mem_dict)

    # build connection
    conn1 = WSPConnection(featured_member=featured_member,
                          bolt_group=bolt_group, plate=plate, weld=weld)
    # print(conn1)

    print(f'connection (long) name:{conn1.long_name}')
    print(f'connection (short) name:{conn1.short_name(1)}')
    print(f'member:{conn1.featured_member.name}')
    print(f'bolt_group:{conn1.bolt_group.name}')
    print(f'weld:{conn1.weld.name}')
    print(f'plate:{conn1.plate.name}')

    print(f'V_a:{conn1.V_a}')
    print(f'V_b:{conn1.V_b}')
    print(f'V_c:{conn1.V_c}')
    print(f'V_d:{conn1.V_d}')
    print(f'V_e:{conn1.V_e}')
    print(f'V_f:{conn1.V_f}')
    print(f'V_g:{conn1.V_g}')
    print(f'V_h:{conn1.V_h}')
    print(f'V_des_ASI:{conn1.V_des_ASI}')
    print(f'V_des_all:{conn1.V_des_all}')


if __name__ == "__main__":
    main()
                
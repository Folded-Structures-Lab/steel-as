# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from math import isnan, log10, floor
from typing import Callable

from steelas.component.bolt import BoltGroup2D
from steelas.component.weld import Weld
from steelas.component.plate import Plate
from steelas.connection.featured_member import FeaturedMember

@dataclass
class Connection():
    '''parent class for simple steel connections. contains '''

@dataclass
class FEPConnection():
    # Va - weld to web in shear (supported member to weld)
    # Vb - bolts shear + plate bearing (plate to bolt group)
    # Vc - plate in shear (plate)
    # Vd - plate block shear/tear-out (plate with bolt hole)
    # Ve - supported member web shear (supported member)
    # Vf - supported member shear (supported member)
    # Vg - coped member bending check (ecc. connection load)

    featured_member: FeaturedMember
    # = BoltGroup_2D(7, 2, Bolt(d_f = 20, bolt_cat = '8.8/S', threads_included = True), 70, 140, 35)
    bolt_group: BoltGroup2D
    plate: Plate  # = Plate(200, 10, 'Plate GR250')
    weld: Weld  # = Weld(6, 'CFW', 'SP', 'E48XX')
    conn_type: str = 'FEP'

    a: float = 100  # vertical offset to top bolt, centre
    a_ev_e: float = 35  # a_e1, vertical edge distance, bolt hole centre to edge
    # gap: float = 20  #NOTE:derived attr space between supported member edge and supporting member
    # d_i: float = 0 #TODO

    detailing_OK: bool = True
    d_i: float = field(init=False)
    a_eh_e: float = field(init=False)
    #t_i_min: int = field(init=False)
    V_a: float = field(init=False)
    V_b: float = field(init=False)
    V_c: float = field(init=False)
    V_d: float = field(init=False)
    V_e: float = field(init=False)
    V_f: float = field(init=False)
    V_g: float = field(init=False)
    V_des_ASI: float = field(init=False)
    V_des_all: float = field(init=False)

    # round values to a number of significant figures
    sig_figs: int = 4

    def __post_init__(self):
        self.d_i = self.bolt_group.d_hp + 2 * self.a_ev_e
        # a_e3 horizontal edge distance, bolt hole centre to edge
        self.a_eh_e = (self.plate.b_i - self.bolt_group.d_hg)/2
        self.gap = self.plate.t_i
        self.b_l_min = self.featured_member.member.section.geom.t_w + self.plate.t_i #NOTE: assume min FEP supporting member t_w = supported member's

        # DETAILING CHECKS
        # assume coped section top edge & bot edge in align with plate
        # bot cope depth recalculated using b_cb_align function based on plate depth
        # top cope depth can be recalculated from d_ct_align function but use d_ct=35 for a=70 and d_ct=65 for a=100
        # L_c_max, d_c_max detailing check not implmented
        # if not assume align, check plate depth & supported member depth vs. supporting member depth + L_c_max, d_c_max

        if self.featured_member.cope_type in ['SWC', 'DWC']:
            # check section top cope edge in align with plate #check that cope depth + vertical edge distance equal to bolt hole vertical location
            if self.featured_member.d_ct != (self.a - self.a_ev_e):
                self.detailing_OK = False

        # # a_e1 max should be less than min distance of top/bot of beam to top/bot hole
        # a_ev_e_max_1 = self.a - self.featured_member.unfeatured_member.section.geom.t_f
        # a_ev_e_max_2 = self.featured_member.unfeatured_member.section.geom.d - self.featured_member.unfeatured_member.section.geom.t_f - self.a - self.bolt_group.d_hp

        # self.a_ev_e_max = min(a_ev_e_max_1, a_ev_e_max_2)
        # if self.a_ev_e > self.a_ev_e_max:
        #     # detailing check: vertical edge distance
        #     self.detailing_OK = False

        if self.a_ev_e < self.bolt_group.bolt.a_e_min:
            # detailing check: vertical edge distance
            self.detailing_OK = False

        if self.a_eh_e < self.bolt_group.bolt.a_e_min:
            # detailing check: horizontal edge distance
            self.detailing_OK = False

        self.d_i_min = 0.5 * self.featured_member.unfeatured_member.section.geom.d # NOTE d_i_min as field?
        if self.d_i < self.d_i_min:
            # detailing check: minimum plate depth relative to section depth
            self.detailing_OK = False

        # #source: Design Guide 4 upper limit to plate depth
        # if self.featured_member.cope_type == 'O':

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
        #  self.member.t_f  # NOTE assumption wrong?
        # elif self.member.cope_type == 'SWC':
        #     self.d_i_max = self.member.d - self.member.d_ct - self.member.t_f
        # elif self.member.cope_type == 'DWC':
        #     # NOTE if cope edge in align with plate, need decide max plate depth first
        #     self.d_i_max = self.member.d - self.member.d_ct - self.member.t_f
        #     # self.d_i_max = self.member.d - self.member.d_ct - self.member.d_cb #NOTE for not require align case, need decide cope depth first

        if self.featured_member.name == '200UB18.2 (GR300) SWC':
            ...
            if self.bolt_group.n_p == 3:
                ...
        if self.d_i > self.d_i_max:
            # detailing check: maximum plate depth relative to section depth
            self.detailing_OK = False

        # NOT IMPLEMENTED
        # if self.member.cope_type != 'O':
        #     if self.member.L_c > self.member.L_c_max:
        #         self.detailing_OK = False

        # if self.member.cope_type == 'SWC':
        #     if self.member.d_ct > self.member.d_c_max:
        #         self.detailing_OK = False
        # if self.member.cope_type == 'DWC':
        #     if self.member.d_ct or self.member.d_cb_DWC(self.d_i) > self.member.d_c_max:
        #         self.detailing_OK = False

        # self.a_e_max = min(12*min(self.plate.t_i, self.sup_member.t_w), 150) #source: AS4100:1998 CL 9.6.4
        # self.s_p_max = min(15*min(self.plate.t_i, self.sup_member.t_w), 200) #souce: AS4100:1998 CL 9.6.3

        # CONNECTION CAPACITIES
        # Va - weld + plate depth
        self.V_a = self.weld.V_a(self.d_i)

        # Vb - bolts shear + plate bearing
        phiV_bb = self.plate.phiV_bb(
            self.bolt_group.n_b, self.bolt_group.bolt.d_f, self.plate.t_i, self.plate.f_ui)
        phiV_bt = self.plate.phiV_bt(self.bolt_group.n_b, self.bolt_group.a_ey(
            self.a_ev_e), self.plate.t_i, self.plate.f_ui)

        self.V_b = min(self.bolt_group.phiV_df, phiV_bb, phiV_bt)

        # Vc - plate shear
        self.V_c = 2 * self.plate.phiV_v(self.d_i)

        # Vd - plate block shear (tear-out)
        self.V_d = 2 * self.plate.phiV_bs(self.bolt_group.l_ty(self.a_eh_e), self.bolt_group.l_vy(self.a_ev_e))

        # Ve - beam web shear at end plate
        self.V_e = self.featured_member.phiV_wp(self.d_i)

        # Vf - beam shear
        self.V_f = self.featured_member.phiV_ws

        # Vg - coped member bending check (ecc. connection load)
        #self.V_g = self.featured_member.phiV_cm(self.gap, self.d_i)
        self.V_g = self.featured_member.phiV_cm(self.gap)

        self.V_des_ASI = self._V_des_ASI()

        self.V_des_all = self._V_des_all()

        # round to sig figs
        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if isinstance(v, (float, int)) and (not isnan(v)) and (v != 0):
                    setattr(self, k, round(v, self.sig_figs -
                            int(floor(log10(abs(v))))-1))

    def _V_des_ASI(self):
        return min(self.V_a, self.V_b, self.V_c, self.V_d, self.V_e, self.V_f)

    def _V_des_all(self):
        # if self.member.cope_type == 'O':
        #    return min(self.V_a, self.V_b, self.V_c, self.V_d, self.V_e, self.V_f)
        # else:
        return min(self.V_a, self.V_b, self.V_c, self.V_d, self.V_e, self.V_f, self.V_g)

    @property
    def govern_cap(self):
        caps = {'V_a': self.V_a, 'V_b': self.V_b, 'V_c': self.V_c,
                'V_d': self.V_d, 'V_e': self.V_e, 'V_f': self.V_f, 'V_g': self.V_g}
        for k, v in caps.items():
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
    bolt_group_dict = {'n_p': 4, 'n_g': 2, 's_p': 70,
                       's_g': 90, 'bolt': '{"d_f": 20, "bolt_cat": "8.8/S", "threads_included": true}'}
    weld_dict = {'t_w': 6, 'weld_type': 'CFW',
                 'weld_cat': 'SP', 'weld_class': 'E48XX'}
    plate_dict = {'b_i': 150, 't_i': 10, 'plate': 'Plate GR250'}
    bolt_group = BoltGroup2D(**bolt_group_dict)
    weld = Weld(**weld_dict)
    plate = Plate(**plate_dict)

    # build featured members
    from steelas.member.member import SteelSection, SteelMember

    section_dict = {'name': '460UB82.1 (GR300)', 'section': '460UB82.1', 'sec_type': 'UB', 'mat_type': 'HotRolledSection',
                    'grade': 'GR300', 'd': 460.4, 'b': 191, 't_f': 16.0, 't_w': 9.9, 'r_1': 11.4}
    ss = SteelSection.from_section_dict(section_dict)
    sm = SteelMember(section=ss)
    featured_mem_dict = {'unfeatured_member': sm, 'features': 'SWC',
                         'd_ct': 65, 'd_cb': 0.0, 'L_c': 120, 'r_c': 10}
    featured_member = FeaturedMember(**featured_mem_dict)

    # build connection
    conn1 = FEPConnection(featured_member=featured_member,
                          bolt_group=bolt_group, plate=plate, weld=weld)
    # print(conn1)
    section_dict = {'name': '360UB50.7 (GR300)', 'section': '360UB50.7', 'sec_type': 'UB', 'mat_type': 'HotRolledSection',
                    'grade': 'GR300', 'd': 355.6, 'b': 171, 't_f': 11.5, 't_w': 7.3, 'r_1': 11.4}
    ss = SteelSection.from_section_dict(section_dict)
    sm = SteelMember(section=ss)
    featured_mem_dict = {'unfeatured_member': sm, 'features': 'O',
                            'd_ct': 0, 'd_cb': 0.0, 'L_c': 0, 'r_c': 0}
    featured_member = FeaturedMember(**featured_mem_dict)
    conn2 = FEPConnection(featured_member=featured_member,
                            bolt_group=bolt_group, plate=plate, weld=weld)


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
    print(f'V_des_ASI:{conn1.V_des_ASI}')
    print(f'V_des_all:{conn1.V_des_all}')


if __name__ == "__main__":
    main()

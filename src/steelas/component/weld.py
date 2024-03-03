"""
Structural Steel `Weld` Component Class.

This module defines the Weld class for representing a structural steel weld, including its dimensions,
geometry, material properties, and various capacity calculations based on Australian standards and ASI design handbooks.
"""

#allows user classes in type hints
from __future__ import annotations 

from math import floor, log10
import json
from dataclasses import dataclass, field

@dataclass(kw_only=False)
class Weld():
    """
    Represents a structural steel weld, encapsulating its dimensions, type, category, class, and
    providing methods for capacity calculations.

    Attributes: Attributes
        t_w (int): Leg size of the fillet weld in mm.
        weld_type (str): Type of weld, e.g., 'CFW' for continuous fillet weld.
        weld_cat (str): Category of the weld, e.g., 'SP' for specific purpose.
        weld_class (str): Class of the weld electrode, e.g., 'E48XX'.

    Attributes: Derived Attributes
        phiv_w (float): Design capacity of the weld per unit length in kN/mm, calculated post-initialization.
        name (str): Descriptive name of the weld, combining its dimensions, type, category, and class.
        constr (str): Constructor string in JSON format storing the weld's initial configuration.
        sig_figs (int): Number of significant figures for rounding calculated values.

    The class includes properties to derive critical weld parameters like design throat thickness,
    nominal weld capacity, and capacity factors based on standards such as AS4100:1998.
    """
    t_w: int = 6  # weld leg
    weld_type: str = 'CFW'
    weld_cat: str = 'SP'
    weld_class: str = 'E48XX'

    # capacity
    phiv_w: float = field(init=False)

    #data (output)
    name: str = field(init=False)
    constr: str = field(init=False)
    #round values to a number of significant figures
    sig_figs: int = field(repr=False, default = 3)

    def __post_init__(self):
        self.name = f'{self.t_w}mm {self.weld_type} {self.weld_cat} {self.weld_class}'
        self.constr = json.dumps({"t_w": self.t_w, "weld_type": self.weld_type,
                                 "weld_cat": self.weld_cat, "weld_class": self.weld_class})

        self.phiv_w = self.phi * self.v_w

        if self.sig_figs:
            for k, v in list(self.__dict__.items()):
                if type(v) is float:
                    setattr(self, k, round(v, self.sig_figs-int(floor(log10(abs(v))))-1) )    
    

    @property
    def t_t(self):
        '''design throat thickness, AS4100:1998 CL 9.7.3.1'''
        return self.t_w / 2**0.5

    @property
    def v_w(self) -> float:
        '''nominal capacity of fillet weld per unit length, AS4100 CL 9.7.3.10'''
        v_w = 0.6 * self.f_uw * self.k_r * self.t_t/1e3  # kN/mm
        return v_w

    @property
    def phi(self) -> float:
        '''capacity factor for weld category, AS4100 Table 3.4, AS4100:1998 CL 9.7.3.10'''
        phi_dict = {'SP': 0.8, 'GP': 0.6}
        if self.weld_cat not in phi_dict.keys():
            raise ValueError('Unknown capacity factor phi for current weld category')
        return phi_dict[self.weld_cat] 

    @property
    def f_uw(self) -> float:
        '''nominal tensile strength of weld metal, ASI Handbook1 Table 22, AS4100 Table 9.7.3.10(1)'''
        f_uw_dict = {'E41XX': 410, 'W40X': 410, 'E48XX': 480, 'W50X': 480}
        if self.weld_class not in f_uw_dict.keys():
            raise ValueError('Unknown f_uw for current weld class')
        return f_uw_dict[self.weld_class]

    @property
    def k_r(self) -> float:
        '''reduction factor for a welded lap connection, AS4100:1998 Table 9.7.3.10(2)'''
        # 1.0 for most connection except long lap splices
        return 1

    # weld to web in shear
    def V_a(self, d_i) -> float:
        '''weld capacity on plate, ASI Design Guide 4 section 10.2'''
        return self.phiv_w * 2 * d_i

    def V_a_ecc(self, d_i, e) -> float:  # for weld group
        '''weld capacity on plate, ASI Design Guide 5 section 10.2'''
        return self.phiv_w * 2 * d_i / (1 + (6*e/d_i)**2)**0.5

    def get_units(self, D='-', L='mm', F='kN', P='MPa'):
        unit_dict = {'t_t': L, 't_w': L,
                     'f_uw': P,
                     'v_w': F+'/mm', 'phiv_w': F+'/mm',
                     'weld_type': D, 'weld_cat': D, 'weld_class': D, 'name': D, 'phi': D, 'k_r': D, 'constr': D
                     }
        return unit_dict

    @classmethod
    def from_dict(cls, **kwargs):
        """
        Constructs a Weld object from a dictionary of attributes, allowing for dynamic creation based
        on varying specifications.

        Args:
            **kwargs: Arbitrary keyword arguments corresponding to Weld attributes.

        Returns:
            Weld: An initialized Weld object based on the provided attributes.
        """  
        o = cls()
        for k, v in kwargs.items():
            if hasattr(o, k):
                setattr(o, k, v)
        return o

    @classmethod
    def from_constr(cls, constructor_str: str) -> Weld:
        """
        Constructs a Weld object from a constructor string that contains a JSON representation
        of the weld's configuration.

        Args:
            constructor_str (str): JSON string representation of the Weld's configuration.

        Returns:
            Weld: An initialized Weld object based on the JSON string.
        """
        attr_dict = json.loads(constructor_str)
        return Weld(**attr_dict)




def main():

    w = Weld(t_w=6, weld_type='CFW', weld_cat='SP', weld_class='E48XX')
    print(w, '\n')

if __name__ == "__main__":
    main()
                    
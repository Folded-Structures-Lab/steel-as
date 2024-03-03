import math

def A_g(params: dict) -> float:
    '''Gross area'''
    t_w = params.t
    t_f = params.t
    A_g = 2*((params.d-2*params.r_o)*t_w + (params.b-2*params.r_o)*t_f)+4*(math.pi/4*(params.r_o**2-(params.r_o-params.t)**2))
    return A_g
   
def I_x(params: dict) -> float:
    '''Moment of inertia - major axis'''
    t_w = params.t
    t_f = params.t
    I_x = 2*(1/12*(params.d-2*params.r_o)**3*t_w) +2*(1/12*(params.b-2*params.r_o)*t_f**3+(params.b-2*params.r_o)*t_f*(params.d/2-t_f/2)**2) +4*((0.05488*params.r_o**4+math.pi*params.r_o**2/4*(params.d/2+4/3/math.pi*params.r_o-params.r_o)**2)-(0.05488*(params.r_o-params.t)**4+math.pi*(params.r_o-params.t)**2/4*(params.d/2-t_w+4/3/math.pi*(params.r_o-params.t)-(params.r_o-params.t))**2))
    return I_x
    #return math.pi/64 * (params.d**4 - (params.d-2*params.t)**4)

def I_y(params: dict) -> float:
    '''Moment of inertia - minor axis'''
    t_w = params.t
    t_f = params.t
    I_y = 2*(1/12*(params.d-2*params.r_o)*t_w**3+(params.d-2*params.r_o)*t_w*(params.b/2-t_f/2)**2)+2*(1/12*(params.b-2*params.r_o)**3*t_f)+4*((0.05488*params.r_o**4+math.pi*params.r_o**2/4*(params.b/2+4/3/math.pi*params.r_o-params.r_o)**2)-(0.05488*(params.r_o-params.t)**4+math.pi*(params.r_o-params.t)**2/4*(params.b/2-t_w+4/3/math.pi*(params.r_o-params.t)-(params.r_o-params.t))**2))
    return I_y
    #return I_x(params)

def S_x(params: dict) -> float:
    '''Plastic section modulus - major axis'''
    t_w = params.t
    t_f = params.t
    S_x = 2*(((params.d-2*params.r_o)/2)**2 * t_w + t_f*(params.b-2*params.r_o)*(params.d-t_f)/2) +4*(math.pi*params.r_o**2/4*(params.d/2+4/3/math.pi*params.r_o-params.r_o))-4*(math.pi*(params.r_o-params.t)**2/4*(params.d/2-t_w+4/3/math.pi*(params.r_o-params.t)-(params.r_o-params.t)))
    return S_x

def S_y(params: dict) -> float:
    '''Plastic section modulus - minor axis'''
    t_w = params.t
    t_f = params.t
    S_y = 2*(t_w*(params.d-2*params.r_o)*(params.b-t_w)/2 + t_f*(params.b/2-params.r_o)**2)+4*(math.pi*params.r_o**2/4*(params.b/2+4/3/math.pi*params.r_o-params.r_o))-4*(math.pi*(params.r_o-params.t)**2/4*(params.b/2-t_w+4/3/math.pi*(params.r_o-params.t)-(params.r_o-params.t)))
    return S_y

def I_w(params: dict) -> float:
    '''Warping constant'''
    return 0

def J(params: dict) -> float:
    '''Torsion constant'''
    r = params.r_o - params.t/2 #r is mean corner radius
    p = 2 * ((params.d-params.t)+(params.b-params.t))-2*r*(4-math.pi)
    A_p = (params.d-params.t)*(params.b-params.t)-r**2*(4-math.pi)
    J = 4 * params.t * A_p**2/p + p * params.t**3/3
    return J   


def main():
    params_dict={
        'name': '50x25x2RHS (C350)',
        'sec_type': 'RHS',
        'd': 50,
        'b': 25,
        't': 4,
        'r_o': 4
    }

    from steelas.member.geometry import SectionGeometry    
    sg = SectionGeometry(**params_dict)
    print(sg)

    print(sg.A_g)
    print(A_g(sg))
    
    print(sg.I_x)
    print(I_x(sg))

    print(sg.I_y)
    print(I_y(sg))
    
    print(sg.S_x)
    print(S_x(sg))

    print(sg.S_y)
    print(S_y(sg))

    print(sg.J)
    print(J(sg))
    
    print(sg.I_w)
    print(I_w(sg))

if __name__ == "__main__":
    main()
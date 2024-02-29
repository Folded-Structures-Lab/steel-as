import math

def A_g(params: dict) -> float:
    '''Gross area'''
    return math.pi*((params.d/2)**2 - ((params.d/2)-params.t)**2)   

def I_x(params: dict) -> float:
    '''Moment of inertia - major axis'''
    return math.pi/64 * (params.d**4 - (params.d-2*params.t)**4)

def I_y(params: dict) -> float:
    '''Moment of inertia - minor axis'''
    return I_x(params)

def S_x(params: dict) -> float:
    '''Plastic section modulus - major axis'''
    #return math.pi/32/params.d * (params.d**4 - (params.d-2*params.t)**4)
    return (params.d**3 - (params.d-2*params.t)**3)/6

def S_y(params: dict) -> float:
    '''Plastic section modulus - minor axis'''
    return S_x(params)

def I_w(params: dict) -> float:
    '''Warping constant'''
    return 0

def J(params: dict) -> float:
    '''Torsion constant'''
    J = math.pi * (params.d**4-(params.d-2*params.t)**4)/32
    return J    
     


def main():
    params_dict={
        'name': '60.3x4.5CHS (C250)',
        'sec_type': 'CHS',
        'd': 60.3,
        't': 4.5
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
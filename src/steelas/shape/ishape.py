import math

def A_g(params: dict) -> float:
    '''Gross area'''
    b_w=(params.d-2*params.t_f)
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    A_g = 2*params.b*params.t_f + params.t_w*b_w+ 4*(1-math.pi/4)*r_1**2
    return A_g
    #return math.pi*((params.d/2)**2 - ((params.d/2)-params.t)**2)   

def I_x(params: dict) -> float:
    '''Moment of inertia - major axis'''
    b_w=(params.d-2*params.t_f)
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    I_x =2*(params.b*params.t_f**3/12+params.b*params.t_f*((params.d-params.t_f)/2)**2)+params.t_w*b_w**3/12+ 4*(0.01825*r_1**4 + (1-math.pi/4)*r_1**2*(0.776*r_1 - r_1 +params.d/2 - params.t_f)**2)
    return I_x
    #return math.pi/64 * (params.d**4 - (params.d-2*params.t)**4)

def I_y(params: dict) -> float:
    '''Moment of inertia - minor axis'''
    b_w=(params.d-2*params.t_f)
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    I_y =b_w*params.t_w**3/12+2*(params.t_f*params.b**3/12)+4*(0.01825*r_1**4 + (1-math.pi/4)*r_1**2*(r_1-0.776*r_1 + params.t_w/2)**2)
    return I_y
    #return I_x(params)

def S_x(params: dict) -> float:
    '''Plastic section modulus - major axis'''
    b_w=(params.d-2*params.t_f)
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    S_x =2*(params.t_w*(b_w/2)**2/2 + params.t_f*params.b*(params.d-params.t_f)/2) + 4*  (1-math.pi/4)*r_1**2*(0.776*r_1 - r_1 +params.d/2 - params.t_f)
    return S_x

def S_y(params: dict) -> float:
    '''Plastic section modulus - minor axis'''
    b_w=(params.d-2*params.t_f)
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    S_y =2*(b_w*(params.t_w/2)**2/2 + 2*params.t_f*(params.b/2)**2/2)+ 4*  (1-math.pi/4)*r_1**2*(-0.776*r_1 + r_1 +params.t_w/2)
    return S_y

def I_w(params: dict) -> float:
    '''Warping constant'''
    return params.I_y*(params.d-params.t_f)**2/4

def J(params: dict) -> float:
    '''Torsion constant'''
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    #params.darwish and Johnston, 1965
    D_1 = ((params.t_f + r_1)**2 + params.t_w *
            (r_1 + params.t_w/4))/(2*r_1 + params.t_f)
    alpha_1 = -0.042 + 0.2204*params.t_w/params.t_f + 0.1355 * r_1/params.t_f \
        - 0.0865*params.t_w * r_1 / params.t_f**2 - 0.0725*params.t_w**2 / params.t_f**2
    J = (2 * params.b * params.t_f**3 + (params.d - 2 * params.t_f) * params.t_w**3)/3 + \
        2 * alpha_1 * D_1**4 - 4 * 0.105*params.t_f**4
    return J   



def main():
    params_dict={
        'name': '200UB18.2 (GR300)',
        'sec_type': 'UB',
        'd': 198,
        'b': 99,
        't_f': 7,
        't_w': 4.5, 
        'r_1': 11
    }

    params_dict2={
        'name': '1200WB423 (GR300)',
        'sec_type': 'WB',
        'd': 1192,
        'b': 500,
        't_f': 36,
        't_w': 16
    }

    from steelas.member.geometry import SectionGeometry    
    sg = SectionGeometry(**params_dict2)
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
import math

def y_c(params:dict)-> float:
    '''distance to centroid to outside of flange'''
    b_w=(params.d-params.t_f)
    y_c = (params.t_w*b_w*(b_w/2 + params.t_f) +
            params.b*params.t_f**2/2 + \
            2*(1-math.pi/4)*params.r_1**2*(params.t_f+(1-0.776*params.r_1))) \
                / A_g(params)
    return y_c


def y_pna(params:dict) -> float:
    '''plastic neutral axis distance from outside of flange'''
    if params.t_f < A_g(params)/(2*params.b):
        y= params.d-A_g(params)/(4*params.t_w)
    else:
        y=A_g(params)/(2*params.b)
    return y


def A_g(params: dict) -> float:
    '''Gross area'''
    b_w=(params.d-params.t_f)
    #r_1 = 0 if math.isnan(params.r_1) else params.r_1
    A_g = params.b*params.t_f + params.t_w*b_w+ 2*(1-math.pi/4)*params.r_1**2
    return A_g 

def I_x(params: dict) -> float:
    '''Moment of inertia - major axis'''
    b_w=(params.d-params.t_f)
    y_cur = y_c(params)
    I_x = 1/12 * (params.b*params.t_f**3 + params.t_w*b_w**3) + 2*(0.01825*params.r_1**4) + \
                   params.b*params.t_f*(y_cur- params.t_f/2)**2 + b_w*params.t_w*(y_cur-(params.t_f+b_w/2))**2 + 2*(1-math.pi/4)*params.r_1**2*(y_cur-(params.t_f+(1-0.776)*params.r_1))**2
    
    # I_x =2*(params.b*params.t_f**3/12+params.b*params.t_f*((params.d-params.t_f)/2)**2)+params.t_w*b_w**3/12+ 4*(0.01825*r_1**4 + (1-math.pi/4)*r_1**2*(0.776*r_1 - r_1 +params.d/2 - params.t_f)**2)
    return I_x
    #return math.pi/64 * (params.d**4 - (params.d-2*params.t)**4)

def I_y(params: dict) -> float:
    '''Moment of inertia - minor axis'''
    b_w=(params.d/2-params.t_f)
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    I_y =b_w*params.t_w**3/12+(params.t_f*params.b**3/12)+2*(0.01825*r_1**4 + (1-math.pi/4)*r_1**2*(r_1-0.776*r_1 + params.t_w/2)**2)
    return I_y
    #return I_x(params)

def S_x(params: dict) -> float:
    '''Plastic section modulus - major axis'''
    #y_cur = y_pna(params)
    if params.t_f < A_g(params)/(2*params.b):
        
        S_x = params.t_w * (params.d-params.t_f)**2/4 + \
            params.b * params.d * params.t_f / 2 - \
            params.b**2*params.t_f**2/(4*params.t_w)
    else:
        S_x =  params.t_w * params.d**2/2 + params.b * params.t_f **2/4 - \
            params.d*params.t_f*params.t_w/2 -\
            (params.d-params.t_f)**2 *params.t_w**2 / (4 * params.b)

    return S_x

def S_y(params: dict) -> float:
    '''Plastic section modulus - minor axis'''
    b_w=(params.d-params.t_f)
    r_1 = 0 if math.isnan(params.r_1) else params.r_1
    S_y =2*b_w*(params.t_w/2)**2/2 + 2*params.t_f*(params.b/2)**2/2+ 2*  (1-math.pi/4)*r_1**2*(-0.776*r_1 + r_1 +params.t_w/2)
    return S_y

def I_w(params: dict) -> float:
    '''Warping constant'''
    return 0

def J(params: dict) -> float:
    '''Torsion constant'''
    #Darwish and Johnston, 1965
    D_1 = ((params.t_f + params.r_1)**2 + params.t_w *
            (params.r_1 + params.t_w/4))/(2*params.r_1 + params.t_f)
    alpha_1 = -0.042 + 0.2204*params.t_w/params.t_f + 0.1355 * params.r_1/params.t_f \
        - 0.0865*params.t_w * params.r_1 / params.t_f**2 - 0.0725*params.t_w**2 / params.t_f**2
    J = params.b * params.t_f**3/3 + (params.d - params.t_f)/3 * params.t_w**3 + \
        alpha_1 * D_1**4 - 0.105*params.t_w**4 - 2*0.105*params.t_f**4
    return J   



def main():
    params_dict={
    'name':'125BT15.7 (GR300)',	
    #'section':'125BT15.7',	
    #'sec_grade':'GR300',	
    'sec_type':'BT',	
    'd':125,	
    'b':146,	
    't_f':8.6,	
    't_w':6.1,	
    'r_1':8.9
    }



    from steelas.member.geometry import SectionGeometry    
    sg = SectionGeometry(**params_dict)
    print(sg)

    check_vals = {'d_1':116,	'A_g':2000,		'y_C':26.5,	'I_x':2580000,	'Z_xf':97300,	'Z_xs':26200,	'Z_x':26200,	'S_x':46200,	'r_x':35.9,	'I_y':2230000,	'Z_y':30600,	'S_y':47100,	'r_y':33.4,	'J':444000,	'I_w':math.nan,	'f_y':320,	'f_yw':320,	'k_f':0.909,	'Z_exf':39000,	'Z_exs':29100,	'Z_ex':29100,	'Z_ey':45700,	'f_u':440}

    print(sg.y_c)
    print(check_vals['y_C'])

    print(sg.A_g)
    print(check_vals['A_g'])
    
    print(sg.I_x)
    print(check_vals['I_x'])

    print(sg.I_y)
    print(check_vals['I_y'])
    
    print(sg.S_x)
    print(check_vals['S_x'])

    print(sg.S_y)
    print(check_vals['S_y'])

    print(sg.J)
    print(check_vals['J'])
    

if __name__ == "__main__":
    main()
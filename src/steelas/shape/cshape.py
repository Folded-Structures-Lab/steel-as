
import math

def x_c(params: dict) -> float:
    '''centroid distance from left-hand side'''
    b_w=params.d-2*params.t_f
    x_c = (params.t_w**2/2*b_w+2*params.b**2/2*params.t_f+2*(1-math.pi/4)*params.r_1**2*(params.r_1-0.776*params.r_1 + params.t_w))/A_g(params)
    #x_c = (2*params.t_f*params.b**2/2 + params.t_w**2*(params.d-2*params.t_w)/2)/params.A_g
    return x_c

def x_pna(params:dict) -> float:
    '''plastic neutral axis distance from left-hand side'''
    if params.t_w < A_g(params)/(2*params.d):
        x= params.b-A_g(params)/(4*params.t_f)
    else:
        x=A_g(params)/(2*params.d)
    return x

def A_g(params: dict) -> float:
    '''Gross area'''
    b_f = params.b-params.t_w
    A_g = 2*params.t_f*b_f + params.d*params.t_w + 2*(1-math.pi/4)*params.r_1**2
    return A_g
    #return math.pi*((params.d/2)**2 - ((params.d/2)-params.t)**2)   

def I_x(params: dict) -> float:
    '''Moment of inertia - major axis'''
    b_f = params.b-params.t_w
    I_x =1/12 * params.t_w*params.d**3 + 2/12 * params.t_f**3 * b_f + params.t_f*b_f *2 *(params.d/2 - params.t_f/2)**2 + 2*(0.01825*params.r_1**4 + (1-math.pi/4)*params.r_1**2*(0.776*params.r_1 - params.r_1 +params.d/2 - params.t_f)**2)
    return I_x
    #return math.pi/64 * (params.d**4 - (params.d-2*params.t)**4)

def I_y(params: dict) -> float:
    '''Moment of inertia - minor axis'''
    b_w=params.d-2*params.t_f
    x_cur = x_c(params)
    I_y =1/12 * b_w * params.t_w**3 + 2/12 * params.b**3 * params.t_f +\
          b_w*params.t_w *(x_cur - params.t_w/2)**2 + 2*params.t_f*params.b*(params.b/2 - x_cur)**2  + 2*(0.01825*params.r_1**4 + (1-math.pi/4)*params.r_1**2*(x_cur -  params.t_w - (1-0.776)*params.r_1)**2)
    return I_y
    #return I_x(params)

def S_x(params: dict) -> float:
    '''Plastic section modulus - major axis'''
    b_w=params.d-2*params.t_f
    S_x =2*(params.t_w*(b_w/2)**2/2+params.t_f*params.b*(params.d/2-params.t_f/2)) + 2*  (1-math.pi/4)*params.r_1**2*(0.776*params.r_1 - params.r_1 +params.d/2 - params.t_f)
    return S_x

def S_y(params: dict) -> float:
    '''Plastic section modulus - minor axis'''
    b_f = params.b-params.t_w
    b_w=params.d-2*params.t_f
    #NOTE -> plastic neutral axis, not centroid
    x_cur = x_pna(params)
    if x_cur>params.t_w:
        #https://calcresource.com/cross-section-channel.html
        #NOTE: neglects corner fillets
        S_y = params.t_f * b_f**2/2 + params.b * params.d * params.t_w/2 - params.d**2 * params.t_w**2/8/params.t_f 
    else:
        S_y = 1/(4*params.d)*(4*params.t_f*params.b**2*(params.d-params.t_f)+params.t_w**2*(params.d**2-4*params.t_f**2)-4*params.b*params.t_f*b_w*params.t_w)
    
    #add fillet material
    x_rad = (1-0.776)*params.r_1 
    if x_cur > (params.t_w +x_rad):
        x_fillet = (x_cur-params.t_w-x_rad)
    #elif x_cur > params.t_w:
    #    x_fillet = 0
    else:
        x_fillet = (params.t_w-x_cur)+x_rad
    
    S_y_extra = 2*  (1-math.pi/4)*params.r_1**2 *x_fillet
    S_y = S_y + S_y_extra
    return S_y

def I_w(params: dict) -> float:
    '''Warping constant'''
    #I_w = (params.d-params.t_f)**2/4*(params.I_y - params.A_g * (params.x_c-params.t_w/2)**2 * ((params.d-params.t_f)**2*params.A_g/(4*params.I_x)-1))
    x_cur = x_c(params)
    A_g_cur = A_g(params)
    I_w = (params.d-params.t_f)**2/4*(params.I_y - A_g_cur * (x_cur-params.t_w/2)**2 * ((params.d-params.t_f)**2*A_g_cur/(4*params.I_x)-1))
    return I_w

def J(params: dict) -> float:
    '''Torsion constant'''
    alpha_3 = -0.0908 + 0.2621 * params.t_w / params.t_f + 0.1231 * params.r_1 / params.t_f -  0.0752 * params.t_w * params.r_1 / params.t_f**2 - 0.0945*params.t_w**2 / params.t_f**2
    D_3 = 2*((3*params.r_1 + params.t_w + params.t_f) - (2*(2*params.r_1 + params.t_w)*(2*params.r_1 + params.t_f))**0.5)
    J = 2 * params.b * params.t_f**3/3 + 1/3 * (params.d - 2 * params.t_f) * params.t_w**3   +  2 * alpha_3 * D_3**4 - 2*0.105*params.t_f**4
    return J




def main():
    params_dict={
        'name': '200PFC (GR300)',
        'sec_type': 'PFC',
        'd': 200,
        'b': 75,
        't_f': 12,
        't_w': 6, 
        'r_1': 12
    }

    check_vals = {'d_1':176,	'A_g':2920,	'A_s':0.678,	'x_C':24.4,	'x_0':50.5,	'I_x':19100000,	'Z_x':191000,	'S_x':221000,	'r_x':80.9,	'I_y':1650000,	'Z_y':32700,	'Z_yL':67800,	'S_y':58900,	'r_y':23.8,	'J':105000,	'I_w':10600000000}

    params_dict={
        'name':'75PFC (GR300)',
        'sec_type':'PFC',
        'd':75,	
        'b':40,	
        't_f':6.1,	
        't_w':3.8,	
        'r_1':8
    }
    check_vals = {'d_1':62.8,	'A_g':754,	'A_s':0.296,	'x_C':13.7,	'x_0':27.2,	'I_x':683000,	'Z_x':18200,	'S_x':21400,	'r_x':30.1,	'I_y':120000,	'Z_y':4560,	'Z_yL':8710,	'S_y':8200,	'r_y':12.6,	'J':8420,	'I_w':106000000}

    from steelas.member.geometry import SectionGeometry    
    sg = SectionGeometry(**params_dict)
    print(sg)


    print(sg.x_c)
    print(check_vals['x_C'])

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

    print(sg.I_w)
    print(check_vals['I_w'])
    
    
if __name__ == "__main__":
    main()
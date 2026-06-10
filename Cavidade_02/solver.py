import numpy as np

def boundary_conditions(u , v, P, u_max):
    ## Face esquerda
    u[:,0] = - u[:,1]
    v[:,0] = - v[:,1]   
    P[:,0] = P[:,1]

    ## Face direita
    u[-1,:] = - u[-2,:]
    v[-1,:] = - v[-2,:]
    P[-1,:] = P[-2,:]

    ## Face inferior
    u[0,:] = - u[1,:]
    v[0,:] = - v[1,:]
    P[0,:] = P[1,:]

    ## Face superior
    u[-1, :] = 2 * u_max - u[-2,:]
    v[-1, :] = - v[-2,:]
    P[-1, :] = P[-2,:]


def u_estrela(u, v, P, dx, dy, dt,  rho, nu):
    u_estrela = np.copy(u)
    for j in range(1, u.shape[0]-1):
        for i in range(1, u.shape[1]-1):
            du2_dx = (u[j,i]**2 - u[j,i-1]**2) / dx
            duv_dy = ((u[j+1,i] + u[j,i]) * (v[j+1,i] + v[j+1,i-1]) - (u[j,i] + u[j-1,i]) * (v[j,i] + v[j,i-1])) / (4*dy)
            dP_dx = (P[j,i+1] - P[j,i]) / (dx)
            d2u_dx2 = (u[j,i+1] - 2*u[j,i] + u[j,i-1]) / dx**2
            d2u_dy2 = (u[j+1,i] - 2*u[j,i] + u[j-1,i]) / dy**2
            
            u_estrela[j, i] = u[j, i] + dt * (-du2_dx - duv_dy - dP_dx/rho + nu * (d2u_dx2 + d2u_dy2)) 
    return u_estrela

def v_estrela(u, v, P, dx, dy, dt, rho, nu):
    v_estrela = np.copy(v)
    for j in range(1, v.shape[0]-1):
        for i in range(1, v.shape[1]-1):
            duv_dx = ((u[j,i+1] + u[j,i]) * (v[j+1,i] + v[j+1,i-1]) - (u[j,i] + u[j,i-1]) * (v[j,i] + v[j,i-1])) / (4*dx)
            dv2_dy = (v[j+1,i]**2 - v[j-1,i]**2) / (2*dy)
            dP_dy = (P[j+1,i] - P[j,i]) / (dy)
            d2v_dx2 = (v[j,i+1] - 2*v[j,i] + v[j,i-1]) / dx**2
            d2v_dy2 = (v[j+1,i] - 2*v[j,i] + v[j-1,i]) / dy**2
            
            v_estrela[j, i] = v[j, i] + dt * (-duv_dx - dv2_dy - dP_dy/rho + nu * (d2v_dx2 + d2v_dy2)) 
    return v_estrela


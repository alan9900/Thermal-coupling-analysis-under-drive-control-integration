"""Consistent nodal heat-capacity row sums for linear SOLID278 topologies.

Gaussian integration computes integral(N_i dV); do not use arithmetic nodal
temperature to claim stored energy. Reject unsupported/folded elements.
"""
import numpy as np
from itertools import product
def weights(x):
    x=np.asarray(x,float);n,k,_=x.shape
    if k==4:
        v=np.abs(np.linalg.det(np.stack([x[:,1]-x[:,0],x[:,2]-x[:,0],x[:,3]-x[:,0]],axis=2)))/6
        if np.any(v<=0):raise ValueError('Degenerate tetrahedral volume')
        return np.repeat(v[:,None]/4,4,axis=1),v
    if k not in [5,6,8]:raise ValueError('Unsupported solid connectivity '+str(k))
    out=np.zeros((n,k));vol=np.zeros(n);sign=None
    if k==6:
        rule=[(r,s,t,w*.5) for (r,s,w) in [(1/6,1/6,1/6),(2/3,1/6,1/6),(1/6,2/3,1/6)] for t in [-1/np.sqrt(3),1/np.sqrt(3)]]
        # Triangle weights already integrate reference area=1/2; z weight=1.
        rule=[(r,s,t,w*2) for r,s,t,w in rule]
    else:rule=[(r,s,t,1) for r,s,t in product([-1/np.sqrt(3),1/np.sqrt(3)],repeat=3)]
    for r,s,t,w in rule:
        if k==8:
            a=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
            N=np.prod(1+a*np.array([r,s,t]),axis=1)/8
            d=np.column_stack([a[:,j]*np.prod(np.delete(1+a*np.array([r,s,t]),j,axis=1),axis=1)/8 for j in range(3)])
        elif k==5:
            a=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
            N=np.r_[np.prod(1+a*np.array([r,s]),axis=1)*(1-t)/8,(1+t)/2]
            d=np.zeros((5,3));d[:4,0]=a[:,0]*(1+a[:,1]*s)*(1-t)/8;d[:4,1]=a[:,1]*(1+a[:,0]*r)*(1-t)/8
            d[:4,2]=-np.prod(1+a*np.array([r,s]),axis=1)/8;d[4,2]=.5
        else:
            L=np.array([1-r-s,r,s]);dL=np.array([[-1,-1],[1,0],[0,1]])
            N=np.r_[L*(1-t)/2,L*(1+t)/2]
            d=np.zeros((6,3));d[:3,:2]=dL*(1-t)/2;d[3:,:2]=dL*(1+t)/2;d[:3,2]=-L/2;d[3:,2]=L/2
        determinant=np.linalg.det(np.einsum('nki,kj->nij',x,d))
        current=np.sign(determinant)
        if sign is None:sign=current
        elif np.any(current!=sign):raise ValueError('Folded solid Jacobian')
        dv=np.abs(determinant)*w;out+=dv[:,None]*N;vol+=dv
    if np.any(vol<=0) or np.any(out<0):raise ValueError('Invalid volume/capacity weights')
    assert np.max(np.abs(out.sum(axis=1)-vol)/vol)<1e-12
    return out,vol

def self_test():
    cells=[(np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]]),1/6,.25),
        (np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[.5,.5,1]]),1/3,.25),
        (np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,0,1],[0,1,1]]),.5,.5),
        (np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]]),1,.5)]
    for x,v,z in cells:
        w,vol=weights(x[None,:,:]);assert abs(vol[0]-v)<1e-12
        assert abs(w[0]@x[:,2]-v*z)<1e-12
        w2,v2=weights((2*x+np.array([3,4,5]))[None,:,:]);assert abs(v2[0]-8*v)<1e-11 and np.max(abs(w2-8*w))<1e-11
    for invalid in [np.zeros((1,4,3)),np.zeros((1,7,3))]:
        try:weights(invalid)
        except ValueError:pass
        else:raise AssertionError('Invalid volume/topology must be rejected')
    print('PASS four topology analytic volume, linear-temperature integration, partition unity and affine scaling; degenerate/unsupported cells rejected')
if __name__=='__main__':self_test()

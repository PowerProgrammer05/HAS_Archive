import numpy as np
import pandas as pd
def randomwalk_laplacian(weights=pd.DataFrame()): #weights are raw weights, pandas dataframe
    A = weights.to_numpy()  #adjacency ma
    n = len(A)

    D = A.sum(axis=1) #degree matrix
    D_safe = np.where(D == 0, 1, D)  # avoid division by zero
    I = np.identity(n) #identity matrix
    P = A / D_safe[:, None]

    randomwalk_laplacian = I - P
    return randomwalk_laplacian

def spectral(L):
    if np.allclose(L, L.T, atol=1e-8):
        eigvals, eigvecs = np.linalg.eigh(L)  #symmetric일때
    else:
        eigvals, eigvecs = np.linalg.eig(L) 
    return eigvals, eigvecs

a = pd.read_csv("datas/high_raw_weight.csv", index_col=0)


L = randomwalk_laplacian(a)
val, vec = spectral(L)
print(vec.shape)
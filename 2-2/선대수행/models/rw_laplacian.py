import numpy as np
import pandas as pd


def randomwalk_laplacian(weights=pd.DataFrame()): 
    A = weights.to_numpy()  # adjacency matrix
    n = len(A)

    D = A.sum(axis=1)  # degree matrix
    D_safe = np.where(D == 0, 1, D)  # avoid division by zero
    I = np.identity(n)  # identity matrix
    P = A / D_safe[:, None]

    randomwalk_laplacian = I - P
    return randomwalk_laplacian


def spectral(L):
    if np.allclose(L, L.T, atol=1e-8):
        eigvals, eigvecs = np.linalg.eigh(L)  # symmetric일 때
    else:
        eigvals, eigvecs = np.linalg.eig(L) 
    return eigvals, eigvecs


class laplacian_spectral:
    
    def __init__(self, weights: np.ndarray):
        self.weights = weights
        self.laplacian = None
        self.eigvals = None
        self.eigvecs = None
        
    def compute_laplacian(self, normalized: bool = True):
        if normalized:
            # Normalized Laplacian: L_norm = I - D^{-1/2} A D^{-1/2}
            D = np.diag(self.weights.sum(axis=1))
            D_sqrt_inv = np.diag(1.0 / np.sqrt(np.diag(D) + 1e-10))
            self.laplacian = np.eye(len(self.weights)) - D_sqrt_inv @ self.weights @ D_sqrt_inv
        else:
            # Unnormalized Laplacian: L = D - A
            D = np.diag(self.weights.sum(axis=1))
            self.laplacian = D - self.weights
        
        return self.laplacian
    
    def compute_spectrum(self, n_components: int = None):
        if self.laplacian is None:
            self.compute_laplacian()
        
        eigvals, eigvecs = spectral(self.laplacian)
        
        idx = np.argsort(np.abs(eigvals))
        self.eigvals = eigvals[idx]
        self.eigvecs = eigvecs[:, idx]
        
        if n_components:
            self.eigvals = self.eigvals[:n_components]
            self.eigvecs = self.eigvecs[:, :n_components]
        
        return self.eigvals, self.eigvecs
    
    def get_eigenvectors(self, n: int = 3):
        if self.eigvecs is None:
            self.compute_spectrum(n_components=n)
        return self.eigvecs[:, :n]
    
    def get_eigenvalues(self, n: int = 3):
        if self.eigvals is None:
            self.compute_spectrum(n_components=n)
        return self.eigvals[:n]

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import torch

from ._dsmm import DSMM
from ._normal_cdf import NormalCDF
from ._log_normal_cdf import LogNormalCDF


def add_diag(input, diag):
    """
    Adds a diagonal matrix s*I to the input matrix input.

    Args:
        :attr:`input` (Tensor (nxn) or (bxnxn)):
            Tensor or LazyTensor wrapping matrix to add diagonal component to.
        :attr:`diag` (scalar or Tensor (n) or Tensor (bxn) or Tensor (bx1)):
            Diagonal component to add to tensor

    Returns:
        :obj:`Tensor` (bxnxn or nxn)
    """
    if torch.is_tensor(input):
        from ..lazy import NonLazyTensor
        return NonLazyTensor(input).add_diag()
    else:
        return input.add_diag(diag)


def add_jitter(mat):
    """
    Adds "jitter" to the diagonal of a matrix.
    This ensures that a matrix that *should* be positive definite *is* positive definate.

    Args:
        - mat (matrix nxn) - Positive definite matrxi
    Returns: (matrix nxn)
    """
    if hasattr(mat, "add_jitter"):
        return mat.add_jitter()
    else:
        diag = torch.eye(mat.size(-1), dtype=mat.dtype, device=mat.device).mul_(1e-3)
        if mat.ndimension() == 3:
            return mat + diag.unsqueeze(0).expand(mat.size(0), mat.size(1), mat.size(2))
        else:
            return mat + diag


def dsmm(sparse_mat, dense_mat):
    """
    Performs the (batch) matrix multiplication S x D
    where S is a sparse matrix and D is a dense matrix

    Args:
        - sparse_mat (matrix (b x)mxn) - Tensor wrapping sparse matrix
        - dense_mat (matrix (b x)nxo) - Tensor wrapping dense matrix

    Returns:
        - matrix (b x)mxo - Result
    """
    return DSMM(sparse_mat)(dense_mat)


def exact_predictive_mean(full_covar, full_mean, train_labels, num_train, likelihood, precomputed_cache=None):
    """
    Computes the posterior predictive mean of a GP

    Args:
    - full_covar ( (n+t) x (n+t) ) - the block prior covariance matrix of training and testing points
        - [ K_XX, K_XX*; K_X*X, K_X*X* ]
    - full_mean (n + t) - the training and test prior means, stacked on top of each other
    - train_labels (n) - the training labels minus the training prior mean
    - noise (1) - the observed noise (from the likelihood)
    - precomputed_cache - speeds up subsequent computations (default: None)

    Returns:
    - (t) - the predictive posterior mean of the test points
    """
    if not num_train:
        return full_mean, None

    if not hasattr(full_covar, "exact_predictive_mean"):
        from ..lazy.non_lazy_tensor import NonLazyTensor

        full_covar = NonLazyTensor(full_covar)
    return full_covar.exact_predictive_mean(full_mean, train_labels, num_train, likelihood, precomputed_cache)


def exact_predictive_covar(full_covar, num_train, likelihood, precomputed_cache=None):
    """
    Computes the posterior predictive covariance of a GP

    Args:
    - full_covar ( (n+t) x (n+t) ) - the block prior covariance matrix of training and testing points
        - [ K_XX, K_XX*; K_X*X, K_X*X* ]
    - num_train (int) - how many training points are there in the full covariance matrix
    - noise (1) - the observed noise (from the likelihood)
    - precomputed_cache - speeds up subsequent computations (default: None)

    Returns:
    - LazyTensor (t x t) - the predictive posterior covariance of the test points
    """
    if not num_train:
        return full_covar, None

    if not hasattr(full_covar, "exact_predictive_covar"):
        from ..lazy.non_lazy_tensor import NonLazyTensor

        full_covar = NonLazyTensor(full_covar)
    return full_covar.exact_predictive_covar(num_train, likelihood, precomputed_cache)


def log_normal_cdf(x):
    """
    Computes the element-wise log standard normal CDF of an input tensor x.

    This function should always be preferred over calling normal_cdf and taking the log
    manually, as it is more numerically stable.
    """
    return LogNormalCDF()(x)


def matmul(mat, rhs):
    """
    Computes a matrix multiplication between a matrix (mat) and a right hand side (rhs).
    If mat is a tensor, then this is the same as torch.matmul.
    This function can work on lazy tensors though

    Args:
        - mat (matrix nxn) - left hand size matrix
        - rhs (matrix nxk) - rhs matrix or vector

    Returns:
        - matrix nxk
    """
    return mat.matmul(rhs)


def inv_matmul(mat, rhs):
    """
    Computes a linear solve with several right hand sides.

    Args:
        - mat (matrix nxn) - Matrix to solve with
        - rhs (matrix nxk) - rhs matrix or vector

    Returns:
        - matrix nxk - (mat)^{-1} rhs
    """
    if hasattr(mat, "inv_matmul"):
        return mat.inv_matmul(rhs)
    else:
        from ..lazy.non_lazy_tensor import NonLazyTensor

        return NonLazyTensor(mat).inv_matmul(rhs)


def inv_quad(mat, tensor):
    """
    Computes an inverse quadratic form (w.r.t mat) with several right hand sides.
    I.e. computes tr( tensor^T mat^{-1} tensor )

    Args:
        - tensor (tensor nxk) - Vector (or matrix) for inverse quad

    Returns:
        - tensor - tr( tensor^T (mat)^{-1} tensor )
    """
    res, _ = inv_quad_log_det(mat, inv_quad_rhs=tensor, log_det=False)
    return res


def inv_quad_log_det(mat, inv_quad_rhs=None, log_det=False):
    """
    Computes an inverse quadratic form (w.r.t mat) with several right hand sides.
    I.e. computes tr( tensor^T mat^{-1} tensor )
    In addition, computes an (approximate) log determinant of the the matrix

    Args:
        - tensor (tensor nxk) - Vector (or matrix) for inverse quad

    Returns:
        - scalar - tr( tensor^T (mat)^{-1} tensor )
        - scalar - log determinant
    """
    if hasattr(mat, "inv_quad_log_det"):
        return mat.inv_quad_log_det(inv_quad_rhs, log_det)
    else:
        from ..lazy.non_lazy_tensor import NonLazyTensor

        return NonLazyTensor(mat).inv_quad_log_det(inv_quad_rhs, log_det)


def log_det(mat):
    """
    Computes an (approximate) log determinant of the matrix

    Returns:
        - scalar - log determinant
    """
    _, res = inv_quad_log_det(mat, inv_quad_rhs=None, log_det=True)
    return res


def normal_cdf(x):
    """
    Computes the element-wise standard normal CDF of an input tensor x.
    """
    return NormalCDF()(x)


def root_decomposition(mat):
    """
    Returns a (usually low-rank) root decomposotion lazy tensor of a PSD matrix.
    This can be used for sampling from a Gaussian distribution, or for obtaining a
    low-rank version of a matrix
    """
    if hasattr(mat, "root_decomposition"):
        return mat.root_decomposition()
    else:
        from ..lazy.non_lazy_tensor import NonLazyTensor

        return NonLazyTensor(mat).root_decomposition()


def root_inv_decomposition(mat, initial_vectors=None, test_vectors=None):
    """
    Returns a (usually low-rank) root decomposotion lazy tensor of a PSD matrix.
    This can be used for sampling from a Gaussian distribution, or for obtaining a
    low-rank version of a matrix
    """
    if hasattr(mat, "root_inv_decomposition"):
        return mat.root_inv_decomposition(initial_vectors, test_vectors)
    else:
        from ..lazy.non_lazy_tensor import NonLazyTensor

        return NonLazyTensor(mat).root_inv_decomposition(initial_vectors, test_vectors)


__all__ = [
    "add_diag",
    "dsmm",
    "exact_predictive_mean",
    "exact_predictive_covar",
    "inv_matmul",
    "inv_quad",
    "inv_quad_log_det",
    "log_det",
    "log_normal_cdf",
    "matmul",
    "normal_cdf",
    "root_decomposition",
    "root_inv_decomposition",
]

"""Utility functions for initializing weights and biases."""

import math
from functools import lru_cache
import numpy as np
import torch
from scipy import special
from scipy.stats import truncnorm


def _prod(nums):
    out = 1
    for n in nums:
        out = out * n
    return out


def _calculate_fan(linear_weight_shape, fan="fan_in"):
    fan_out, fan_in = linear_weight_shape

    if fan == "fan_in":
        f = fan_in
    elif fan == "fan_out":
        f = fan_out
    elif fan == "fan_avg":
        f = (fan_in + fan_out) / 2
    else:
        raise ValueError("Invalid fan option")

    return f


@lru_cache(maxsize=1)
def _trunc_normal_constants():
    # Match SciPy's central-interval mass expression and arithmetic order.
    # These distribution constants are independent of shape, scale and RNG.
    return (
        truncnorm.std(a=-2, b=2, loc=0, scale=1),
        special.log_ndtr(-2.0),
        special.log1p(-special.ndtr(-2.0) - special.ndtr(-2.0)),
    )


def trunc_normal_init_(weights, scale=1.0, fan="fan_in"):
    shape = weights.shape
    f = _calculate_fan(shape, fan)
    scale = scale / max(1, f)
    correction, log_cdf, log_mass = _trunc_normal_constants()
    std = math.sqrt(scale) / correction
    size = _prod(shape)
    if (std <= 0 or not math.isfinite(std)
            or not hasattr(special, "logsumexp")):
        # Older SciPy versions used a different inverse-CDF expression. Keep
        # their sampler, validation and zero-scale behavior unchanged.
        samples = truncnorm.rvs(a=-2, b=2, loc=0, scale=std, size=size)
    else:
        # SciPy's inverse-CDF sampler, specialized to the fixed [-2, 2]
        # interval. Preserve its uniform draws and logsumexp reduction; an
        # algebraically equivalent CDF or logaddexp would round differently.
        uniform = truncnorm.random_state.uniform(size=size)
        log_probability = special.logsumexp(
            [np.full_like(uniform, log_cdf), np.log(uniform) + log_mass], axis=0
        )
        samples = special.ndtri_exp(log_probability) * std + 0
    samples = np.reshape(samples, shape)
    with torch.no_grad():
        weights.copy_(torch.tensor(samples, device=weights.device))


def lecun_normal_init_(weights):
    trunc_normal_init_(weights, scale=1.0)


def he_normal_init_(weights):
    trunc_normal_init_(weights, scale=2.0)


def glorot_uniform_init_(weights):
    torch.nn.init.xavier_uniform_(weights, gain=1)


def final_init_(weights):
    with torch.no_grad():
        weights.fill_(0.0)


def gating_init_(weights):
    with torch.no_grad():
        weights.fill_(0.0)


def bias_init_zero_(bias):
    with torch.no_grad():
        bias.fill_(0.0)


def bias_init_one_(bias):
    with torch.no_grad():
        bias.fill_(1.0)


def normal_init_(weights):
    torch.nn.init.kaiming_normal_(weights, nonlinearity="linear")


def ipa_point_weights_init_(weights):
    with torch.no_grad():
        softplus_inverse_1 = 0.541324854612918
        weights.fill_(softplus_inverse_1)

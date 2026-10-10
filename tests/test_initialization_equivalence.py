"""Initialization must preserve parameters and subsequent stochastic behavior."""
import math

import numpy as np
import pytest
from scipy.stats import truncnorm
import torch

from boltzgen.model.layers.initialize import trunc_normal_init_


@pytest.mark.parametrize('shape', [(0, 7), (1, 1), (17, 31), (384, 384), (1024, 1024)])
@pytest.mark.parametrize('scale,fan', [(1.0, 'fan_in'), (2.0, 'fan_out'), (0.25, 'fan_avg'), (0.0, 'fan_in')])
@pytest.mark.parametrize('dtype', [torch.float16, torch.float32, torch.float64, torch.bfloat16])
def test_initializer_matches_scipy_and_rng(shape, scale, fan, dtype):
    f = {'fan_in': shape[1], 'fan_out': shape[0],
         'fan_avg': sum(shape) / 2}[fan]
    std = math.sqrt(scale / max(1, f)) / truncnorm.std(-2, 2)
    np.random.seed(137)
    torch.manual_seed(241)
    expected = torch.tensor(truncnorm.rvs(-2, 2, scale=std, size=math.prod(shape))
                            .reshape(shape), dtype=dtype)
    expected_numpy = np.random.get_state()
    expected_torch = torch.get_rng_state().clone()
    np.random.seed(137)
    torch.manual_seed(241)
    actual = torch.empty(shape, dtype=dtype, requires_grad=True)
    trunc_normal_init_(actual, scale, fan)
    assert torch.equal(actual, expected)
    state = np.random.get_state()
    assert state[0] == expected_numpy[0]
    np.testing.assert_array_equal(state[1], expected_numpy[1])
    assert state[2:] == expected_numpy[2:]
    assert torch.equal(torch.get_rng_state(), expected_torch)


def test_initializer_handles_noncontiguous_parameter():
    np.random.seed(91)
    expected = torch.empty((9, 13), dtype=torch.float64)
    trunc_normal_init_(expected)
    np.random.seed(91)
    actual = torch.empty((13, 9), dtype=torch.float64).T
    trunc_normal_init_(actual)
    assert torch.equal(actual, expected)


@pytest.mark.parametrize('generator', [False, True])
def test_initializer_preserves_distribution_rng(generator):
    original = truncnorm.random_state
    try:
        rng = np.random.default_rng(718) if generator else np.random.RandomState(718)
        truncnorm.random_state = rng
        expected = torch.tensor(truncnorm.rvs(-2, 2, scale=math.sqrt(1/13) / truncnorm.std(-2, 2),
                                            size=9*13).reshape(9, 13), dtype=torch.float64)
        expected_next = rng.uniform(size=10)
        truncnorm.random_state = np.random.default_rng(718) if generator else np.random.RandomState(718)
        actual = torch.empty((9, 13), dtype=torch.float64)
        trunc_normal_init_(actual)
        assert torch.equal(actual, expected)
        np.testing.assert_array_equal(truncnorm.random_state.uniform(size=10), expected_next)
    finally:
        truncnorm.random_state = original


@pytest.mark.skipif(not torch.cuda.is_available(), reason='CUDA unavailable')
@pytest.mark.parametrize('dtype', [torch.float16, torch.float32, torch.float64, torch.bfloat16])
def test_initializer_cuda_values_and_rng(dtype):
    np.random.seed(153)
    expected = torch.tensor(truncnorm.rvs(-2, 2, scale=math.sqrt(1 / 31) / truncnorm.std(-2, 2),
                                        size=17*31).reshape(17, 31), device='cuda', dtype=dtype)
    expected_state = np.random.get_state()
    torch_state = torch.get_rng_state().clone()
    cuda_state = torch.cuda.get_rng_state().clone()
    np.random.seed(153)
    actual = torch.empty((17, 31), device='cuda', dtype=dtype, requires_grad=True)
    trunc_normal_init_(actual)
    assert torch.equal(actual, expected)
    state = np.random.get_state()
    np.testing.assert_array_equal(state[1], expected_state[1])
    assert state[2:] == expected_state[2:]
    assert torch.equal(torch.get_rng_state(), torch_state)
    assert torch.equal(torch.cuda.get_rng_state(), cuda_state)

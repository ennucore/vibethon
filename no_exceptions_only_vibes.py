#!/usr/bin/env python3
"""A small zoo of *argument-free* functions for Vibezz.

Each function is self-contained (no parameters) and raises exactly one
exception that can be repaired on the fly in a pdb session by tweaking
locals or patching state.
"""

import math
import json
import datetime as _dt

# 1 ─────────────────────────────────────────────────────────────────────

def zero_division_demo():
    """
    """
    numerator = 42
    denominator = 0
    return numerator / denominator


# 2 ─────────────────────────────────────────────────────────────────────

def missing_list_item():
    """
    """
    nums = [0, 1, 2]
    target_index = 5
    return nums[target_index]


# 3 ─────────────────────────────────────────────────────────────────────

def negative_square_root():
    """
    """
    x = -16
    return math.sqrt(x)


# 4 ─────────────────────────────────────────────────────────────────────

def json_key_error():
    """
    """
    payload = '{"user": "alice"}'
    data = json.loads(payload)
    return f"Alice is {data['age']} years old"


# 5 ─────────────────────────────────────────────────────────────────────

def sort_mixed_types():
    """
    """
    items = [3, "two", 1, "zero"]
    items.sort()
    return items


# 6 ─────────────────────────────────────────────────────────────────────

def stale_cache_access():
    """
    """
    cache_entry = None
    return cache_entry.isoformat()


# 7 ─────────────────────────────────────────────────────────────────────

def fibonacci_negative():
    """
    """
    n = -8

    def fib(k):
        if k < 0:
            raise ValueError("n must be >= 0")
        if k < 2:
            return k
        return fib(k-1) + fib(k-2)

    return fib(n)


# 8 ─────────────────────────────────────────────────────────────────────

def bad_json_payload():
    """
    """
    payload = '{not-valid-json]'
    return json.loads(payload)


# 9 ─────────────────────────────────────────────────────────────────────

def math_domain_error():
    """
    """
    base = 10
    power = 1000
    return base ** power


# 10 ────────────────────────────────────────────────────────────────────

def kinetic_energy_bug():
    """
    """
    m = 2   # kg
    v = 3   # m/s
    energy = m * v * v   # missing 0.5
    assert abs(energy - 9) < 1e-9  # will raise AssertionError
    return energy


# 11 ────────────────────────────────────────────────────────────────────

def projectile_range_bug():
    """
    """
    g = 9.81          # m/s²
    v = 20            # m/s
    theta = 45        # degrees but math.sin expects rad
    R = v**2 * math.sin(2*theta) / g
    assert 40 < R < 42, f"unreasonable range {R}"  # will fail
    return R


# 12 ────────────────────────────────────────────────────────────────────

def ideal_gas_bug():
    """
    """
    n = 1.0          # mol
    R = 8.314        # J/(mol·K)
    T = 300          # K
    V = 1.0          # litres (! should be 0.001 m³)
    P = n * R / T / V   # wrong formula + unit
    assert 95e3 < P < 105e3, P  # expect ~99 kPa
    return P


# 13 ────────────────────────────────────────────────────────────────────

def earth_escape_velocity_bug():
    """
    """
    G = 6.674e-11        # m³ kg⁻¹ s⁻²
    M = 5.972e24         # kg
    R = 6.371e6          # m
    v = 2 * G * M / R    # missing sqrt
    assert 11000 < v < 12000, v  # expect ≈11.2 km/s
    return v


# 14 ────────────────────────────────────────────────────────────────────

def radioactive_decay_bug():
    """
    """
    N0 = 1000
    half_life = 30  # days
    t = 15          # days
    lam = math.log(2) / half_life
    remaining = N0 ** (-lam * t)  # nonsensical
    assert 650 < remaining < 710, remaining  # expect ≈707
    return remaining

if __name__ == "__main__":
    print("🚀 Starting Vibezz - Enhanced Python Debugger")
    print("=" * 50)

    print("\nTesting all functions:")
    print("-" * 20)

    functions = [
        zero_division_demo,
        missing_list_item,
        negative_square_root,
        json_key_error,
        sort_mixed_types,
        stale_cache_access,
        fibonacci_negative,
        bad_json_payload,
        math_domain_error,
        kinetic_energy_bug,
        projectile_range_bug,
        ideal_gas_bug,
        earth_escape_velocity_bug,
        radioactive_decay_bug
    ]

    for func in functions:
        print(f"\nTesting {func.__name__}()...")
        try:
            result = func()
            print(f"✅ Success! Result: {result}")
        except Exception as e:
            print(f"❌ Failed with {type(e).__name__}: {str(e)}")
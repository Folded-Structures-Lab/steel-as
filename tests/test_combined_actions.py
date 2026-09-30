"""AS4100 Section 8 combined actions.

Expected values are hand calculations from the capacities pinned in
test_capacities_used_in_hand_calcs, rounded to 4 significant figures.
"""

import math

import pytest

from steelas.data.io import MemberLibrary
from steelas.member.member import SteelMember, SteelSection


@pytest.fixture(scope="module")
def ub150() -> SteelSection:
    return SteelSection.from_library(MemberLibrary.OpenSections, "150UB18.0 (GR300)")


@pytest.fixture(scope="module")
def member(ub150) -> SteelMember:
    # k_t < 1 so that N_t differs from N_s
    return SteelMember(section=ub150, l_ex=3000, l_ey=3000, l_eb=3000, k_t=0.75)


@pytest.fixture(scope="module")
def restrained_member(ub150) -> SteelMember:
    return SteelMember(section=ub150, l_ex=3000, l_ey=3000, l_eb=0, k_t=0.75)


def _member(library: MemberLibrary, name: str, **kwargs) -> SteelMember:
    return SteelMember(section=SteelSection.from_library(library, name), **kwargs)


@pytest.fixture(scope="module")
def ub610() -> SteelMember:
    return _member(MemberLibrary.OpenSections, "610UB101 (GR300)")


@pytest.fixture(scope="module")
def rhs125() -> SteelMember:
    return _member(MemberLibrary.HollowSections, "125x75x6RHS (C450)")


@pytest.fixture(scope="module")
def pfc150() -> SteelMember:
    return _member(MemberLibrary.OpenSections, "150PFC (GR300)")


@pytest.fixture(scope="module")
def uc250() -> SteelMember:
    return _member(MemberLibrary.OpenSections, "250UC72.9 (GR300)")


# braced in-plane with k_e = 0.7, no transverse load
BEAM_COLUMN = dict(
    l=3000,
    l_ex=2100,
    l_ey=3000,
    l_eb=3000,
    l_z=3000,
    alpha_m=1.3,
    beta_mx=0.5,
    beta_my=0,
    transverse_load=False,
)


@pytest.fixture(scope="module")
def beam_column(ub150) -> SteelMember:
    return SteelMember(section=ub150, **BEAM_COLUMN)


def test_capacities_used_in_hand_calcs(member, restrained_member):
    assert member.phi == 0.9
    assert member.M_sx == pytest.approx(43.2)
    assert member.M_sy == pytest.approx(8.61)
    assert member.M_bx == pytest.approx(20.5)
    assert member.N_s == pytest.approx(735)
    assert member.N_t == pytest.approx(644)
    assert member.N_cx == pytest.approx(618)
    assert member.N_cy == pytest.approx(131)
    assert restrained_member.M_bx == pytest.approx(43.2)


@pytest.mark.parametrize(
    "method, N_star, expected",
    [
        ("M_rx", 0, 43.2),  # M_sx
        ("M_rx", -100, 36.67),  # 43.2 * (1 - 100 / (0.9 * 735))
        ("M_rx", 100, 35.75),  # 43.2 * (1 - 100 / (0.9 * 644))
        ("M_rx", -700, 0),  # N* > phiN_s
        ("M_ry", -100, 7.308),  # 8.61 * (1 - 100 / (0.9 * 735))
        ("M_ry", 100, 7.124),  # 8.61 * (1 - 100 / (0.9 * 644))
        ("M_ix", -100, 35.43),  # 43.2 * (1 - 100 / (0.9 * 618))
        ("M_ix", 100, 35.75),  # Cl 8.4.2.3, M_rx
        ("M_iy", -50, 4.959),  # 8.61 * (1 - 50 / (0.9 * 131))
        ("M_iy", 100, 7.124),  # Cl 8.4.2.3, M_ry
        ("M_ox", -50, 11.81),  # 20.5 * (1 - 50 / (0.9 * 131))
        ("M_ox", 100, 24.04),  # 20.5 * (1 + 100 / (0.9 * 644)) < M_rx = 35.75
        ("M_cx", -50, 11.81),  # min(M_ix = 39.32, M_ox = 11.81)
        ("M_cx", 100, 24.04),  # min(M_rx = 35.75, M_ox = 24.04)
    ],
)
def test_general_capacities(member, method, N_star, expected):
    assert getattr(member, method)(N_star) == pytest.approx(expected, rel=1e-3, abs=1e-9)


def test_M_ox_tension_limited_to_M_rx(restrained_member):
    # 43.2 * (1 + 100 / (0.9 * 644)) = 50.65 > M_rx = 35.75
    assert restrained_member.M_ox(100) == pytest.approx(35.75, rel=1e-3)


@pytest.mark.parametrize(
    "fixture, compact, k_f, capacities",
    [
        ("member", ("C", "C"), 1.0, dict(M_sx=43.2, M_sy=8.61, N_s=735, N_t=644)),
        ("ub610", ("C", "C"), 0.888, dict(M_sx=870, M_sy=116, N_s=3460, N_t=3890)),
        ("rhs125", ("C", "C"), 1.0, dict(M_sx=37.9, M_sy=26.6, N_s=959, N_t=906)),
        ("pfc150", ("C", "C"), 1.0, dict(M_sx=41.3, M_sy=12.3, N_s=721, N_t=721)),
        ("uc250", ("N", "N"), 1.0, dict(M_sx=296, M_sy=136, N_s=2800, N_t=2800)),
    ],
)
def test_sections_used_in_hand_calcs(request, fixture, compact, k_f, capacities):
    m = request.getfixturevalue(fixture)
    slenderness = m.section.slenderness
    assert (slenderness.compact_x, slenderness.compact_y) == compact
    assert m.section.k_f == k_f
    assert {k: getattr(m, k) for k in capacities} == pytest.approx(capacities)


def test_ub610_web_slenderness_used_in_hand_calcs(ub610):
    # 572.4 / 10.6 * (300 / 250) ** 0.5, hot-rolled web in uniform compression
    web = ub610.section.slenderness.components_c[0]
    assert (web.lam_e, web.lam_ey) == pytest.approx((59.15, 45), rel=1e-3)


@pytest.mark.parametrize(
    "fixture, method, N_star, expected",
    [
        # Cl 8.3.2(a), compression with k_f = 1
        ("member", "M_rx", -300, 27.86),  # 1.18 * 43.2 * (1 - 300 / (0.9 * 735))
        ("member", "M_rx", -100, 43.2),  # 1.18 * 36.67 = 43.27 > M_sx
        ("rhs125", "M_rx", -300, 29.18),  # 1.18 * 37.9 * (1 - 300 / (0.9 * 959))
        # Cl 8.3.2(a), tension with k_f < 1
        ("ub610", "M_rx", 1000, 733.4),  # 1.18 * 870 * (1 - 1000 / (0.9 * 3890))
        # Cl 8.3.2(b): 870 * (1 - 1000 / (0.9 * 3460)) * (1 + 0.18 * (82 - 59.15) / (82 - 45))
        ("ub610", "M_rx", -1000, 656.3),
        # Cl 8.3.3(a)
        ("member", "M_ry", -300, 8.139),  # 1.19 * 8.61 * (1 - (300 / (0.9 * 735)) ** 2)
        ("member", "M_ry", 300, 7.501),  # 1.19 * 8.61 * (1 - (300 / (0.9 * 644)) ** 2)
        ("ub610", "M_ry", 2000, 92.99),  # 1.19 * 116 * (1 - (2000 / (0.9 * 3890)) ** 2)
        # Cl 8.3.3(b)
        ("rhs125", "M_ry", -300, 20.48),  # 1.18 * 26.6 * (1 - 300 / (0.9 * 959))
        # general form: compression with k_f < 1, not doubly symmetric, not compact
        ("ub610", "M_ry", -1000, 116.0),  # 1.19 * 116 * (1 - (-1000 / (0.9 * 3460)) ** 2)
        ("pfc150", "M_rx", -100, 34.94),  # 41.3 * (1 - 100 / (0.9 * 721))
        ("pfc150", "M_ry", -100, 10.40),  # 12.3 * (1 - 100 / (0.9 * 721))
        ("uc250", "M_rx", -500, 237.3),  # 296 * (1 - 500 / (0.9 * 2800))
    ],
)
def test_alternative_section_capacities(request, fixture, method, N_star, expected):
    m = request.getfixturevalue(fixture)
    assert getattr(m, method)(N_star, alternative=True) == pytest.approx(expected, rel=1e-3)


@pytest.mark.parametrize("fixture", ["member", "ub610", "rhs125"])
@pytest.mark.parametrize("method", ["M_rx", "M_ry"])
@pytest.mark.parametrize("load_ratio", [-1.2, -0.9, -0.5, -0.1, 0, 0.1, 0.5, 0.9])
def test_alternative_not_less_than_general(request, fixture, method, load_ratio):
    m = request.getfixturevalue(fixture)
    N_star = load_ratio * m.phiN_s
    capacity = getattr(m, method)
    assert capacity(N_star, alternative=True) >= capacity(N_star)


@pytest.mark.parametrize(
    "fixture, N_star, M_x_star, M_y_star, alternative, expected",
    [
        # general: N*/phiN + M_x*/(phi M_sx) + M_y*/(phi M_sy)
        ("member", -300, 10, 2, False, 0.9688),  # 300/661.5 + 10/38.88 + 2/7.749
        ("pfc150", -100, 10, 3, True, 0.6941),  # 100/648.9 + 10/37.17 + 3/11.07
        # alternative: (M_x*/phi M_rx)^gamma + (M_y*/phi M_ry)^gamma
        ("member", -300, 10, 2, True, 0.2722),  # gamma = 1.854, phiM_r = 25.07, 7.325
        ("member", 300, 10, 2, True, 0.3150),  # gamma = 1.918, phiM_r = 22.13, 6.751
        ("member", -500, 5, 1, True, 0.2633),  # gamma = 2.0 (limit), phiM_r = 11.20, 3.953
    ],
)
def test_section_biaxial_ratio(
    request, fixture, N_star, M_x_star, M_y_star, alternative, expected
):
    m = request.getfixturevalue(fixture)
    ratio = m.section_biaxial_ratio(N_star, M_x_star, M_y_star, alternative=alternative)
    assert ratio == pytest.approx(expected, rel=1e-3)


def test_section_biaxial_ratio_axial_force_exceeds_capacity(member):
    assert member.section_biaxial_ratio(-700, 1, 1, alternative=True) == math.inf


def test_beam_column_capacities_used_in_hand_calcs(beam_column):
    capacities = dict(M_sx=43.2, M_sy=8.61, M_bx=26.6, N_s=735, N_t=735, N_cx=671, N_cy=131)
    assert {k: getattr(beam_column, k) for k in capacities} == pytest.approx(capacities)


@pytest.mark.parametrize(
    "method, N_star, alternative, expected",
    [
        # Cl 8.4.2.2 general, N_cx with k_e = 0.7
        ("M_ix", -100, False, 36.05),  # 43.2 * (1 - 100 / (0.9 * 671))
        # Cl 8.4.2.2 alternative, N_c = 617.5 with k_e = 1, k = ((1 + 0.5) / 2) ** 3
        ("M_ix", -100, True, 39.96),  # 43.2 * ((1 - k) * c + 1.18 * k * c ** 0.5)
        ("M_ix", -20, True, 43.2),  # 45.19 > M_rx
        ("M_iy", -50, True, 5.303),  # N_cy = 131 as l = l_ey, k = 0.125
        # Cl 8.4.4.1.1
        ("M_ox", -50, False, 15.32),  # 26.6 * (1 - 50 / (0.9 * 131))
        # Cl 8.4.4.1.2, alpha_bc = 2.648, M_box = 20.50 (alpha_m = 1), N_oz = 1327
        ("M_ox", -50, True, 40.32),  # 2.648 * 20.50 * ((1 - 50/117.9) * (1 - 50/1194)) ** 0.5
        ("M_cx", -50, False, 15.32),  # min(M_ix = 39.62, M_ox = 15.32)
        ("M_cx", -50, True, 40.32),  # min(M_ix = 43.2, M_ox = 40.32)
        # tension members, alternative M_r
        ("M_ix", 300, True, 27.86),  # Cl 8.4.2.3, 1.18 * 43.2 * (1 - 300 / (0.9 * 735))
        ("M_iy", 300, True, 8.139),  # Cl 8.4.2.3, 1.19 * 8.61 * (1 - (300 / 661.5) ** 2)
        ("M_ox", 300, False, 23.61),  # Cl 8.4.4.2, 26.6 * (1 + 300 / 661.5) = 38.66 > M_rx
        ("M_ox", 300, True, 27.86),  # Cl 8.4.4.2, 38.66 > alternative M_rx
    ],
)
def test_member_capacities(beam_column, method, N_star, alternative, expected):
    capacity = getattr(beam_column, method)(N_star, alternative)
    assert capacity == pytest.approx(expected, rel=1e-3)


@pytest.mark.parametrize("method", ["M_ix", "M_iy"])
@pytest.mark.parametrize("N_star", [-100, -50, -10])
def test_in_plane_alternative_for_uniform_moment_is_general(ub150, method, N_star):
    m = SteelMember(section=ub150, l=3000, l_ex=3000, l_ey=3000, beta_mx=-1, beta_my=-1)
    capacity = getattr(m, method)
    assert capacity(N_star, alternative=True) == pytest.approx(capacity(N_star), rel=1e-3)


@pytest.mark.parametrize(
    "library, name",
    [
        (MemberLibrary.OpenSections, "610UB101 (GR300)"),  # k_f < 1
        (MemberLibrary.OpenSections, "150PFC (GR300)"),  # not doubly symmetric
        (MemberLibrary.OpenSections, "250UC72.9 (GR300)"),  # not compact
    ],
)
@pytest.mark.parametrize("method", ["M_ix", "M_iy", "M_ox"])
def test_member_alternatives_fall_back_to_general(library, name, method):
    capacity = getattr(_member(library, name, **BEAM_COLUMN), method)
    assert capacity(-100, alternative=True) == capacity(-100)


@pytest.mark.parametrize(
    "library, name, overrides",
    [
        (MemberLibrary.OpenSections, "150UB18.0 (GR300)", dict(transverse_load=True)),
        (MemberLibrary.HollowSections, "125x75x6RHS (C450)", {}),  # I-sections only
    ],
)
def test_M_ox_alternative_falls_back_to_general(library, name, overrides):
    m = _member(library, name, **{**BEAM_COLUMN, **overrides})
    assert m.M_ox(-50, alternative=True) == m.M_ox(-50)


@pytest.mark.parametrize("method, length", [("M_ix", "l"), ("M_iy", "l"), ("M_ox", "l_z")])
def test_member_alternatives_require_length(ub150, method, length):
    m = SteelMember(section=ub150, **{**BEAM_COLUMN, length: 0})
    with pytest.raises(ValueError, match=f"^{length} is required"):
        getattr(m, method)(-50, alternative=True)


@pytest.mark.parametrize(
    "N_star, M_x_star, M_y_star, alternative, expected",
    [
        # (M_x*/phi M_cx)^1.4 + (M_y*/phi M_iy)^1.4
        (-50, 5, 1, False, 0.3649),  # M_cx = 15.32, M_iy = 4.959
        (-50, 5, 1, True, 0.1745),  # M_cx = 40.32, M_iy = 5.303
        # Cl 8.4.5.2 tension, (M_x*/phi M_tx)^1.4 + (M_y*/phi M_ry)^1.4
        (300, 10, 2, True, 0.4386),  # M_tx = 27.86, M_ry = 8.139
    ],
)
def test_member_biaxial_ratio(beam_column, N_star, M_x_star, M_y_star, alternative, expected):
    ratio = beam_column.member_biaxial_ratio(N_star, M_x_star, M_y_star, alternative)
    assert ratio == pytest.approx(expected, rel=1e-3)


def test_member_biaxial_ratio_axial_force_exceeds_capacity(beam_column):
    # N* > phiN_cy = 117.9
    assert beam_column.member_biaxial_ratio(-200, 1, 1) == math.inf

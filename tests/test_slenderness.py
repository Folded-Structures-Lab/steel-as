"""AS4100 Cl 5.2 section slenderness."""

import pytest

from steelas.data.io import MemberLibrary, get_section_from_library
from steelas.member.geometry import SectionGeometry
from steelas.member.material import SteelMaterial
from steelas.member.slenderness import SteelSlenderness


def test_slender_chs_not_implemented():
    params = get_section_from_library(MemberLibrary.HollowSections, "26.9x2.6CHS (C250)")
    # lam_e = 26.9 / 0.1 * 250 / 250 = 269 > lam_ey = 120
    params = {**params, "t": 0.1}
    geom = SectionGeometry.from_dict(**params)
    mat = SteelMaterial.from_dict(**params)
    with pytest.raises(NotImplementedError, match="Slender CHS"):
        SteelSlenderness(geom=geom, mat=mat)

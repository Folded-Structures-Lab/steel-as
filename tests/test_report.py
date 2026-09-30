"""Attribute reporting."""

import pytest

from steelas.data.io import MemberLibrary
from steelas.member.member import SteelMember, SteelSection


@pytest.fixture(scope="module")
def section() -> SteelSection:
    return SteelSection.from_library(MemberLibrary.OpenSections, "150UB18.0 (GR300)")


def test_section_report_lists_attributes(section, capsys):
    section.report()
    out = capsys.readouterr().out
    for heading in ("SectionGeometry", "SteelMaterial", "SteelSlenderness"):
        assert f"{heading} Attributes:" in out
    assert "f_y = 320" in out


def test_member_report_lists_attributes(section, capsys):
    SteelMember(section=section).report()
    assert "phiM_sx = 38.9" in capsys.readouterr().out

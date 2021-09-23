# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""Test the scilab wrapper for GEMSEO."""
from pathlib import Path

import pytest
from gemseo_scilab.py_scilab import ScilabPackage

DIRNAME = Path(__file__).parent / "sci"
DUMMY_FUNCS = ["dummy_func1", "dummy_func2"]


@pytest.mark.parametrize(
    "folder,expected_exception,expected_error_message",
    [
        (
            "toto",
            FileNotFoundError,
            "Script directory for Scilab sources: .* does not exist.",
        ),
        ("no_func", ValueError, "No function name found in .*"),
        ("no_output", ValueError, "Function dummy_func1 has no outputs."),
        ("no_args", ValueError, "Function dummy_func1 has no arguments."),
    ],
)
def test_exceptions(folder, expected_exception, expected_error_message):
    """Test that the proper errors and exceptions are raised.

    Args:
        folder: The specific folder where the `.sci` files are stored.
        expected_exception: The expected exception to be raised.
        expected_error_message: The expected error message to be raised.
    """
    with pytest.raises(
        expected_exception,
        match=expected_error_message,
    ):
        ScilabPackage(DIRNAME / folder)


def test_dummy_funcs():
    """Test the conversion of scilab functions into python functions."""
    package = ScilabPackage(DIRNAME / "dummy_func")
    for func in DUMMY_FUNCS:
        assert func in package.functions
    func1 = package.functions[DUMMY_FUNCS[0]]
    assert func1.name == DUMMY_FUNCS[0]
    assert func1.args == ["b"]
    assert func1.outs == ["a"]

    func2 = package.functions[DUMMY_FUNCS[1]]
    assert func2.name == DUMMY_FUNCS[1]
    assert func2.args == ["d", "e", "f"]

    assert func2.outs == ["a", "b", "c"]
    d, e, f = 1.0, 2.0, 3.0
    a, b, c = func2(d, e, f)

    assert a == 3 * d
    assert b == 5 * d + e
    assert c == 6 * f + 2


def test_str_representation():
    """Test the string representation method of the scilab package."""
    package = ScilabPackage(DIRNAME / "str_rep")

    assert (
        str(package) == "Scilab python interface\nAvailable functions:\n"
        "Auto generated function from scilab.\n\n"
        "    name: dummy_func1\n"
        "    arguments: b\n"
        "    outputs: a\n    "
    )

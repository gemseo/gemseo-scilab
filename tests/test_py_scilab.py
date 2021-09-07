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
"""Missing docstring."""
from os.path import dirname
from os.path import join

from gemseo_scilab.py_scilab import ScilabPackage

DIRNAME = join(dirname(__file__), "sci")
DUMMY_FUNCS = ["dummy_func1", "dummy_func2"]


def test_dummy_funcs():
    """Missing docstring."""
    package = ScilabPackage(DIRNAME)
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

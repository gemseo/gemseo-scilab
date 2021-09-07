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
"""Tests for the scilab discipline."""
from os.path import dirname
from os.path import join

from gemseo_scilab.py_scilab import ScilabPackage
from gemseo_scilab.scilab_discipline import ScilabDiscipline
from numpy import array

DIRNAME = join(dirname(__file__), "sci")


DUMMY_FUNCS = ["dummy_func1", "dummy_func2"]


def exec_disc(fname, in_data):
    """Missing docstring."""
    disc = ScilabDiscipline(fname, DIRNAME)
    disc.execute(in_data)
    return disc.get_output_data()


def test_dummy_funcs():
    """Missing docstring."""
    package = ScilabPackage(DIRNAME)

    for funcid in range(2):
        fname = DUMMY_FUNCS[funcid]
        scilab_func = package.functions[fname]

        data_dict = {k: array([0.2]) for k in scilab_func.args}
        disc_outs = exec_disc(fname, data_dict)

        output_names = scilab_func.outs
        input_values = [0.2 for _ in scilab_func.args]
        scilab_outputs = scilab_func(*input_values)
        if not isinstance(scilab_outputs, tuple):
            output_name = output_names[0]
            output_value = scilab_outputs
            assert output_value == disc_outs[output_name]

        else:
            for output_name, output_value in zip(output_names, scilab_outputs):
                assert output_value == disc_outs[output_name]

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
import logging
import pickle
from pathlib import Path
from typing import Dict
from typing import Mapping

import pytest
from gemseo_scilab.py_scilab import ScilabPackage
from gemseo_scilab.scilab_discipline import ScilabDiscipline
from numpy import array
from numpy import ndarray


DIRNAME = Path(__file__).parent / "sci/dummy_func"


DUMMY_FUNCS = ["dummy_func1", "dummy_func2", "dummy_func3", "dummy_func4"]


def exec_disc(
    fname,  # type: str
    in_data,  # type: Mapping[str, ndarray]
):  # type: (...) -> Dict[str, ndarray]
    """Create and execute a scilab discipline.

    Args:
        fname: The name of the function.
        in_data: The input data.

    Returns:
        The output data from the function execution.
    """
    disc = ScilabDiscipline(fname, DIRNAME)
    disc.execute(in_data)
    return disc.get_output_data()


def test_dummy_funcs():
    """Test the execution of a scilab discipline with dummy functions."""
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


def test_func_not_in_dir():
    """Test that an error is raised when a function is not defined in the given path."""
    fname = DUMMY_FUNCS[2]

    data_dict = {k: array([0.2]) for k in ["toto_1", "toto_2"]}

    with pytest.raises(
        ValueError, match=f"The function named {fname} is not in script_dir .*"
    ):
        exec_disc(fname, data_dict)


def test_pickle(tmp_wd):
    """Test the execution of a ScilabDiscipline in parallel.

    Args:
        tmp_wd: Fixture to move into a temporary work directory.
    """
    disc = ScilabDiscipline("dummy_func1", DIRNAME)
    outf = "outf.pck"
    disc.serialize(outf)
    inputs = {"b": array([1.0])}
    out_ref = disc.execute(inputs)

    disc_load = pickle.load(open(outf, "rb"))
    out = disc_load.execute(inputs)
    assert (out["a"] == out_ref["a"]).all()


def test_func_fail_exec(caplog):
    """Test that an error is raised when a function fails to be executed in scilab.

    Args:
        caplog: Fixture to capture log messages.
    """
    caplog.set_level(logging.ERROR)

    fname = DUMMY_FUNCS[3]

    data_dict = {"b": array([0.0])}

    with pytest.raises(BaseException):
        exec_disc(fname, data_dict)
        assert caplog.text == f"Discipline: {fname} execution failed"


def test_matrix_output():
    """Test the discipline execution if an output is given as an `ndarray`."""
    out = exec_disc("dummy_func5", {"b": [1.0]})
    assert out["a"].all() == array([3.0, 3.0]).all()

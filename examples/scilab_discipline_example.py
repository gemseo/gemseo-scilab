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
from __future__ import annotations

import time
from pathlib import Path

from gemseo import configure_logger
from gemseo.core.grammars.simple_grammar import SimpleGrammar
from gemseo_scilab.scilab import load_scilab_functions
from gemseo_scilab.scilab import start_scilab
from gemseo_scilab.scilab_discipline import ScilabDiscipline
from numpy import array
from numpy import ndarray

LOGGER = configure_logger(level=0)


def main():
    LOGGER.info("Loading sci functions")
    load_scilab_functions("sci")
    LOGGER.info("Create grammars")
    input_grammar = SimpleGrammar(
        "sci inputs", names_to_types={"A": ndarray, "x": float, "i": int}
    )
    output_grammar = SimpleGrammar(
        "sci outputs", names_to_types={"a": float, "b": float, "c": float, "d": float}
    )
    # function  [a,b,c_interface,d,e] = dummy_func_mat_float(A,x)
    LOGGER.info("Creating discipline")
    disc = ScilabDiscipline(
        "dummy_func_mat_float", Path("sci"), input_grammar, output_grammar
    )
    LOGGER.info("execute discipline")

    t0 = time.time()
    n = 10
    for i in range(n):
        out = disc.execute({"A": array([2.0, 3.0, 4.0]), "x": 2.4, "i": i})
        print("Out=", out)
    tf = time.time()
    print("Run time per call ", (tf - t0) / n)


if __name__ == "__main__":
    start_scilab()
    main()

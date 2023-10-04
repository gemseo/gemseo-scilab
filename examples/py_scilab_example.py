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

import numpy
from gemseo_scilab.scilab import *


def main():
    run_command("x_mat=[2,3]")
    run_command("disp(x_mat);")

    load_scilab_functions("sci")
    run_command("out=dummy_eval(2.);")
    create_double_vector("A", numpy.array([2.0, 3.0, 4.0]))

    print("A vector=")
    run_command("disp(A);")

    create_double_matrix("AB", numpy.array([[2.0, 3.0, 4.0], [5.0, 6.0, 7.0]]))
    print("AB matrix=")
    run_command("disp(AB);")

    run_command("[a,b,c_interface]=dummy_func_mat(A);")
    run_command("disp(a,b,c_interface);")

    run_command("B=dummy_func_mat2(A);")

    out = get_double_array("B")
    print("Out in python = ", out)

    create_double("x", 1.2)
    print("x=")
    run_command("disp(x);")

    run_command("xx=2*x;")
    xx = get_double("xx")
    print("xx=", xx)
    try:
        xx = get_double("xxdqf")
    except RuntimeError as err:
        print(err)

    run_command("[xxx]=dummy_eval(x);")
    xxx = get_double("xxx")
    print("xxx= 3x", xxx)

    create_int("i", 3)
    print("i=")
    run_command("disp(i);")
    run_command("ii=2*i;")
    print("Disp ii=")
    run_command("disp(ii);")

    # Still fails
    ii = get_int("ii")
    print("ii=", ii)


if __name__ == "__main__":
    start_scilab()
    main()

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

import atexit
from os import environ
from pathlib import Path
from shutil import which
from typing import Final

from numpy import asfortranarray
from numpy import empty
from numpy import float64
from numpy import ndarray

from gemseo_scilab._scilab import ffi
from gemseo_scilab._scilab import lib

SCILAB_EXECUTABLE_PATH: Final[str | None] = which("scilab")

# Try to figure out the environment variable SCI if possible.
if "SCI" not in environ:
    if SCILAB_EXECUTABLE_PATH is None:
        raise OSError("The environment variable SCI is not set.")
    sci_path = Path(SCILAB_EXECUTABLE_PATH).parent.parent / "share/scilab"
    if not sci_path.is_dir():
        raise OSError("The environment variable SCI is not set.")
    environ["SCI"] = str(sci_path)


def start_scilab(scilab_exe_dir_path: Path | str = "", terminate_at_exit=True) -> None:
    """Starts the Scilab engine. It stays open until closed with terminate_scilab()

    Args:
        scilab_exe_dir_path: The path to the directory that contains the scilab executables.
        terminate_at_exit: Whether to automatically terminate scilab
            at the end of the process.
    """
    if not scilab_exe_dir_path and SCILAB_EXECUTABLE_PATH is not None:
        scilab_exe_dir_path = Path(SCILAB_EXECUTABLE_PATH).parent
    else:
        raise ValueError(
            "The path to the directory that contains the scilab executables cannot be determined."
            " Please set the argument scilab_exe_dir_path."
        )

    lib.DisableInteractiveMode()

    if not lib.StartScilab(str(scilab_exe_dir_path).encode(), ffi.NULL, 0):
        raise RuntimeError("Failed to start scilab.")

    if terminate_at_exit:
        atexit.register(terminate_scilab)


def terminate_scilab() -> None:
    """Terminate scilab."""
    if not lib.TerminateScilab(ffi.NULL):
        raise RuntimeError("Failed to terminate scilab.")


def run_command(command: str) -> None:
    """Run a command in scilab.

    Args:
        command: The command to run.
    """
    err = lib.SendScilabJob(command.encode())
    if err != 0:
        raise RuntimeError(f"Scilab command: {command}, failed with error code: {err}")


def load_scilab_functions(directory_path: Path | str) -> None:
    """Load in Scilab the functions in a directory using the getd method.

    Args:
        directory_path: The path to the directory to load.
    """
    run_command(f"getd('{str(directory_path)}');")


def create_double_vector(name: str, array: ndarray) -> None:
    """Create a named vector of doubles.

    Args:
         name: The name.
         array: The vector.
    """
    assert len(array.shape) == 1
    assert array.dtype == float64

    sciErr = lib.createNamedMatrixOfDouble(
        ffi.NULL, name.encode(), array.size, 1, ffi.from_buffer("double *", array)
    )

    if sciErr.iErr:
        lib.printError(ffi.cast("SciErr *", sciErr), 0)
        raise RuntimeError(f"Failed to create the double vector variable {name}")


def create_double_matrix(name: str, array: ndarray) -> None:
    """Create a named matrix of doubles (2D)

    Args:
         name: The name.
         array: The matrix.
    """
    shape = array.shape
    assert len(shape) == 2
    assert array.dtype == float64

    sciErr = lib.createNamedMatrixOfDouble(
        ffi.NULL,
        name.encode(),
        shape[0],
        shape[1],
        ffi.cast("double *", asfortranarray(array).ctypes.data),
    )

    if sciErr.iErr:
        lib.printError(ffi.cast("SciErr *", sciErr), 0)
        raise RuntimeError(f"Failed to create the double array variable {name}")


def create_double(name: str, value: float) -> None:
    """Create a named double.

    Args:
         name: The name.
         value: The value.
    """
    err = lib.createNamedScalarDouble(ffi.NULL, name.encode(), value)
    if err != 0:
        raise RuntimeError(f"Failed to create the double variable {name}")


def create_int(name: str, value: int) -> None:
    """Create a named integer.

    Args:
         name: The name.
         value: The integer.
    """
    err = lib.createNamedScalarInteger32(ffi.NULL, name.encode(), value)
    if err != 0:
        raise RuntimeError(f"Failed to create the integer variable {name}")


def get_variable_dim(name: str) -> tuple[int, int]:
    """Return the dimensions of a variable.

    Args:
         name: The name.

    Returns:
        The two dimensions.
    """
    n = ffi.new("int *")
    m = ffi.new("int *")
    sciErr = lib.getNamedVarDimension(ffi.NULL, name.encode(), m, n)
    if sciErr.iErr:
        lib.printError(ffi.cast("SciErr *", sciErr), 0)
        raise RuntimeError(f"Failed to get the dimension of the variable {name}")
    return n[0], m[0]


def get_double(name: str) -> float:
    """Return a named double.

    Args:
         name: The name.

    Returns:
         The value.
    """
    value = ffi.new("double *")
    err = lib.getNamedScalarDouble(ffi.NULL, name.encode(), value)
    if err != 0:
        raise RuntimeError(f"Failed to get the value of the variable {name}")
    return value[0]


def get_int(name: str) -> int:
    """Return a named integer.

    Args:
         name: The name.

    Returns:
         The value.
    """
    value = ffi.new("int *")
    err = lib.getNamedScalarInteger32(ffi.NULL, name.encode(), value)
    if err != 0:
        raise RuntimeError(f"Failed to get the value of the variable {name}")
    return value[0]


def get_double_array(name: str) -> ndarray:
    """Return a named matrix of doubles (1D or 2D).

    Args:
         name: The name.

    Returns:
         The array.
    """
    n, m = get_variable_dim(name)

    if m == 1:
        shape = n
    else:
        shape = (n, m)

    array = empty(shape, dtype=float64)

    sciErr = lib.readNamedMatrixOfDouble(
        ffi.NULL,
        name.encode(),
        ffi.new("int *", n),
        ffi.new("int *", m),
        ffi.from_buffer("double *", array),
    )

    if sciErr.iErr:
        lib.printError(ffi.cast("SciErr *", sciErr), 0)
        raise RuntimeError(f"Failed to get the value of the variable {name}")

    return array

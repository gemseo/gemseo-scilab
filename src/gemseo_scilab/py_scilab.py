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
"""Scilab wrapper."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Final

from scilab2py import scilab

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy import ndarray

LOGGER = logging.getLogger(__name__)


class ScilabFunction:
    """A scilab function."""

    _f_pointer: Callable | None
    _fun_def: str
    name: str
    args: Sequence[str]
    outs: Sequence[str]

    def __init__(
        self,
        fun_def: str,
        name: str,
        args: Sequence[str],
        outs: Sequence[str],
    ) -> None:
        """Constructor.

        Args:
            fun_def: The definition of the function.
            name: The name of the function.
            args: The arguments of the function.
            outs: The outputs of the function.
        """
        self._f_pointer = None
        self._fun_def = fun_def
        self.name = name
        self.args = args
        self.outs = outs

        self.__init_from_def()

    def __call__(  # noqa: D102
        self, *args: Any, **kwargs: Any
    ) -> dict[str, float | ndarray]:
        return self._f_pointer(*args, **kwargs)

    def __init_from_def(self) -> None:
        """Initialize the function from its definition."""
        exec(self._fun_def)
        self._f_pointer = locals()[self.name]

    def __getstate__(self) -> dict[str, Any]:
        out_dict = self.__dict__.copy()
        del out_dict["_f_pointer"]
        return out_dict

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self._f_pointer = None
        self.__init_from_def()


class ScilabPackage:
    """Interface to a scilab package.

    Scilab python interface scans the sci files in a directory and generates python
    functions from them.
    """

    RE_OUTS: Final[re.Pattern] = re.compile(r"\[([^$].*?)]")
    RE_FUNC: Final[re.Pattern] = re.compile(r"=([^$].*?)\(")
    RE_ARGS: Final[re.Pattern] = re.compile(r"\(([^$].*?)\)")

    def __init__(self, script_dir_path: str | Path) -> None:
        """Constructor.

        Args:
            script_dir_path: The path to the directory to scan for .sci files.

        Raises:
            FileNotFoundError: If the `script_dir_path` does not exist.
        """
        script_dir_path = Path(script_dir_path)
        if not script_dir_path.is_dir():
            raise FileNotFoundError(
                f"Script directory for Scilab sources: {script_dir_path}"
                " does not exist."
            )

        # scilab.timeout = 10
        LOGGER.info("Using the scilab script directory: %s", script_dir_path)

        scilab.getd(str(script_dir_path))
        self.functions = {}
        self.__scan_funcs(script_dir_path)

    def __scan_onef(self, line: str) -> None:
        """Scan a function in a sci file to parse its arguments, outputs and name.

        Args:
            line: The line from the sci file to scan.

        Raises:
            ValueError: If no function is found in `line`.
                If the function has no outputs. If the function has no arguments.
        """
        line = line.replace(" ", "")
        match_groups = self.RE_FUNC.search(line)
        if match_groups is None:
            raise ValueError(f"No function name found in {line}")

        fname = match_groups.group(0).strip()[1:-1].strip()
        LOGGER.debug("Detected function: %s", fname)

        match_groups = self.RE_OUTS.search(line)
        if match_groups is None:
            raise ValueError(f"Function {fname} has no outputs.")

        argstr = match_groups.group(0).strip()
        argstr = argstr.replace("[", "").replace("]", "")
        outs = argstr.split(",")
        fouts = [out_str.strip() for out_str in outs]

        LOGGER.debug("Outputs are: %s", outs)

        match_groups = self.RE_ARGS.search(line)
        if match_groups is None:
            raise ValueError(f"Function {fname} has no arguments.")

        argstr = match_groups.group(0).strip()[1:-1].strip()
        args = argstr.split(",")
        fargs = [args_str.strip() for args_str in args]
        LOGGER.debug("And arguments are: %s", args)

        args_form = ", ".join(fargs)
        outs_form = ", ".join(fouts)
        fun_def = f"""
def {fname}({args_form}):
    '''Auto generated function from scilab.

    name: {fname}
    arguments: {args_form}
    outputs: {outs_form}
    '''
    {outs_form} = scilab.{fname}({args_form})
    return {outs_form}
"""
        self.functions[fname] = ScilabFunction(fun_def, fname, fargs, fouts)

    def __scan_funcs(self, script_dir_path: Path) -> None:
        """Scan all functions in the directory.

        Raises:
            ValueError: If an interface cannot be generated for a function.
        """
        for script_f in script_dir_path.glob("*.sci"):
            LOGGER.info("Found script file: %s", script_f)

            with Path(script_f).open() as script:
                for line in script.readlines():
                    if not line.strip().startswith("function"):
                        continue

                    try:
                        self.__scan_onef(line)
                    except ValueError:
                        LOGGER.exception(
                            "Cannot generate interface for function %s", line
                        )
                        raise

    def __str__(self) -> str:
        sout = "Scilab python interface\nAvailable functions:\n"
        for function in self.functions.values():
            sout += function._f_pointer.__doc__
        return sout

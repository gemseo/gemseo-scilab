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
import logging
import re
from glob import glob
from os.path import exists
from os.path import join

from scilab2py import scilab

LOGGER = logging.getLogger(__name__)


class ScilabFunction:
    """A scilab function."""

    def __init__(self, f_pointer, name, args, outs) -> None:
        """# noqa: D205, D212, D415
        Args:
            f_pointer:
            name:
            args:
            outs:
        """
        self.f_pointer = f_pointer
        self.name = name
        self.args = args
        self.outs = outs

    def __call__(self, *args, **kwargs):
        """Call the scilab function."""
        return self.f_pointer(*args, **kwargs)


class ScilabPackage:
    """Interface to a scilab package.

    Scilab python interface Scans the sci files in a directory and generates python
    functions from them.
    """

    RE_OUTS = re.compile(r"\[(.*?)]")
    RE_FUNC = re.compile(r"=(.*?)\(")
    RE_ARGS = re.compile(r"\((.*?)\)")

    def __init__(self, script_dir_path: str) -> None:
        """# noqa: D205, D212, D415
        Args:
            script_dir_path : The path to the directory to scan for .sci files.
        """
        if not exists(script_dir_path):
            raise FileNotFoundError(
                f"Script directory for Scilab sources: {script_dir_path}"
                " does not exists."
            )

        # scilab.timeout = 10
        LOGGER.info("Use scilab script directory: %s", script_dir_path)

        self.__script_dir_path = script_dir_path
        scilab.getd(script_dir_path)
        self.functions = {}
        self.__scan_funcs()

    def __scan_onef(self, line: str) -> None:
        """Scans a function in a sci file to parse arguments, outputs and name.

        @param line : the string containing the function
        """
        match_groups = self.RE_FUNC.search(line)
        if match_groups is None:
            raise Exception(f"No function name found in {line}")

        fname = match_groups.group(0).strip()[1:-1].strip()
        LOGGER.debug("Detected function: %s", fname)

        match_groups = self.RE_OUTS.search(line)
        if match_groups is None:
            raise Exception(f"Function {fname} has no outputs.")

        argstr = match_groups.group(0).strip()
        argstr = argstr.replace("[", "").replace("]", "")
        outs = argstr.split(",")
        fouts = [out_str.strip() for out_str in outs]

        LOGGER.debug("Outputs are: %s", outs)

        match_groups = self.RE_ARGS.search(line)
        if match_groups is None:
            raise Exception("Function has no arguments.")

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

        exec(fun_def)

        wrapped_func = locals()[fname]
        setattr(self, fname, wrapped_func)
        self.functions[fname] = ScilabFunction(wrapped_func, fname, fargs, fouts)

    def __scan_funcs(self) -> None:
        """Scans all functions in the directory."""
        for script_f in glob(join(self.__script_dir_path, "*.sci")):
            LOGGER.info("Found script file: %s", script_f)

            with open(script_f) as script:
                for line in script.readlines():
                    if not line.strip().startswith("function"):
                        continue

                    try:
                        self.__scan_onef(line)
                    except BaseException:
                        LOGGER.error("Cannot generate interface for function %s", line)
                        raise

    def __str__(self) -> str:
        sout = "Scilab python interface\nAvailable functions:\n"
        for function in self.functions.values():
            sout += function.func.__doc__
        return sout

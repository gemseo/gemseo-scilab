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
# Author: Francois Gallard
"""Scilab discipline."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Final

from gemseo.core.discipline import MDODiscipline
from gemseo.core.grammars.base_grammar import BaseGrammar
from gemseo.core.grammars.json_grammar import JSONGrammar
from gemseo.core.grammars.simple_grammar import SimpleGrammar
from numpy import ndarray

from gemseo_scilab.scilab import create_double
from gemseo_scilab.scilab import create_double_matrix
from gemseo_scilab.scilab import create_double_vector
from gemseo_scilab.scilab import create_int
from gemseo_scilab.scilab import get_double
from gemseo_scilab.scilab import get_double_array
from gemseo_scilab.scilab import get_int
from gemseo_scilab.scilab import run_command

LOGGER = logging.getLogger(__file__)


class ScilabDiscipline(MDODiscipline):
    """Base wrapper for OCCAM problem discipline wrappers and SimpleGrammar."""

    RE_OUTS: Final[re.Pattern] = re.compile(r"\[([^$].*?)]")
    RE_FUNC: Final[re.Pattern] = re.compile(r"=([^$].*?)\(")
    RE_ARGS: Final[re.Pattern] = re.compile(r"\(([^$].*?)\)")

    def __init__(
        self,
        function_name: str,
        script_dir_path: str,
        input_grammar: BaseGrammar,
        output_grammar: BaseGrammar,
    ) -> None:
        """Constructor.

        Args:
            function_name: The name of the scilab function to
                generate the discipline from.
            script_dir_path: The path to the directory to scan for `.sci` files.

        Raises:
            ValueError: If the function is not in any of the files of
                the `script_dir_path`.
        """
        if isinstance(input_grammar, SimpleGrammar):
            grammar_type = MDODiscipline.GrammarType.SIMPLE
        elif isinstance(input_grammar, JSONGrammar):
            grammar_type = MDODiscipline.GrammarType.JSON
        super().__init__(
            name=function_name,
            auto_detect_grammar_files=False,
            grammar_type=grammar_type,
        )
        self.__functions = {}
        self.input_grammar = input_grammar
        self.output_grammar = output_grammar
        self.__simple_input_grammar = input_grammar.to_simple_grammar()
        self.__simple_output_grammar = output_grammar.to_simple_grammar()

        LOGGER.debug("Scanning scilab functions directory: %s", script_dir_path)
        self.__scan_funcs(script_dir_path)
        self._function_name = function_name
        self._f_args, self._f_outs = self.__functions[self._function_name]
        self._check_grammars()

        self._create_run_command()

        LOGGER.debug("Scilab discipline run command : %s", self._run_command)

    def _create_run_command(self):
        self._run_command = "{} = {}{}".format(
            self._f_outs, self._function_name, tuple(self._f_args)
        )
        self._run_command = self._run_command.replace("'", "")

    def _check_grammars(self):
        s_input_grammar = sorted(self.input_grammar.names)
        s_fargs = sorted(self._f_args)
        if s_input_grammar != s_fargs:
            msg = (
                "Inconsistent scilab function inputs: {} "
                ", and input grammar element names: {}"
            )
            raise ValueError(msg.format(s_fargs, s_input_grammar))

        s_output_grammar = sorted(self.output_grammar.names)
        s_f_outs = sorted(self._f_outs)
        if s_output_grammar != s_f_outs:
            msg = (
                "Inconsistent scilab function outputs: {} "
                ", and output grammar element names: {}"
            )
            raise ValueError(msg.format(s_f_outs, s_output_grammar))

    def _run(self) -> None:
        grammar = self.__simple_input_grammar
        LOGGER.debug("Writing inputs to scilab env")
        for name in grammar.names:
            value = self.local_data[name]
            data_type = grammar._SimpleGrammar__names_to_types[name]
            LOGGER.debug("Writing input:%s = %s of type %s", name, value, data_type)
            if data_type == int:
                create_int(name, value)
            elif data_type == float:
                create_double(name, value)
            elif data_type == ndarray:
                shape = value.shape
                if len(shape) == 1:
                    create_double_vector(name, value)
                elif len(shape) == 2:
                    create_double_matrix(name, value)
                else:
                    raise RuntimeError(f"Unsupported shape {shape} ")
            else:
                raise TypeError(f"Unsupported data type {type(value)} ")

        LOGGER.debug("Running scilab command %s", self._run_command)
        run_command(self._run_command)

        LOGGER.debug("Reading outputs from scilab env")
        grammar = self.__simple_output_grammar
        for name in grammar.names:
            data_type = grammar._SimpleGrammar__names_to_types[name]
            LOGGER.debug("Reading output:%s of type: %s", name, data_type)
            if data_type == int:
                value = get_int(name)
            elif data_type == float:
                value = get_double(name)
            elif data_type == ndarray:
                value = get_double_array(name)
            else:
                raise TypeError(f"Unsupported data type {data_type} ")

            self.local_data[name] = value
            LOGGER.debug("Got value: %s", value)

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

        self.__functions[fname] = (fargs, fouts)

    def __scan_funcs(self, script_dir_path: Path) -> None:
        """Scan all functions in the directory.

        Raises:
            ValueError: If an interface cannot be generated for a function.
        """
        for script_f in script_dir_path.glob("*.sci"):
            LOGGER.debug("Found script file: %s", script_f)
            with open(script_f) as script:
                for line in script.readlines():
                    if not line.strip().startswith("function"):
                        continue
                    try:
                        self.__scan_onef(line)
                    except ValueError:
                        LOGGER.error("Cannot generate interface for function %s", line)
                        raise

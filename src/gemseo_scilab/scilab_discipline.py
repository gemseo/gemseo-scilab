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
"""Scilab discipline."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from gemseo.core.discipline.data_processor import DataProcessor
from gemseo.core.discipline.discipline import Discipline
from numpy import array
from numpy import ndarray

from gemseo_scilab.py_scilab import ScilabPackage

if TYPE_CHECKING:
    from gemseo.typing import MutableStrKeyMapping
    from gemseo.typing import StrKeyMapping

    from gemseo_scilab.py_scilab import ScilabFunction

LOGGER = logging.getLogger(__name__)


class ScilabDiscipline(Discipline):
    """Base wrapper for OCCAM problem discipline wrappers and SimpleGrammar."""

    def __init__(
        self,
        function_name: str,
        script_dir_path: str,
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
        self.__scilab_package = ScilabPackage(script_dir_path)

        if function_name not in self.__scilab_package.functions:
            msg = (
                f"The function named {function_name}"
                f" is not in script_dir {script_dir_path}"
            )
            raise ValueError(msg)

        self._scilab_function = self.__scilab_package.functions[function_name]

        super().__init__(name=function_name)

        self.io.input_grammar.update_from_names(self._scilab_function.args)
        self.io.output_grammar.update_from_names(self._scilab_function.outs)
        self.io.data_processor = ScilabDataProcessor(self._scilab_function)

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping | None:
        """Run the discipline.

        Raises:
            BaseException: If the discipline execution fails.
        """
        try:
            output_data = self._scilab_function(**input_data)
        except BaseException:
            LOGGER.exception("Discipline: %s execution failed", self.name)
            raise

        out_names = self._scilab_function.outs

        if len(out_names) == 1:
            return {out_names[0]: output_data}
        return dict(zip(out_names, output_data, strict=False))


class ScilabDataProcessor(DataProcessor):
    """A scilab function data processor."""

    def __init__(self, scilab_function: ScilabFunction) -> None:
        """Constructor.

        Args:
            scilab_function: The scilab function.
        """
        super().__init__()
        self.__scilab_function = scilab_function

    def pre_process_data(self, data: StrKeyMapping) -> MutableStrKeyMapping:  # noqa: D102
        return dict(data)

    def post_process_data(self, data: StrKeyMapping) -> MutableStrKeyMapping:  # noqa: D102
        processed_data = dict(data)
        for data_name in self.__scilab_function.outs:
            val = processed_data[data_name]

            if isinstance(val, ndarray):
                processed_data[data_name] = val.flatten()
            else:
                processed_data[data_name] = array([val])

        return processed_data

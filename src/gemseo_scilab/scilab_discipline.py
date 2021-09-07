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
import logging
from typing import Mapping
from typing import Union

import numpy as np
from gemseo.core.data_processor import DataProcessor
from gemseo.core.discipline import MDODiscipline
from gemseo_scilab.py_scilab import ScilabFunction
from gemseo_scilab.py_scilab import ScilabPackage

LOGGER = logging.getLogger(__name__)


class ScilabDiscipline(MDODiscipline):
    """Base wrapper for OCCAM problem discipline wrappers and SimpleGrammar."""

    def __init__(self, function_name: str, script_dir_path: str) -> None:
        """Constructor.

        @param function_name : the name of the scilab function to
                                generate the discipline from
        @param script_dir_path : directory to scan for .sci files
        """
        super().__init__(
            name=function_name,
            auto_detect_grammar_files=False,
            grammar_type=MDODiscipline.JSON_GRAMMAR_TYPE,
        )
        self.__scilab_package = ScilabPackage(script_dir_path)

        if function_name not in self.__scilab_package.functions:
            raise ValueError(
                f"The function named {function_name} "
                f" is not in script_dir {script_dir_path}"
            )

        self.__scilab_function = self.__scilab_package.functions[function_name]

        self.input_grammar.initialize_from_base_dict(self.__base_input_data)
        self.output_grammar.initialize_from_base_dict(self.__base_output_data)
        self.data_processor = ScilabDataProcessor(self.__scilab_function)

    def _run(self) -> None:
        """Run the discipline."""
        input_data = self.get_input_data()

        try:
            output_data = self.__scilab_function(**input_data)
        except BaseException:
            LOGGER.error("Discipline: %s execution failed", self.name)
            raise

        out_names = self.__scilab_function.outs

        if len(out_names) == 1:
            self.store_local_data(**{out_names[0]: output_data})
        else:
            for out_n, out_v in zip(out_names, output_data):
                self.store_local_data(**{out_n: out_v})

    @property
    def __base_input_data(self):
        def_data = [0.1]
        return {k: def_data for k in self.__scilab_function.args}

    @property
    def __base_output_data(self):
        def_data = [0.1]
        return {k: def_data for k in self.__scilab_function.outs}


class ScilabDataProcessor(DataProcessor):
    """A scilab function data processor."""

    def __init__(self, scilab_function: ScilabFunction) -> None:
        """# noqa: D205, D212, D415
        Args:
            scilab_function: The scilab function.
        """
        super().__init__()
        self.__scilab_function = scilab_function

    def pre_process_data(self, input_data: np.ndarray):
        """Convert GEMSEO input data for scilab.

        @param input_data : the input data dict
        """
        processed_data = input_data.copy()
        for data_name in self.__scilab_function.args:
            processed_data[data_name] = processed_data[data_name]
        return processed_data

    def post_process_data(self, local_data: Mapping[str, Union[float, np.ndarray]]):
        """Convert output data from scilab for GEMSEO.

        @param local_data : the local data of self
        """
        processed_data = dict(local_data)
        for data_name in self.__scilab_function.outs:
            val = processed_data[data_name]
            if not isinstance(val, np.ndarray):
                processed_data[data_name] = np.array([val])
        return processed_data

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
from typing import Dict
from typing import List
from typing import Mapping
from typing import Union

from gemseo.core.data_processor import DataProcessor
from gemseo.core.discipline import MDODiscipline
from gemseo_scilab.py_scilab import ScilabFunction
from gemseo_scilab.py_scilab import ScilabPackage
from numpy import array
from numpy import ndarray

LOGGER = logging.getLogger(__name__)


class ScilabDiscipline(MDODiscipline):
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
        super().__init__(
            name=function_name,
            auto_detect_grammar_files=False,
            grammar_type=MDODiscipline.JSON_GRAMMAR_TYPE,
        )
        self.__scilab_package = ScilabPackage(script_dir_path)

        if function_name not in self.__scilab_package.functions:
            raise ValueError(
                f"The function named {function_name}"
                f" is not in script_dir {script_dir_path}"
            )

        self._scilab_function = self.__scilab_package.functions[function_name]

        self.input_grammar.initialize_from_base_dict(self.__base_input_data)
        self.output_grammar.initialize_from_base_dict(self.__base_output_data)
        self.data_processor = ScilabDataProcessor(self._scilab_function)

    def _run(self) -> None:
        """Run the discipline.

        Raises:
            BaseException: If the discipline execution fails.
        """
        input_data = self.get_input_data()

        try:
            output_data = self._scilab_function(**input_data)
        except BaseException:
            LOGGER.error("Discipline: %s execution failed", self.name)
            raise

        out_names = self._scilab_function.outs

        if len(out_names) == 1:
            self.store_local_data(**{out_names[0]: output_data})
        else:
            for out_n, out_v in zip(out_names, output_data):
                self.store_local_data(**{out_n: out_v})

    @property
    def __base_input_data(self) -> Dict[str, Union[float, ndarray]]:
        """The data to initialize the inputs."""
        def_data = [0.1]
        return {k: def_data for k in self._scilab_function.args}

    @property
    def __base_output_data(self) -> Dict[str, Union[float, ndarray]]:
        """The data to initialize the outputs."""
        def_data = [0.1]
        return {k: def_data for k in self._scilab_function.outs}

    def get_attributes_to_serialize(self) -> List[str]:
        """Define the attributes to be serialized.

        Returns:
            The attributes names.
        """
        attrs = super().get_attributes_to_serialize()
        attrs.append("_scilab_function")
        return attrs


class ScilabDataProcessor(DataProcessor):
    """A scilab function data processor."""

    def __init__(self, scilab_function: ScilabFunction) -> None:
        """Constructor.

        Args:
            scilab_function: The scilab function.
        """
        super().__init__()
        self._scilab_function = scilab_function

    def pre_process_data(
        self, input_data: Mapping[str, ndarray]
    ) -> Dict[str, Union[float, ndarray]]:
        """Convert the input from GEMSEO to scilab.

        Args:
            input_data: The input data.

        Returns:
            The data to be passed to scilab.
        """
        processed_data = input_data.copy()
        for data_name in self._scilab_function.args:
            processed_data[data_name] = processed_data[data_name]
        return processed_data

    def post_process_data(
        self, local_data: Mapping[str, Union[float, ndarray]]
    ) -> Dict[str, ndarray]:
        """Convert the output data from scilab to GEMSEO.

        Args:
            local_data : The data obtained after executing scilab.

        Returns:
            The processed data to be given to GEMSEO.
        """
        processed_data = dict(local_data)
        for data_name in self._scilab_function.outs:
            val = processed_data[data_name]

            if isinstance(val, ndarray):
                processed_data[data_name] = val.flatten()
            else:
                processed_data[data_name] = array([val])

        return processed_data

# -*-mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8 -*-
'''
 * Copyright (c) {2015} {IRT-AESE}.
 * All rights reserved.
 *
 * Contributors:
 *    {INITIAL AUTHORS} - initial API and implementation and/or initial
 *                        documentation
 *        @author: François Gallard
 *    {OTHER AUTHORS}   - {MACROSCOPIC CHANGES}
'''
from gemseo.core.discipline import MDODiscipline
from gemseo_scilab.py_scilab import ScilabPackage
import numpy as np
import logging
from gemseo.core.data_processor import DataProcessor
LOGGER = logging.getLogger()


class ScilabDiscipline(MDODiscipline):
    '''
    Base wrapper for OCCAM problem discipline wrappers and SimpleGrammar
    '''

    def __init__(self, function_name, script_dir):
        '''
        Constructor
        @param function_name : the name of the scilab function to
                                generate the discipline from
        @param script_dir : directory to scan for .sci files
        '''
        super(ScilabDiscipline, self).__init__(
            name=function_name,
            auto_detect_grammar_files=False,
            grammar_type=MDODiscipline.JSON_GRAMMAR_TYPE)
        self.sci_package = ScilabPackage(script_dir)
        if function_name not in self.sci_package.functions:
            raise Exception("Function : {} has not beed detected in script_dir {}" .format(
                            function_name, script_dir))
        self.scilab_func = self.sci_package.functions[function_name]
        self.input_grammar.initialize_from_base_dict(
            self._get_in_basedict())
        self.output_grammar.initialize_from_base_dict(
            self._get_out_basedict())
        self.data_processor = ScilabDataProcessor(self.scilab_func)
        return

    def _run(self):
        """
        Run the discipline
        """
        input_vals = self.get_input_data()
        try:
            out_vals = self.scilab_func(**input_vals)
        except:
            LOGGER.error("Discipline : " + str(self.name) +
                         " execution failed")
            raise

        out_names = self.scilab_func.outs
        if len(out_names) == 1:
            self.store_local_data(**{out_names[0]: out_vals})
        else:
            for out_n, out_v in zip(out_names, out_vals):
                self.store_local_data(**{out_n: out_v})
        return

    def _get_in_basedict(self):
        def_data = [0.1]
        return {k: def_data for k in self.scilab_func.args}

    def _get_out_basedict(self):
        def_data = [0.1]
        return {k: def_data for k in self.scilab_func.outs}


class ScilabDataProcessor(DataProcessor):
    """
    A scilab func data processor
    """

    def __init__(self, scilab_function):
        super(ScilabDataProcessor, self).__init__()
        self.scilab_function = scilab_function
        self.sci_args = self.scilab_function.args
        self.sci_outs = self.scilab_function.outs

    def pre_process_data(self, input_data):
        """
        Parses the data from gems (ndarrays) and makes floats for scilab
        @param input_data : the input data dict
        """
        processed_data = input_data.copy()
        for dname in self.sci_args:
            processed_data[dname] = processed_data[dname]
        return processed_data

    def post_process_data(self, local_data):
        """
        Parses the outptu data from scilab (floats) and makes ndarrays from
        them for GEMS
        @param local_data : the local data of self
        """
        processed_data = local_data.copy()
        for dname in self.sci_outs:
            val = processed_data[dname]
            if not isinstance(val, np.ndarray):
                processed_data[dname] = np.array([val])
            else:
                processed_data[dname] = val
        return processed_data

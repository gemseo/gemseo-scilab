# -*-mode: python; py-indent-offset: 4; tab-width: 8; coding:utf-8 -*-
'''
 * Copyright (c) {2015} {IRT-AESE}.
 * All rights reserved.
 *
 * Contributors:
 *    {INITIAL AUTHORS} - initial API and implementation and/or initial documentation
 *        @author: François Gallard
 *    {OTHER AUTHORS}   - {MACROSCOPIC CHANGES}
'''
from gemseo_scilab.scilab_discipline import ScilabDiscipline
from gemseo_scilab.py_scilab import ScilabPackage
import unittest
from os.path import dirname, join
from numpy import array
from gemseo.api import configure_logger

configure_logger("gemseo")

class Test_ScilabDiscipline(unittest.TestCase):

    DUMMY_FUNCS = ["dummy_func1", "dummy_func2"]

    def setUp(self):
        self.DIRNAME = join(dirname(__file__), "sci")

    def exec_disc(self, fname, in_data):
        disc = ScilabDiscipline(fname, self.DIRNAME)
        disc.execute(in_data)
        return disc.get_output_data()

    def test_dummy_funcs(self):
        package = ScilabPackage(self.DIRNAME)

        for funcid in range(2):
            fname = self.DUMMY_FUNCS[funcid]
            scilab_func = package.functions[fname]
            print("Checking discipline ", fname)

            data_dict = {k: array([0.2]) for k in scilab_func.args}
            disc_outs = self.exec_disc(fname, data_dict)

            output_names = scilab_func.outs
            inpts_val = [0.2 for k in scilab_func.args]
            scilab_outputs = scilab_func(*inpts_val)
            if not isinstance(scilab_outputs, tuple):
                outname = output_names[0]
                outval = scilab_outputs
                print("Checking output :", outname, outval)
                self.assertEqual(outval, disc_outs[outname])

            else:
                for outname, outval in zip(output_names, scilab_outputs):
                    print("Checking output :", outname, outval)
                    self.assertEqual(outval, disc_outs[outname])

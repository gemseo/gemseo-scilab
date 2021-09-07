# -*-mode: python; py-indent-offset: 4; tab-width: 8; coding:utf-8 -*-
'''
 * Copyright (c) {201.5} {IRT-AESE}.
 * All rights reserved.
 *
 * Contributors:
 *    {INITIAL AUTHORS} - initial API and implementation and/or initial
 *                            documentation
 *        @author: François Gallard
 *    {OTHER AUTHORS}   - {MACROSCOPIC CHANGES}
'''
from scilab2py import scilab
from os.path import join, exists
import re
from glob import glob
import logging
LOGGER = logging.getLogger()


class ScilabFunction(object):
    """
    A scilab function
    """

    def __init__(self, f_pointer, name, args, outs):
        self.f_pointer = f_pointer
        self.name = name
        self.args = args
        self.outs = outs

    def __call__(self, *args, **kwargs):
        return self.f_pointer(*args, **kwargs)


class ScilabPackage(object):
    """
    Scilab python interface
    Scans the sci files in a directory and generates python functions from them
    It is a singleton to avoid multiple scanning
    """
    FUNC_NAME = "fname"
    FUNC_ARGS = "fargs"
    FUNC_OUTS = "fouts"
    FUNC_EXEC = "exec"
    RE_OUTS = re.compile(r"\[(.*?)\]")
    RE_FUNC = re.compile(r"=(.*?)\(")
    RE_ARGS = re.compile(r"\((.*?)\)")

    def __init__(self, script_dir):
        """
        Constructor :
        @param script_dir : directory to scan for .sci files
        """
        if not exists(script_dir):
            raise Exception("Script directory for Scilab sources : " +
                            str(script_dir) + " does not exists !")
        #scilab.timeout = 10
        LOGGER.info("Use scilab script directory : " + str(script_dir))
        self.script_dir = script_dir
        scilab.getd(script_dir)
        self.functions = {}
        self.__scan_funcs()

    def __scan_onef(self, line):
        """
        Scans a function in a sci file to parse arguments, outputs and name
        @param line : the string containing the function
        """
        grps = self.RE_FUNC.search(line)
        if grps is not None:
            fname = grps.group(0).strip()[1:-1].strip()
            LOGGER.debug("Detected function: " + str(fname))
        else:
            raise Exception("Function has no name !")

        grps = self.RE_OUTS.search(line)
        if grps is not None:
            argstr = grps.group(0).strip()
            argstr = argstr.replace("[", "").replace("]", "")
            outs = argstr.split(",")
            fouts = [out_str.strip() for out_str in outs]
            LOGGER.debug("Outputs are : " + str(outs))
        else:
            raise Exception("Function " + fname + " has no ouptuts !")

        grps = self.RE_ARGS.search(line)
        if grps is not None:
            argstr = grps.group(0).strip()[1:-1].strip()
            args = argstr.split(",")
            fargs = [args_str.strip() for args_str in args]
            LOGGER.debug("And arguments are : " + str(args))
        else:
            raise Exception("Function has no arguments !")
        args_form = ', '.join(fargs)
        outs_form = ", ".join(fouts)
        docstr = "name : %s\narguments : %s \noutputs : %s" % (
            fname, args_form, outs_form)

        fun_def = """
def %s(%s):
    '''
Auto generated function from scilab
%s
    '''
    %s = scilab.%s(%s)
    return %s
self.%s=%s
self.functions['%s']=ScilabFunction(%s,'%s', %s, %s)
""" % (fname, args_form, docstr, outs_form, fname,
            args_form, outs_form, fname, fname, fname, fname,
            fname, fargs, fouts)

        exec(fun_def)
        return

    def __scan_funcs(self):
        """
        Scans all functions in the directory
        """
        for script_f in glob(join(self.script_dir, "*.sci")):
            LOGGER.info("Found script file : " + str(script_f))
            with open(script_f, "r") as script:
                for line in script.readlines():
                    if line.strip().startswith("function"):
                        try:
                            self.__scan_onef(line)
                        except:
                            LOGGER.error(
                                "Cannot generate interface for function " +
                                line)
                            raise
        return

    def __str__(self):
        sout = "Scilab python interface\n"
        sout += "Available functions : \n"
        for function in list(self.functions.values()):
            sout += function.func.__doc__
        return sout

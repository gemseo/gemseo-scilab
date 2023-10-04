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

from os import environ
from pathlib import Path
from shutil import which

from cffi import FFI

scilab_executable_path = which("scilab")

if scilab_executable_path:
    path = Path(scilab_executable_path)
    SCILAB_LIBRARY_DIR = str(path.parent.parent / "lib/scilab")
    SCILAB_INCLUDE_DIR = str(path.parent.parent / "include/scilab")
else:
    SCILAB_LIBRARY_DIR = environ.get("SCILAB_LIBRARY_DIR")
    if not SCILAB_LIBRARY_DIR:
        raise ValueError(
            "Missing environment variable SCILAB_LIBRARY_DIR "
            "pointing to the directory that contains the libraries scilab-cli and scicall_scilab."
        )
    SCILAB_INCLUDE_DIR = environ.get("SCILAB_INCLUDE_DIR")
    if not SCILAB_INCLUDE_DIR:
        raise ValueError(
            "Missing environment variable SCILAB_INCLUDE_DIR "
            "pointing to the directory that contains the headers call_scilab.h and api_scilab.h."
        )

ffibuilder = FFI()

ffibuilder.cdef(
    """
#define MESSAGE_STACK_SIZE 5
typedef struct api_Err
{
    int iErr;
    int iMsgCount;
    char* pstMsg[MESSAGE_STACK_SIZE];
} SciErr;
void DisableInteractiveMode(void);
bool StartScilab(char *SCIpath, char *ScilabStartup, int Stacksize);
int SendScilabJob(char *job);
bool TerminateScilab(char *ScilabQuit);
SciErr createNamedMatrixOfDouble(void* _pvCtx, const char* _pstName, int _iRows, int _iCols, const double* _pdblReal);
int printError(SciErr* _psciErr, int _iLastMsg);
int createNamedScalarDouble(void* _pvCtx, const char* _pstName, double _dblReal);
int createNamedScalarInteger32(void* _pvCtx, const char* _pstName, int _iData);
SciErr getNamedVarDimension(void* _pvCtx, const char *_pstName, int* _piRows, int* _piCols);
SciErr readNamedMatrixOfDouble(void* _pvCtx, const char* _pstName, int* _piRows, int* _piCols, double* _pdblReal);
int getNamedScalarDouble(void* _pvCtx, const char* _pstName, double* _pdblReal);
int getNamedScalarInteger32(void* _pvCtx, const char* _pstName, int* _piData);
"""
)

ffibuilder.set_source(
    "gemseo_scilab._scilab",
    """
#include "call_scilab.h"
#include "api_scilab.h"
""",
    include_dirs=[SCILAB_INCLUDE_DIR],
    library_dirs=[SCILAB_LIBRARY_DIR],
    libraries=["scilab-cli", "scicall_scilab"],
    extra_link_args=[f"-Wl,-rpath={SCILAB_LIBRARY_DIR}"],
)

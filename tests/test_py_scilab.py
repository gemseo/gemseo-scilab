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

from gemseo_scilab.py_scilab import ScilabPackage
from os.path import dirname, join

DIRNAME = join(dirname(__file__), "sci")
DUMMY_FUNCS = ["dummy_func1", "dummy_func2"]


def test_dummy_funcs():
    package = ScilabPackage(DIRNAME)
    for func in DUMMY_FUNCS:
        assert func in package.functions
    func1 = package.functions[DUMMY_FUNCS[0]]
    assert func1.name == DUMMY_FUNCS[0]
    assert func1.args == ["b"]
    assert func1.outs == ["a"]

    func2 = package.functions[DUMMY_FUNCS[1]]
    assert func2.name == DUMMY_FUNCS[1]
    assert func2.args == ["d", "e", "f"]

    assert func2.outs == ["a", "b", "c"]
    d, e, f = 1., 2., 3.
    print(("func2(d, e, f)",func2(d, e, f)))
    a, b, c = func2(d, e, f)

    assert a == 3 * d
    assert b == 5 * d + e
    assert c == 6 * f + 2

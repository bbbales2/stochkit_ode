#!/usr/bin/env python

import fileinput
import numpy
import os
import pickle
import shutil
import struct
import subprocess
import sys
import tempfile

def ode(model, t, i, species = ''):
    # Build temporary files
    outputdir = tempfile.mkdtemp()
    [mfd, modelfile] = tempfile.mkstemp()

    path = os.path.abspath(os.path.dirname(__file__))

    mfhandle = os.fdopen(mfd, 'w')
    mfhandle.write(model)
    mfhandle.close()

    shutil.rmtree(outputdir)

    args = []

    args.append('-m ' + modelfile)

    args.append('-t ' + str(t))
    args.append('-i ' + str(i))
    if species != '':
        args.append('--species ' + str(species))
    args.append('--out-dir ' + outputdir)
    args.append('--force')

    print '{0}/bin/stochkit_ode {1}'.format(path, args)

    process = subprocess.Popen('{0}/bin/stochkit_ode {1}'.format(path, " ".join(args)).split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = process.communicate()

    if process.returncode != 0:
        raise Exception("""Stochkit_ode failed: 
out : {0}
error : {1}""".format(out,error))
    
    # Collect all the output data
    values = numpy.loadtxt(outputdir + '/output.txt')

    shutil.rmtree(outputdir)
    os.remove(modelfile)
    return values

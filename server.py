#!/usr/bin/env python

from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor

import cgi
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
import numpy
import os
import pickle
import signal
import shutil
import StringIO
import subprocess
import sys
import tempfile
import threading

# Change directory into folder where this file lives
path = os.path.abspath(os.path.dirname(__file__))
os.chdir(path)

# Conceptually, these need to be arguments (presumably via function call, not cmd line parsing)
dataPort = 8083
myPort = 8084
datadir = path + "/datadir/"

# We need to have state to our webserver. This can be entirely custom per program. In this program, the variable 'jobs' contains all the state, and it is pickled and loaded to and from files
#
# I am not a fan of pushing this logic into distribute land. I'm a fan of just rigging it up however. The granularity of our GUI-based jobs should never get past the state of being unmanageable in this way
try:
    fhandle = open('jobs', 'r')
    jobs = pickle.loads(fhandle.read())
    fhandle.close()
except:
    jobs = {}

# I request this function be called at the end of the program (look down the code near the end). It cleans up and saves the jobs to a file. It should also join all the running threads and such... But I don't do that :DD:D:D:D:D:DD
def clean_up():
    fhandle = open('jobs', 'w')
    fhandle.write(pickle.dumps(jobs))
    fhandle.close()

# This stuff is so annoying. I have considered asking Sheng to make StochKit a real ubuntu-like package, but I think the truth of the matter is that we're going to be packaging scientific software, which means we'll need to be ready to flex for it.
# The only kinda-solution for this I see right now is, since we'll probably be writing Python interfaces to the bulk of the software we use, we could package the modules with distutils?
#   Doing this, and becoming one with the Python environment help with things like shared dependencies (not 5 versions of StochKit in one StochSS install) and encapuslate junk like these environment variables
#os.environ['LD_LIBRARY_PATH'] = os.environ['STOCHKIT_HOME'] + '/libs/boost_1_53_0/stage/lib/'
os.environ['STOCHKIT_HOME'] = os.getcwd() + '/StochKit2.0.8/'
os.environ['LD_LIBRARY_PATH'] = os.environ['STOCHKIT_HOME'] + '/libs/boost_1_53_0/stage/lib/'
os.environ['DYLD_LIBRARY_PATH'] = os.environ['STOCHKIT_HOME'] + '/libs/boost_1_53_0/stage/lib/'
os.environ['STOCHKIT_ODE'] = os.getcwd()

# Weeeeeeeee matplotlib might not be threadsafe... So I lock the whole thing!
runlock = threading.Lock()
def runode(model, time, increment):
    runlock.acquire()

    jobid = len(jobs)
    jobs[jobid] = { "args" : { "model" : model, "time" : time, "increment" : increment } }

    # Assemble the argument list
    tempFolder = tempfile.mkdtemp(dir = datadir)
    [osid, model_file_name] = tempfile.mkstemp(dir = tempFolder)
    model_file = os.fdopen(osid, 'w')
    model_file.write(model)
    model_file.close()

    # Run the ode
    cmd = "bin/stochkit_ode -t {0} -i {1} --out-dir {2}/output -m {3} --label".format(time, int(float(time)/float(increment)), tempFolder, model_file_name)

    process = subprocess.Popen(cmd.split(), stderr = subprocess.PIPE, stdout = subprocess.PIPE)
    stdout, stderr = process.communicate()

    print stdout, stderr

    # Load up the output data and plot it
    f = open('{0}/output/output.txt'.format(tempFolder), 'r')
    names = f.readline().split()
    datas = numpy.loadtxt(f.readlines(), unpack = True)

    plots = []
    for (name, data) in zip(names[1:], datas[1:]):
        # We gonna save these pictures inside our folder. This can all be app specific. No reason we couldn't save in cloud here if we support it
        [handle, tempfilename] = tempfile.mkstemp(dir = datadir, suffix = '.png')
        os.remove(tempfilename)

        matplotlib.pyplot.plot(datas[0], data)
        matplotlib.pyplot.xlabel('Time')
        matplotlib.pyplot.title('Simulated for {0}s in {1}s increments'.format(time, increment))
        matplotlib.pyplot.ylabel(name)

        # Chandra:
        # These next two lines... I think they're heavily dependent on the cloud stuff
        # Up until this point I just do whatever is necessary (and possible) on the 'host' computer. May be saving stuff in weird formats, calling code that requires licenses (Matlab), in general, being a bad webserver
        #
        # But now we need to save real files that need to be accessible to other stuff
        #    Perhaps: We write to a special place that StochSS promises to save?
        #    And we're given an access token of some sort that can be handled by J-script/python to access the file regardless of how
        #         the data gets shifted around in the back end
        #
        #    It's not just images. Conceptually, I could be writing just about anything here (and it makes sense to do so)
        #    It probably makes sense in many cases to use StochSS to orchestrate a huge parameter sweep or whatever, and then somehow export bits and pieces
        #        to the user to cmpute with on the side
        matplotlib.pyplot.savefig(tempfilename, format='png')
        plots.append('datadir/{1}'.format(dataPort, tempfilename.split('/')[-1]))

        matplotlib.pyplot.clf()

    jobs[jobid]["plots"] = plots
    # We just throw away all the temporary data the user has created
    shutil.rmtree(tempFolder)
    runlock.release()

# Here is our JSON interface to the outside world (be they browsers or other computational units)
# Ideally these encapsulate (along with the 3rd party data server) all the ways someone wants to interact with this server
class ODE(Resource):
    isLeaf = True

    # Get requests are used to respond with information about the state of the system
    def render_GET(self, request):
        # results is in this format, one entry per job, can be entirely custom
        # results = [ {"jobid" : jobid, "args" : (model, time, increment), "plots" : plots},
        #             {"jobid" : jobid, "args" : (model, time, increment), "plots" : plots}, ..}
        # Note: if job is not finished, plots element will not be there!!

        # Gotta send this header to the client to allow cross-site js requests..
        request.setHeader('Access-Control-Allow-Origin', '*')

        return '{0}'.format(json.dumps(jobs))

    # Post requests post data to the server... That corresponds logically to an rpc call
    def render_POST(self, request):
        req = json.loads(request.args["request"][0])

        # req comes out a real python object that corresponds to the javascript object send
        #     This is the power of JSON!
        # req = { model : "dimer_decay.xml", time: "100", increment: "2" } if you just wanted to execute Python
        # Note: The input still needs sanitized at this point. Could be security blargs!

        # Gotta send this header to the client to allow cross-site js requests...
        request.setHeader('Access-Control-Allow-Origin', '*')

        req["type"] = 'ode'

        if req["type"] == "ode":
            model = str(req["model"])
            time = float(req['time'])
            increment = int(req['increment'])
            
            # Start our computation in a thread and return some sort of status
            threading.Thread(target = runode, args = (model, time, increment)).start()

            return '{0}'.format(json.dumps( { "status" : "success" } ))
        else:
            return '{0}'.format(json.dumps( { "status" : "failed", "error" : "type not ode not supported yet" } ))

# Start the little webserver
root = ODE()
factory = Site(root)

# When the webserver shuts down, call the clean_up function
reactor.addSystemEventTrigger('after', 'shutdown', clean_up)
reactor.listenTCP(myPort, factory)
reactor.run()

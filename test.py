import ode
import numpy

fhandle = open('dimer_decay.xml', 'r')
model = fhandle.read()
fhandle.close()

trajectories = ode.ode(model, 1, 100)

print type(trajectories)
print trajectories

#pull in stuff from main StochKit makefiles
include $(STOCHKIT_ODE)/.make/makefile.c
include $(STOCHKIT_ODE)/.make/dependency.h
include $(STOCHKIT_ODE)/.make/src4obj.h

all: bin/stochkit_ode bin/stochkit_ode_debug

bin/stochkit_ode: ./ode.cpp ./ODECommandLine.o $(INPUT_DEPS) $(SERIAL_DEPS) $(UTILITY_DEPS) Input_ODE_before_compile.h
	@mkdir -p bin
	$(CXX)  ./ode.cpp ./ODECommandLine.o $(INPUT_SRC) $(PARAMETER_SRC) -o  ./bin/stochkit_ode $(ALLOPTIONS) 

bin/stochkit_ode_debug: ./ode.cpp ./ODECommandLine.o $(INPUT_DEPS) $(SERIAL_DEPS) $(UTILITY_DEPS) Input_ODE_before_compile.h
	@mkdir -p bin
	$(CXX)  -DDEBUG ./ode.cpp ./ODECommandLine.o $(INPUT_SRC) $(PARAMETER_SRC) -o  ./bin/stochkit_ode_debug $(ALLOPTIONS)

ODECommandLine.o: ./ODECommandLine.cpp
	$(CXX) -c ./ODECommandLine.cpp $(COMPILE_ONLY_OPTIONS)

include Makefile.ODE

clean:
	rm -f *.o ./bin/stochkit_ode ./bin/stochkit_ode_debug

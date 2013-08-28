cd cvode
tar -xzf cvode-2.7.0.tar.gz
cd cvode-2.7.0
./configure --prefix=$PWD/cvode
make
make install
cd ../
cd ../
tar -xzf StochKit2.0.8.tgz
cd StochKit2.0.8
./install.sh
cd ../
export STOCHKIT_HOME=$PWD/StochKit2.0.8
export STOCHKIT_ODE=$PWD
make

cd C:\Users\jross\code\qpid-cpp
rmdir /q /s bld
mkdir bld
cd bld
cmake .. -DCMAKE_INSTALL_PREFIX=C:\local\qpid-install -DBOOST_ROOT=%BOOST_ROOT% -DBOOST_LIBRARYDIR=%BOOST_LIBRARYDIR% -DBUILD_BINDING_DOTNET=OFF
cmake --build . --target INSTALL

md %PYTHON_BUILD_DIR%
md %CPP_BUILD_DIR%
cd %CPP_BUILD_DIR%

cmake %CPP_SOURCE_DIR% -G "Visual Studio 11 2012" -DBOOST_ROOT=%BOOST_ROOT% -DBOOST_LIBRARYDIR=%BOOST_LIBRARYDIR% -DBUILD_BINDING_DOTNET=OFF

cd %PYTHON_SOURCE_DIR%

python setup.py build --build-base=%PYTHON_BUILD_DIR% --build-scripts=%PYTHON_BUILD_DIR%\\bin

cd %CPP_BUILD_DIR%

cmake --build . --config RelWithDebInfo -- /m

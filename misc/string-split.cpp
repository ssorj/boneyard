#include <chrono>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

std::vector<std::string> split(const std::string &s, char delim) {
    std::stringstream ss;
    std::string elem;
    std::vector<std::string> elems;

    ss.str(s);
    
    while (std::getline(ss, elem, delim)) {
        elems.push_back(elem);
    }

    return elems;
}

int main(int argc, char** argv) {
    std::vector<std::string> x = split("a,b,c", ',');

    std::cout << x[0] << "_" << x[1] << "_" << x[2] << std::endl;
    
    return 0;
}

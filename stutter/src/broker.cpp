#include <proton/connection.hpp>
#include <proton/container.hpp>
#include <proton/counted_ptr.hpp>
#include <proton/event.hpp>
#include <proton/handler.hpp>
#include <proton/link.hpp>
#include <proton/message.hpp>
#include <proton/sender.hpp>
#include <proton/terminus.hpp>
#include <proton/url.hpp>

using namespace proton;

int main(int argc, char**) {
    connection connection();
    container container();
    counted_ptr ptr();
    event event();
    link link();
    message message();
    handler handler();
    sender sender();
    terminus terminus();
    url url();
    
    return 0;
}

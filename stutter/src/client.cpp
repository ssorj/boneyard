#include <proton/container.hpp>
#include <proton/counted_ptr.hpp>
#include <proton/event.hpp>
#include <proton/handler.hpp>
#include <proton/message.hpp>
#include <proton/receiver.hpp>
#include <proton/sender.hpp>
#include <proton/url.hpp>

using namespace proton;

int main(int argc, char**) {
    container container();
    counted_ptr ptr();
    event event();
    handler handler();
    message message();
    receiver receiver();
    sender sender();
    url url();
    
    return 0;
}

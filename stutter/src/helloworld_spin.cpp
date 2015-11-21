#include "proton/spin/spin_container.hpp"
#include "proton/spin/spin_connection.hpp"
#include "proton/spin/spin_sender.hpp"
#include "proton/spin/spin_receiver.hpp"
#include "proton/spin/received_message.hpp"
#include "proton/message.hpp"

#include <iostream>

using proton::spin;

int main(int argc, char **argv) {
    try {
        spin_container container();
        spin_connection conn = container.create_connection("localhost:5672");
        spin_receiver receiver = conn.create_receiver("examples");
        spin_sender sender = conn.create_sender("examples");

        proton::message msg1("Hello World!");

        sender.send(msg1); // => sent_message, but we don't use it in this example

        received_message msg2 = receiver.receive();
        
        std::cout << msg2.body() << std::endl; // .body() works directly on received_message

        msg2.accept();

        container.close();

        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
    }

    return 1;
}

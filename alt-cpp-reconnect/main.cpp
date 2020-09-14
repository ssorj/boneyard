#include <iostream>
#include <vector>

class reconnect_options {
    bool enabled_ {};
    std::vector<std::string> failover_urls_ {};
    int max_attempts_ {0};

public:
    reconnect_options& enabled(const bool value) {
        enabled_ = value;
        return *this;
    }

    bool enabled() {
        return enabled_;
    }

    reconnect_options& failover_urls(const std::vector<std::string>& urls) {
        failover_urls_ = urls;
        return *this;
    }

    std::vector<std::string>& failover_urls() {
        return failover_urls_;
    }

    reconnect_options& max_attempts(const int attempts) {
        max_attempts_ = attempts;
        return *this;
    }

    int max_attempts() {
        return max_attempts_;
    }
};

class connection_options {
    reconnect_options reconnect_ = reconnect_options {};

public:
    reconnect_options& reconnect() {
        return reconnect_;
    }
};

int main() {
    auto opts = connection_options{};

    opts.reconnect().enabled(true);
    opts.reconnect().failover_urls({ "a", "b" });
    opts.reconnect().max_attempts(5);

    // Or:

    auto ropts = connection_options{}.reconnect();

    ropts.enabled(true);
    ropts.failover_urls({ "a", "b" });
    ropts.max_attempts(5);

    std::cout << opts.reconnect().enabled() << "\n";

    for (std::string& url : opts.reconnect().failover_urls()) {
        std::cout << url << "\n";
    }

    std::cout << opts.reconnect().max_attempts() << "\n";

    return 0;
}

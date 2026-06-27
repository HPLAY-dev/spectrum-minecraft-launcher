#include "mc/common/utils.hpp"

#include <cassert>

int main() {
    assert(mc::common::to_lower("ABC") == "abc");
    assert(mc::common::starts_with("1.20.4", "1.20"));
    return 0;
}

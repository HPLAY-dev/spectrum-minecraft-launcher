#pragma once

#include <string>
#include <vector>

namespace mc::common {

std::string to_lower(std::string value);
bool starts_with(const std::string& value, const std::string& prefix);
std::vector<std::string> split(const std::string& value, char delimiter);

}  // namespace mc::common

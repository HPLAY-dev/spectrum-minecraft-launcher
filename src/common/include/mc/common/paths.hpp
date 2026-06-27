#pragma once

#include <filesystem>
#include <string>

namespace mc::common {

std::filesystem::path expand_user_path(const std::string& path);
std::filesystem::path default_minecraft_dir();

}  // namespace mc::common

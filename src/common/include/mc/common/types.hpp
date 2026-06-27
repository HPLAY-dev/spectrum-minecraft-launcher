#pragma once

#include <string>
#include <vector>

namespace mc::common {

struct VersionEntry {
    std::string id;
    std::string type;
    std::string url;
};

struct LaunchOptions {
    std::string java_path;
    std::string instance_name;
    std::string minecraft_dir;
    std::string username;
    std::string memory;
};

}  // namespace mc::common

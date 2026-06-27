#pragma once

#include "mc/common/types.hpp"

#include <string>
#include <vector>

namespace mc::launcher {

class Engine {
public:
    explicit Engine(std::string minecraft_dir);

    [[nodiscard]] std::string minecraft_dir() const;
    [[nodiscard]] std::vector<mc::common::VersionEntry> list_versions() const;
    [[nodiscard]] std::string build_launch_command(const mc::common::LaunchOptions& options) const;

private:
    std::string minecraft_dir_;
};

}  // namespace mc::launcher

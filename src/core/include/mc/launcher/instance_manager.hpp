#pragma once

#include <string>
#include <vector>

namespace mc::launcher {

class InstanceManager {
public:
    explicit InstanceManager(std::string minecraft_dir);

    [[nodiscard]] std::vector<std::string> list_instances() const;
    [[nodiscard]] bool rename_instance(const std::string& from, const std::string& to);
    [[nodiscard]] bool remove_instance(const std::string& name);

private:
    std::string minecraft_dir_;
};

}  // namespace mc::launcher

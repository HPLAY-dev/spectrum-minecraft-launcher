#include "mc/launcher/instance_manager.hpp"

#include <filesystem>

namespace mc::launcher {

InstanceManager::InstanceManager(std::string minecraft_dir)
    : minecraft_dir_(std::move(minecraft_dir)) {}

std::vector<std::string> InstanceManager::list_instances() const {
    std::vector<std::string> names;
    const auto versions_dir = std::filesystem::path(minecraft_dir_) / "versions";
    if (!std::filesystem::exists(versions_dir)) {
        return names;
    }
    for (const auto& entry : std::filesystem::directory_iterator(versions_dir)) {
        if (entry.is_directory()) {
            names.push_back(entry.path().filename().string());
        }
    }
    return names;
}

bool InstanceManager::rename_instance(const std::string& from, const std::string& to) {
    const auto root = std::filesystem::path(minecraft_dir_) / "versions";
    const auto source = root / from;
    const auto target = root / to;
    if (!std::filesystem::exists(source) || std::filesystem::exists(target)) {
        return false;
    }
    std::filesystem::rename(source, target);
    return true;
}

bool InstanceManager::remove_instance(const std::string& name) {
    const auto target = std::filesystem::path(minecraft_dir_) / "versions" / name;
    if (!std::filesystem::exists(target)) {
        return false;
    }
    return std::filesystem::remove_all(target) > 0;
}

}  // namespace mc::launcher

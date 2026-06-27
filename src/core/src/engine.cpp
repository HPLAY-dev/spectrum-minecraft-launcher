#include "mc/launcher/engine.hpp"

#include "mc/common/paths.hpp"

namespace mc::launcher {

Engine::Engine(std::string minecraft_dir)
    : minecraft_dir_(std::move(minecraft_dir)) {}

std::string Engine::minecraft_dir() const {
    return minecraft_dir_;
}

std::vector<mc::common::VersionEntry> Engine::list_versions() const {
    return {};
}

std::string Engine::build_launch_command(const mc::common::LaunchOptions& options) const {
    return options.java_path + " -Xmx" + options.memory +
           " -Djava.library.path=" + minecraft_dir_ + "/versions/" + options.instance_name +
           "/natives -jar " + minecraft_dir_ + "/versions/" + options.instance_name + "/" +
           options.instance_name + ".jar";
}

}  // namespace mc::launcher

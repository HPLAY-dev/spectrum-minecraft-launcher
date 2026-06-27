#include "mc/common/branding.hpp"
#include "mc/common/paths.hpp"
#include "mc/launcher/engine.hpp"
#include "mc/launcher/instance_manager.hpp"

#include <iostream>

int main() {
    const auto minecraft_dir = mc::common::default_minecraft_dir().string();
    mc::launcher::Engine engine(minecraft_dir);
    mc::launcher::InstanceManager manager(minecraft_dir);

    std::cout << mc::common::app_display_title() << '\n';
    std::cout << "Codename: " << mc::common::kCodename << '\n';
    std::cout << "Major: " << mc::common::kMajorVersion << '\n';
    std::cout << "Minecraft dir: " << engine.minecraft_dir() << '\n';
    std::cout << "Instances:\n";
    for (const auto& name : manager.list_instances()) {
        std::cout << "  - " << name << '\n';
    }
    return 0;
}

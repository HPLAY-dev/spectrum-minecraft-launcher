#include "mc/common/paths.hpp"

#include <cstdlib>

namespace mc::common {

std::filesystem::path expand_user_path(const std::string& path) {
    if (path.empty()) {
        return {};
    }
    if (path[0] == '~') {
        const char* home = std::getenv("USERPROFILE");
        if (home == nullptr) {
            home = std::getenv("HOME");
        }
        if (home != nullptr) {
            return std::filesystem::path(home) / path.substr(2);
        }
    }
    return std::filesystem::path(path);
}

std::filesystem::path default_minecraft_dir() {
#ifdef _WIN32
    const char* appdata = std::getenv("APPDATA");
    if (appdata != nullptr) {
        return std::filesystem::path(appdata) / ".minecraft";
    }
#endif
    return expand_user_path("~/.minecraft");
}

}  // namespace mc::common

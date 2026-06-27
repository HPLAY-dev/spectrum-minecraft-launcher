#pragma once

#include "mc/common/version.generated.hpp"

#include <string>

namespace mc::common {

inline constexpr const char* kAppName = SERENA_APP_NAME;
inline constexpr const char* kCodename = SERENA_CODENAME;
inline constexpr int kMajorVersion = SERENA_MAJOR_VERSION;
inline constexpr const char* kQuarter = SERENA_QUARTER;
inline constexpr const char* kVersionString = SERENA_VERSION_STRING;

inline std::string app_display_title() {
    return std::string(kAppName) + " " + kVersionString;
}

}  // namespace mc::common

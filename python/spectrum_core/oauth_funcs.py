"""OAuth — Rust 优先，回退 mclauncher_core"""

from __future__ import annotations

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def get_mc_token(need_refresh_token=False):
        result = _r.oauth_authenticate()
        if need_refresh_token:
            return result["access_token"], result["refresh_token"]
        return result["access_token"]

    def refresh_token(refresh_token_str):
        return _r.oauth_refresh(refresh_token_str)["access_token"]

    def get_mslogin_uuid_name(access_token):
        return _r.get_mslogin_uuid_name(access_token)

    def is_owned(mc_token, with_profile_data=False):
        from mclauncher_core.oauth_funcs import is_owned as _is_owned

        return _is_owned(mc_token, with_profile_data)

else:
    from mclauncher_core.oauth_funcs import *  # noqa: F403

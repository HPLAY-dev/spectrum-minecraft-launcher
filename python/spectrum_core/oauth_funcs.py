"""OAuth — Rust 优先，回退 py_fallback"""

from __future__ import annotations

from spectrum_core import rust_available, require_native

if rust_available():
    _r = require_native()

    def get_mc_token(need_refresh_token=False, **kwargs):
        result = _r.oauth_authenticate()
        if need_refresh_token:
            return result["access_token"], result["refresh_token"]
        return result["access_token"]

    def refresh_token(refresh_token_str):
        return _r.oauth_refresh(refresh_token_str)["access_token"]

    def get_mslogin_uuid_name(access_token):
        return _r.get_mslogin_uuid_name(access_token)

    def is_owned(mc_token, with_profile_data=False):
        try:
            uuid, name = _r.get_mslogin_uuid_name(mc_token)
            if with_profile_data:
                return [True, {"id": uuid, "name": name}]
            return True
        except Exception:
            return False

else:
    from spectrum_core.py_fallback.oauth_funcs import *  # noqa: F403

# chrome_vip_profile (local only)

This directory holds a **local** Chrome/CDP VIP session profile for TVPL automation.

**Do not commit** cookies, `Local State`, `Default/`, Crashpad, caches, or any profile artifacts.

Profiles must live only on the operator machine (or encrypted vault). If this path ever appears in git history, rotate TVPL credentials and invalidate sessions, then scrub history.

See issues #611 / #612.

# chrome_vip_profile (local-only)

This directory holds a Chrome user-data profile used by the TVPL VIP crawler on the operator's machine.
It contains cookies, saved logins and session state, so it must **never** be committed.

- Everything here except this README is ignored by `.gitignore` (`**/chrome_vip_profile/*`).
- Create the profile locally by launching the crawler; do not copy it between machines via git.
- See #626 / #627 for the cleanup and history scrub.

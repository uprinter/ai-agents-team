# Codex permission and keyring handling

A sandboxed `glab auth status` can falsely report missing authentication when the sandbox cannot read the operating-system keyring. If it fails for credential or keyring access, repeat that diagnostic with Codex `require_escalated` permission before concluding that the user is signed out.

`require_escalated` is a tool permission mode, not a shell flag. Use it for authenticated GitLab HTTPS transport commands when keyring or network access requires it.

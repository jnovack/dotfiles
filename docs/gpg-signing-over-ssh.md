# gpg commit signing over ssh

On macOS, `pinentry-mac` needs a connection to the window server to draw its
passphrase dialog. An SSH session has no window server, so when gpg-agent needs
a passphrase for a remote client it either draws the dialog on the physical
console — where the person at the other end of the SSH connection cannot see
it — or fails outright, and `git commit` aborts with `gpg failed to sign the
data`.

A single gpg-agent serves the desktop and every SSH login through one socket, and
its `pinentry-program` is fixed for all of them. So the fix has two halves:

| Half | Does |
| --- | --- |
| A pinentry dispatcher | Lets one agent serve a GUI dialog to the desktop and a terminal prompt over SSH |
| A login-time preset | Loads the passphrase into the agent at console login, so SSH never needs a pinentry at all |

The preset is what makes signing silent. The dispatcher is the fallback for when
it doesn't run, so the failure mode is a prompt you can answer rather than one
you cannot see.

## Prerequisites

- macOS with Homebrew.
- `brew install gnupg pinentry pinentry-mac` — `pinentry` supplies
  `pinentry-curses`, which is the terminal half of the dispatcher.
- A GPG signing key, with `commit.gpgsign true` and `user.signingkey` already
  set, signing correctly at the console. This guide only makes that work over
  SSH; it does not set signing up from scratch.
- The key's passphrase saved into the login keychain — tick **Save in Keychain**
  the next time `pinentry-mac` prompts at the console. Confirm with:

  ```sh
  security find-generic-password -s GnuPG
  ```

Paths below assume Apple Silicon (`/opt/homebrew`). On Intel, substitute
`/usr/local` throughout.

## 1. Find the keygrip of your signing subkey

The preset addresses a key by *keygrip*, not by key ID or fingerprint.

```sh
gpg --list-secret-keys --with-keygrip --keyid-format=long you@example.com
```

Take the `Keygrip` printed under the subkey marked `[S]` — the signing subkey,
not the `[C]` primary. Substitute it for `REPLACE_WITH_YOUR_KEYGRIP` below.

## 2. Install the pinentry dispatcher

gpg-agent forwards `PINENTRY_USER_DATA` from the *calling* gpg process, which is
what makes a per-request decision possible from a single agent-wide setting.

Write `~/.gnupg/pinentry-auto`:

```sh
#!/bin/sh
# Dispatch to a terminal pinentry when the requesting session has no Aqua GUI.
#
# One gpg-agent serves both the desktop and any SSH logins, so its
# pinentry-program is fixed for every client. pinentry-mac needs a window
# server connection, which an SSH session does not have.
#
# gpg-agent forwards PINENTRY_USER_DATA from the *calling* gpg process, so
# the SSH session can ask for curses per-request while the desktop, which
# leaves the variable unset, keeps the GUI dialog.
case "$PINENTRY_USER_DATA" in
    *curses*) exec /opt/homebrew/bin/pinentry-curses "$@" ;;
esac
exec /opt/homebrew/bin/pinentry-mac "$@"
```

Make it executable:

```sh
chmod 700 ~/.gnupg/pinentry-auto
```

## 3. Set the variable in SSH sessions only

This repo's canonical `.zshrc` already does this — if `~/.zshrc` is the synced
symlink, skip to step 4. Otherwise add to `~/.zshrc`:

```sh
export GPG_TTY=$(tty)

if [ -n "$SSH_CONNECTION" ]; then
    export PINENTRY_USER_DATA=curses
    gpg-connect-agent updatestartuptty /bye >/dev/null 2>&1
fi
```

`GPG_TTY` is what lets `pinentry-curses` find the terminal to draw on;
`updatestartuptty` tells an already-running agent about the current one.

## 4. Write the preset script

`~/.gnupg/preset-signing-key.sh` carries the passphrase from the login keychain
into the agent. The two are separate stores — unlocking the keychain at login
does not populate the agent.

```sh
#!/bin/sh
# Prime gpg-agent's passphrase cache at console login.
#
# The login keychain already holds this passphrase (pinentry-mac put it there),
# but the keychain and the agent's cache are separate stores -- unlocking one
# does not populate the other. Something has to carry it across, and that
# something must run in the console session, where login-keychain access is
# unambiguous. An SSH session is the wrong place to try: it has no window
# server for pinentry-mac, and pinentry-curses cannot read the keychain.
set -eu

KEYGRIP=REPLACE_WITH_YOUR_KEYGRIP

# Resolved rather than hardcoded: the Cellar path carries the gnupg version and
# would break on the next `brew upgrade`.
PRESET="$(/opt/homebrew/bin/gpgconf --list-dirs libexecdir)/gpg-preset-passphrase"

# Starts the agent if launchd got here before any gpg invocation did.
/opt/homebrew/bin/gpg-connect-agent /bye >/dev/null 2>&1

/usr/bin/security find-generic-password -s GnuPG -a "$KEYGRIP" -w \
    | "$PRESET" --preset "$KEYGRIP"
```

```sh
chmod 700 ~/.gnupg/preset-signing-key.sh
```

## 5. Configure gpg-agent

`~/.gnupg/gpg-agent.conf`:

```text
# 400 days. max-cache-ttl is the binding limit -- it expires an entry even when
# it is used constantly -- so both are set together or the pair does nothing.
# The agent's own lifetime is the real bound: reboot, logout or
# `gpgconf --kill gpg-agent` drops the cache whatever these say. These values
# just stop a timer from expiring it first.
default-cache-ttl 34560000
max-cache-ttl 34560000
default-cache-ttl-ssh 34560000
max-cache-ttl-ssh 34560000

pinentry-program /Users/YOUR_USERNAME/.gnupg/pinentry-auto

# Required before gpg-preset-passphrase --preset is accepted.
allow-preset-passphrase
```

`pinentry-program` must be an **absolute path** — gpg-agent does not expand `~`.

## 6. Run the preset at console login

A LaunchAgent in `~/Library/LaunchAgents` loads for the Aqua session only, so it
runs on console login and never on an SSH login — exactly the boundary needed,
since login-keychain access is unambiguous there.

`~/Library/LaunchAgents/com.YOUR_USERNAME.gpg-preset.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.YOUR_USERNAME.gpg-preset</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/.gnupg/preset-signing-key.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/gpg-preset.log</string>
</dict>
</plist>
```

## 7. Activate, at the console

Both commands must run in a console session, not over SSH.

```sh
plutil -lint ~/Library/LaunchAgents/com.YOUR_USERNAME.gpg-preset.plist
gpgconf --kill gpg-agent
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.YOUR_USERNAME.gpg-preset.plist
```

The first run raises a keychain dialog: `security` is a different binary from the
`pinentry-mac` that created the item, so the ACL challenges it. Click **Always
Allow**, or it will ask again at every login.

## Verification

At the console, confirm the agent holds the passphrase:

```sh
gpg-connect-agent 'keyinfo REPLACE_WITH_YOUR_KEYGRIP' /bye
```

```text
S KEYINFO <keygrip> D - - 1 P - - -
                          ^ cached: 1 = primed, - = will prompt
```

Then SSH in and sign something. It should complete with no prompt:

```sh
echo test | gpg --clearsign --local-user you@example.com >/dev/null
```

If the preset failed, `~/Library/Logs/gpg-preset.log` says why, and the fallback
applies: you get a `pinentry-curses` box in the terminal instead of silence.

## Gotchas

- **`max-cache-ttl` is the binding limit, not `default-cache-ttl`.**
  `default-cache-ttl` resets on every use, but `max-cache-ttl` expires the entry
  even when it is used constantly. Raising one without the other does nothing.
- **No TTL survives the agent dying.** Reboot, logout and `gpgconf --kill
  gpg-agent` clear the cache whatever the config says. The long TTL converts
  "expires on a timer" into "expires when the agent restarts"; the preset is what
  covers the restart.
- **`pinentry-curses` needs a real TTY.** This covers a human typing `git commit`
  over SSH. Genuinely non-interactive contexts — CI, an agent harness, anything
  where `tty` returns `not a tty` — can only ever use the primed cache, which is
  the other reason the preset matters.
- **Keygrip, not key ID.** `gpg-preset-passphrase` and `keyinfo` both take the
  keygrip. Passing a fingerprint or long key ID fails silently-ish and leaves the
  cache cold.
- **This is a real security trade.** The signing passphrase sits in the agent for
  the full TTL, reloaded automatically at every console login. Anyone with access
  to your unlocked console can sign as you without knowing the passphrase. That is
  the price of prompt-free SSH commits.

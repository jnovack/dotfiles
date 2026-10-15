# VP3256 Input Toggle

Switches a ViewSonic VP3256-4K display between its DisplayPort and USB-C
inputs via DDC/CI, triggered by a global macOS keyboard shortcut — no need
to reach behind the monitor to press its physical input button.

## Prerequisites

- Apple Silicon Mac (M1/M2/M3/M4)
- [Homebrew](https://brew.sh)
- DDC/CI enabled on the monitor: OSD → Setup Menu → DDC/CI → On

## Steps

### 1. Install m1ddc

`m1ddc` sends DDC/CI commands to displays connected over USB-C/DisplayPort
Alt Mode.

```bash
brew install m1ddc
```

### 2. Make the toggle script executable

The script lives in this repo as `toggle-vp3256-input.sh` and targets this
Mac's VP3256 by its display System UUID
(`757B5DBB-D4F0-4D6C-AC7B-D6CBA7040A60`). It alternates between input code
`15` (DisplayPort) and `27` (USB-C) — the standard MCCS values `m1ddc`
documents. Since `m1ddc` has no command to read the monitor's current input,
the script tracks the last input it set in `~/.cache/vp3256-input-state` and
flips it on each run.

```bash
chmod +x toggle-vp3256-input.sh
```

Run it from this directory, or symlink it onto your `PATH`:

```bash
ln -s "$(pwd)/toggle-vp3256-input.sh" ~/bin/toggle-vp3256-input.sh
```

### 3. Create an Automator Quick Action

This registers the script as a macOS Service so it can be bound to a global
hotkey without any background process running.

1. Open **Automator** → File → New → **Quick Action**.
2. At the top of the workflow, set **Workflow receives no input** in **any
   application**.
3. Search the action library for **Run Shell Script**, drag it into the
   workflow.
4. Set Shell to `/bin/zsh`, Pass input **as arguments**, and enter:

   ```bash
   ~/bin/toggle-vp3256-input.sh
   ```

5. Save the Quick Action as **Toggle VP3256 Input**.

### 4. Bind a keyboard shortcut

1. Open **System Settings → Keyboard → Keyboard Shortcuts → Services**.
2. Under the **General** section, find **Toggle VP3256 Input**.
3. Click its shortcut field and press the key combo you want (e.g.
   `⌃⌥⌘I`).

## Verification

Press the assigned shortcut. The VP3256 should switch its active input
(DisplayPort ↔ USB-C). Press it again to confirm it switches back.

If the monitor ignores the command or jumps to the wrong source, this unit
remaps the standard VCP input codes — edit `DP_CODE` / `USBC_CODE` in
`toggle-vp3256-input.sh`. To find the correct System UUID and confirm which
display you're targeting (useful if adapting this to a different monitor or
Mac with multiple displays connected):

```bash
m1ddc display list detailed
```

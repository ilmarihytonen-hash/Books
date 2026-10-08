# Bookapp

PyQt6 website launcher with English, Finnish, and Swedish UI text. Translations
are maintained separately in `languages\en.json`, `languages\fi.json`, and
`languages\sv.json`. On Windows, saved websites, settings, logs, and encrypted
logins are stored in `%LOCALAPPDATA%\Bookapp`, so the executable does not need
to write beside itself.

## Run from source

Install Python 3.10 or newer, then run `build_windows.bat` to install
dependencies and create `dist\Bookapp.exe`. You can also run
`run_bookapp.bat`; if the executable is missing, it asks before running the
install and build script. Alternatively, install `requirements.txt` and run
`py launcher.py`.

Run the packaged app with `Bookapp.bat` or `run_bookapp.bat`, or open
`dist\Bookapp.exe` directly. The batch launchers use paths relative to their
own location, so the downloaded folder can be moved to another location.
`Bookapp.bat` creates or updates `Bookapp.lnk` beside itself when run.
For the packaged Windows app, `%LOCALAPPDATA%\Bookapp\logs\bookapp.log`
contains timestamped logs. Source runs write to `logs\bookapp.log`.

## Website logins and feedback

Use the browser's top-left **Menu** for Home, the GNU GPL v3 license, Help,
Feedback, Settings, and **Manage logins**. In Settings, change the interface
language, default website, browser zoom, and password-saving preference.
Turning password saving off permanently removes saved website logins from this
PC after confirmation. For the packaged Windows app, configure the feedback
destination and button text in `%LOCALAPPDATA%\Bookapp\config.json`.

Select **Manage logins** to save credentials for the current HTTPS website.
Login data is encrypted with Windows Data Protection and can only be decrypted
by the same Windows user on this computer. Select **Fill fields** to fill
matching visible login fields; Bookapp never submits the form automatically.
The encrypted data is stored in `%LOCALAPPDATA%\Bookapp\logins.dat` for the
packaged Windows app.

To configure the **Feedback** button, edit
`%LOCALAPPDATA%\Bookapp\config.json` for the packaged Windows app (or the
project `config.json` for a source run) and set `feedback_url` to an HTTPS link
or a `mailto:` address. Set
`feedback_label` to customize the button text. For example:

```json
{
  "feedback_url": "mailto:feedback@example.com",
  "feedback_label": "Report a problem"
}
```

The destination is read when the menu item is clicked; restart Bookapp after
changing the button label in the config file. On first run, existing
`config.json`, `urls.yaml`, and `logins.dat` files beside an older executable
or in the previous per-user install folder are copied into the per-user data
folder.

## Download a release

The executable is not committed to Git because the packaged Qt WebEngine app is
larger than GitHub's standard file-size limit. Push a new version tag, such as
`v1.0.6`, to build and publish a release:

```text
git tag v1.0.6
git push origin v1.0.6
```

The release contains `Bookapp.exe`, a portable Windows ZIP, and a source ZIP.
For a Windows 10/11 64-bit PC, download and extract the portable ZIP, then run
`Bookapp.bat`. The bundle includes the packaged app, so Python does not need to
be installed separately. The first launch creates or updates `Bookapp.lnk`
beside the extracted files. Alternatively, run `Bookapp.exe` directly.
Bookapp stores its changing data under Local AppData rather than next to the
executable. GitHub also automatically provides generated source-code archive
links; those are separate from the uploaded assets.

Pushes to `main` still build a temporary `Bookapp-windows` artifact,
available from the workflow run for 30 days.

## Exam mode

Select **Exam mode** in the launcher before starting the browser. The browser
then uses fullscreen and always-on-top window flags, blocks its Escape/F11/F12
keys and window-close requests, and hides URL, language, and menu controls. The
red **Quit exam** button is the in-app exit. This is application-level kiosk
behavior; it does not disable operating-system shortcuts or provide managed
device lockdown.

Build the Windows executable on Windows with `build_windows.bat`. The
executable is generated locally and is not checked into this source tree.

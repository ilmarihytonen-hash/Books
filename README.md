# Bookapp

PyQt6 website launcher with English, Finnish, and Swedish UI text. Translations
are maintained separately in `languages\en.json`, `languages\fi.json`, and
`languages\sv.json`. Saved websites and the selected language are stored in
`urls.yaml` beside the application.

## Run from source

Install Python 3.10 or newer, then run `build_windows.bat` to install dependencies
and create `dist\Bookapp.exe`. You can also install `requirements.txt` and run
`py launcher.py`.

Run the packaged app with `run_bookapp.bat`, or open `dist\Bookapp.exe` directly.
`logs\bookapp.log` contains timestamped Linux-style application logs.

## Download the Windows executable

The executable is not committed to Git because the packaged Qt WebEngine app is
larger than GitHub's standard file-size limit. GitHub Actions builds it when
changes are pushed to `main`. To download it, open the repository's **Actions**
tab, select the latest successful **Build Windows executable** run, and download
the `Bookapp-windows` artifact. Artifacts are retained for 30 days.

## Exam mode

Select **Exam mode** in the launcher before starting the browser. The browser
then uses fullscreen and always-on-top window flags, blocks its Escape/F11/F12
keys and window-close requests, and hides URL, language, and menu controls. The
red **Quit exam** button is the in-app exit. This is application-level kiosk
behavior; it does not disable operating-system shortcuts or provide managed
device lockdown.

Build the Windows executable on Windows with `build_windows.bat`. The executable
is generated locally and is not checked into this source tree.

Note that some of the code was writen with copilot but mostly was made by humans and mostly copilot has been used for bugfixes.

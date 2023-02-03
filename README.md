# nightscout-osx-menubar

View CGM data from [Nightscout] in the OS X menu bar.

**Latest version: 0.4.0**

![nightscout-osx-menubar screenshot](https://raw.githubusercontent.com/jasonlcrane/nightscout-osx-menubar/master/screenshot.png)

## Requirements

* OS X (tested with 10.8 and 10.10, may work with earlier versions)
* A working installation of Nightscout ([cgm-remote-monitor])

## Installation

1. Download [this zip file containing the app][release-zip] and unzip it.
1. Drag "Nightscout Menubar" into your "Applications" folder.
1. Run it.
1. (Optional) To run automatically on startup, go to System Preferences > Users & Groups > Login Items, and add Nightscout Menubar to the list.

## Customization

If you want to customize the display and are comfortable making small edits to a Python file, you can edit `nightscout_osx_menubar.py` within the app package.

In Finder, right-click on the app and click "Show Package Contents". Open `Contents/Resources/nightscout_osx_menubar.py` in a text editor. All the available configuration is at the top of the file.

For example:

* Change `HISTORY_LENGTH` to control the number of history menu items
* Change `MENUBAR_TEXT` to `u"{sgv} {direction}"` to shorten the menu bar text to only BG and a trend arrow
* Change `MENU_ITEM_TEXT` to likewise change how the history items are formatted
* Modify `time_ago` to return strings like "5m" instead of "5 min"
* etc.

This is not a long-term solution since your modifications won't survive a reinstall of the app.

## Development

This uses [rumps], which provides a nice interface to PyObjC to create simple menu bar apps, and [py2app], a Python setuptools command which allows you to package Python scripts as standalone OS X applications.

**To run the app in development:**

```bash
git clone https://github.com/kretep/nightscout-osx-menubar
cd nightscout-osx-menubar
pip install -r requirements.txt --user  # This may take a while
python nightscout_osx_menubar.py
```

* Install requirements with `--user` because [rumps is not compatible with virtualenv][rumps-virtualenv]. You could alternatively `sudo pip install`.
* If this fails, try [installing Xcode Command Line Tools][xcode-cli].

**To build a standalone app in `dist/`:**

```bash
python setup.py py2app
```

It's normal that some modules cannot be found. The application might still run properly. If it doesn't, see the next section:

## Troubleshooting

If an error occurs while running the standalone app, some additional information was probably logged to the console. To view the app's output in the terminal, start the app from the command line:

```bash
cd /Applications  # or wherever your application is
./Nightscout\ Menubar.app/Contents/MacOS/Nightscout\ Menubar
```

Add the `--debug` flag to print additional debug information.

If the application fails because a library cannot be loaded, such as `libffi.8.dylib`, this might be because your Python interpreter is running in a virtual environment, such as Conda. Try using a base install of Python to build the application.

## Notes

[File an issue] if you'd like to give feedback, request an enhancement, or report a bug. Pull requests are welcome.

## Disclaimer

This project is intended for educational and informational purposes only. It is not FDA approved and should not be used to make medical decisions. It is neither affiliated with nor endorsed by Dexcom.

## Thanks
This is a fork of a fork. The [original version of this tool from mddub][original_version], and [the fork from jasonlcrane][fork_version].

[Nightscout]: http://www.nightscout.info/
[cgm-remote-monitor]: https://github.com/nightscout/cgm-remote-monitor
[releases]: https://github.com/kretep/nightscout-osx-menubar/releases
[file an issue]: https://github.com/kretep/nightscout-osx-menubar/issues
[original_version]: https://github.com/mddub/nightscout-osx-menubar
[fork_version]: https://github.com/jasonlcrane/nightscout-osx-menubar
[rumps]: https://github.com/jaredks/rumps
[rumps-virtualenv]: https://github.com/jaredks/rumps/issues/9
[py2app]: https://pythonhosted.org/py2app/
[xcode-cli]: http://stackoverflow.com/questions/20929689/git-clone-command-not-working-in-mac-terminal

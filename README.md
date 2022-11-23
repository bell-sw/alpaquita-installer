# Alpaquita Linux Installer

The official installer of Alpaquita Linux.

## Usage

The installer supports cross-libc installations, i.e. it's possible
to install a musl Alpaquita Linux running on a glibc Alpaquita Linux.
So the code expects that APK key files are shipped with the package.

For that to work put the keys to the `alpaquita_installer/keys` directory.
Then build the package using the provided `setup.py` and install it as usual.
For example:

```
python setup.py build
pip install dist/<the generated wheel file>
```

The installer operates in 2 modes:
 * interactive mode with a text-based UI (default mode)
 * batch (non-interactive) mode (when `-n` is passed)

The former performs an installation based on the user's answers
in the UI, the latter - in accordance with a provided `.yaml` file.

Please consult `AUTOMATING_INSTALLATION.md` for the syntax of the `.yaml` file.

The interactive mode also generates a `setup.yaml` file with a description
of the current installation.

Passing `-h` will display the list of all supported command line arguments.

## Development environment setup
The code is Python 3. All necessary dependencies are listed in
the provided `requirements.txt`:
```
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
alpaquita-installer [args] # or python -m alpaquita_installer [args]
```

The tests are written using `pytest` and can be run with:
```
pip install pytest
pytest tests/*
```

## Acknowledgements

The code implements parts of the MVC ideas and uses many of Urwid widgets
from the [Ubuntu Subiquity installer](https://github.com/canonical/subiquity/blob/main/DESIGN.md).

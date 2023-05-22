{ lib, buildPythonApplication, setuptools, evdev, pillow, pyudev, gst-python, gobject-introspection, libadwaita, wrapGAppsHook }:

buildPythonApplication rec {
  pname = "fingerpaint";
  version = builtins.elemAt (builtins.match ".*version=\"([^\"]+)\".*" (builtins.readFile ./setup.py)) 0;

  src = ./.;

  nativeBuildInputs = [
    gobject-introspection wrapGAppsHook
  ];

  propagatedBuildInputs = [
    setuptools evdev pillow pyudev gst-python libadwaita
  ];

  meta = with lib; {
    description = "Draw using your laptop's touchpad";
    homepage = "https://github.com/Wazzaps/fingerpaint";
    platforms = platforms.linux;
    license = licenses.gpl2;
    maintainers = [
      {
        email = "david.shlemayev@gmail.com";
        matrix = "@wazzaps:matrix.org";
        github = "Wazzaps";
        githubId = 6624767;
        name = "David Shlemayev";
      }
    ];
  };
}

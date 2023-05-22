{ lib, buildPythonApplication, setuptools, evdev, pyudev, gst-python, gobject-introspection, libadwaita, wrapGAppsHook, udev }:

buildPythonApplication rec {
  pname = "fingerpaint";
  version = builtins.elemAt (builtins.match ".*version = \"([^\"]+)\".*" (builtins.readFile ./pyproject.toml)) 0;

  src = ./.;

  nativeBuildInputs = [
    gobject-introspection wrapGAppsHook
  ];

  propagatedBuildInputs = [
    setuptools evdev pyudev gst-python libadwaita udev
  ];

  preFixup = ''
  wrapProgram $out/bin/fingerpaint \
  --prefix LD_LIBRARY_PATH ":" "${udev.out}/lib" \
  '';

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

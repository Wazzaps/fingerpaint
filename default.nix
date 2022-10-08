{ lib, buildPythonApplication, setuptools, evdev, pillow, pyudev, tkinter }:

buildPythonApplication rec {
  pname = "fingerpaint";
  version = builtins.elemAt (builtins.match ".*version='([^']+)'.*" (builtins.readFile ./setup.py)) 0;

  src = ./.;

  propagatedBuildInputs = [
    setuptools evdev pillow pyudev tkinter
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
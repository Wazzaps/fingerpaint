{
  description = "Draw using your laptop's touchpad";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachSystem [ "x86_64-linux" "i686-linux" "aarch64-linux" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in rec {
        packages.fingerpaint = pkgs.python3.pkgs.callPackage ./default.nix {};
        defaultPackage = packages.fingerpaint;
      }));
}

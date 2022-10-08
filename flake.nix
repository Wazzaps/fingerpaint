{
  description = "Draw using your laptop's touchpad";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  # outputs = { self, nixpkgs, flake-utils, ... }:
  # let pkgs = nixpkgs.legacyPackages.x86_64-linux; in {
  #   # devShell.x86_64-linux = pkgs.mkShell rec {
  #   #   name = "fingerpaint-dev";
  #   #   buildInputs = with pkgs; [
  #   #     fingerpaint
  #   #   ];
  #   # };

  #   packages.x86_64-linux.fingerpaint =

  #   defaultPackage = pkgs.fingerpaint;
  # };

  # outputs = { self, nixpkgs, flake-utils, ... }: let supportedLinuxSystems = [
  #   "x86_64-linux" "i686-linux" "aarch64-linux"
  # ]; in {
  #   overlay = final: prev: {
  #     python3 = prev.python3.override {
  #       packageOverrides = python-final: python-prev: {
  #         chiafan-plot-sim = python-final.callPackage ./default.nix {};
  #       };
  #     };
  #   };
  # } // flake-utils.lib.eachSystem [
  #   "x86_64-linux" "i686-linux" "aarch64-linux"
  # ] (system:
  #   let pkgs = import nixpkgs {
  #         inherit system;
  #         overlays = [ self.overlay ];
  #       };

  #       chiafan-py-dev = pkgs.python3.withPackages (python-packages: with python-packages;  [
  #         setuptools
  #         click
  #       ]);
  #   in {
  #     devShell = pkgs.mkShell rec {
  #       name = "chiafan-dev";
  #       buildInputs = with pkgs; [
  #         chiafan-py-dev
  #       ];
  #     };

  #     defaultPackage = pkgs.python3Packages.chiafan-plot-sim;
  #   });

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachSystem [ "x86_64-linux" "i686-linux" "aarch64-linux" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in rec {
        packages.fingerpaint = pkgs.python3.pkgs.callPackage ./default.nix {};
        defaultPackage = packages.fingerpaint;
      }));
}
{
  pkgs ? import <nixpkgs> {},
  python ? pkgs.python36,
}:

with pkgs;
with python.pkgs;

buildPythonPackage rec {
  name = "pyrollbar";
  src = builtins.filterSource (path: type:
      type != "unknown" &&
      baseNameOf path != ".git" &&
      baseNameOf path != "result" &&
      !(pkgs.lib.hasSuffix ".nix" path)
  ) ./.;
  propagatedBuildInputs = [requests six];
}


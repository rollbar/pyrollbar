{
  pkgs ? import <nixpkgs> {}
}:

with pkgs;
let
python = let
  packageOverrides = self: super: {
    pandas = super.pandas.overridePythonAttrs(old: {
      doCheck = false;
    });

    twine = super.twine.overridePythonAttrs(old: {
      doCheck = false;
    });

    tqdm = super.tqdm.overridePythonAttrs(old: {
      doCheck = false;
    });
  };
in python36.override { inherit packageOverrides; };
pyrollbar = pkgs.callPackage ./. { inherit python; };
pyenv = python.withPackages(ps: with ps; [ pyrollbar twine mock pyramid ]);

in

stdenv.mkDerivation {
  name = "pyrollbar-shell";
  buildInputs = [ pyenv ];
}


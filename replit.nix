
{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.python310Packages.pip
    pkgs.python310Packages.setuptools
    pkgs.python310Packages.wheel

    # JRAVIS Core
    pkgs.python310Packages.flask
    pkgs.python310Packages.requests
    pkgs.python310Packages.schedule
    pkgs.python310Packages.psutil
    pkgs.python310Packages.fpdf
    pkgs.python310Packages.pypdf2
    pkgs.python310Packages.openai

    # Extras
    pkgs.python310Packages.pandas
    pkgs.python310Packages.matplotlib
  ];
}


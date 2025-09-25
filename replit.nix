{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python3Packages.pip
    pkgs.python3Packages.flask
    pkgs.python3Packages.schedule
    pkgs.python3Packages.fpdf
    pkgs.python3Packages.pypdf2
  ];
}

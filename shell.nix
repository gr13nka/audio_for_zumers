with import <nixpkgs> { config.allowUnfree = true; };
with python310Packages;
stdenv.mkDerivation {
  name = "audio_zumers_shell";
  buildInputs = [
    # stdenv.cc.cc.lib
    pkgs.python310Full
    python310Packages.pip
    python310Packages.virtualenv
    ffmpeg
    # pkgs.python310Packages.tkinter
  ];
  #
  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
           pkgs.stdenv.cc.cc
     #     pkgs.zlib
    ]}
    export LD_LIBRARY_PATH=${stdenv.cc.cc.lib}/lib:/run/opengl-driver/lib/:$LD_LIBRARY_PATH
    # Проверяем, существует ли директория модели
    if [ ! -d "model" ]; then
      echo "Модель не найдена, скачиваю..."
      wget https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
      unzip vosk-model-small-ru-0.22.zip
      mv vosk-model-small-ru-0.22 model
    else
      echo "Модель уже существует, пропускаю скачивание."
    fi 

    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install -r requirements.txt
    export PATH = $PWD/venv/bin:$PATH
    export PYTHONPATH=venv/lib/python3.10/site-packages/:$PYTHONPATH
  '';


  postShellHook = ''
    ln -sf PYTHONPATH/* venv/lib/python3.10/site-packages
  '';
}












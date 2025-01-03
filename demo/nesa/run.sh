#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ "$(pwd)" =~ " " ]]; then echo This script relies on Miniconda which can not be silently installed under a path with spaces. && exit; fi

{ conda deactivate && conda deactivate && conda deactivate; } 2> /dev/null

OS_ARCH=$(uname -m)
case "${OS_ARCH}" in
    x86_64*)    OS_ARCH="x86_64";;
    arm64*)     OS_ARCH="aarch64";;
    aarch64*)     OS_ARCH="aarch64";;
    *)          echo "Unknown system architecture: $OS_ARCH! This script runs only on x86_64 or arm64" && exit
esac

INSTALL_DIR="$(pwd)/installer_files"
CONDA_ROOT_PREFIX="$(pwd)/installer_files/conda"
INSTALL_ENV_DIR="$(pwd)/installer_files/env"
MINICONDA_DOWNLOAD_URL="https://repo.anaconda.com/miniconda/Miniconda3-py311_24.7.1-0-Linux-${OS_ARCH}.sh"
conda_exists="F"

if "$CONDA_ROOT_PREFIX/bin/conda" --version &>/dev/null; then conda_exists="T"; fi

if [ "$conda_exists" == "F" ]; then
    echo "Downloading Miniconda from $MINICONDA_DOWNLOAD_URL to $INSTALL_DIR/miniconda_installer.sh"

    mkdir -p "$INSTALL_DIR"
    curl -L "$MINICONDA_DOWNLOAD_URL" > "$INSTALL_DIR/miniconda_installer.sh"

    chmod u+x "$INSTALL_DIR/miniconda_installer.sh"
    bash "$INSTALL_DIR/miniconda_installer.sh" -b -p $CONDA_ROOT_PREFIX

    echo "Miniconda version:"
    "$CONDA_ROOT_PREFIX/bin/conda" --version

    rm "$INSTALL_DIR/miniconda_installer.sh"
fi

if [ ! -e "$INSTALL_ENV_DIR" ]; then
    "$CONDA_ROOT_PREFIX/bin/conda" create -y -k --prefix "$INSTALL_ENV_DIR" python=3.11
fi

if [ ! -e "$INSTALL_ENV_DIR/bin/python" ]; then
    echo "Conda environment is empty."
    exit
fi

export PYTHONNOUSERSITE=1
unset PYTHONPATH
unset PYTHONHOME
export CUDA_PATH="$INSTALL_ENV_DIR"
export CUDA_HOME="$CUDA_PATH"

source "$CONDA_ROOT_PREFIX/etc/profile.d/conda.sh" # otherwise conda complains about 'shell not initialized' (needed when running in a script)
conda activate "$INSTALL_ENV_DIR"

python one_click.py $@

#!/usr/bin/env bash
set -eux -o pipefail
# Common utility functions for downstream testing scripts

setup_downstream_test() {
    local repo_name="$1"
    local repo_url="$2"
    

    
    if [[ ! -d "$repo_name" ]]; then
        git clone --depth=1 "$repo_url" "$repo_name"
    fi
    
    pushd "$repo_name" && trap popd EXIT
    git pull
}

setup_uv_environment() {
    local install_args="$*"
    
    uv venv
    uv pip install $install_args -e ../..
}

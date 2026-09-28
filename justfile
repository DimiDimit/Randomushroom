#!/usr/bin/env -S just --justfile


set unstable
set lists

set default-list := true
[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]
set dotenv-load


archs := ['i686', 'x86_64']

cargo-invocation := 'cargo +nightly -Z unstable-options -C plugin'
[windows]
cargo-xwin-invocation := cargo-invocation
[unix]
cargo-xwin-invocation := cargo-invocation + ' xwin'

[windows]
exe-runner := '&'
[unix]
exe-runner := 'wine'


export GAME_DIR := env('GAME_DIR', 'game')
export GAME_EXE := env('GAME_EXE', []) || if path_exists(GAME_DIR / 'wrapgame.exe') { 'wrapgame.exe' } else { 'mushroom_age.exe' }


[no-exit-message]
cargo *args:
    {{cargo-invocation}} {{args}}

cargo-arch arch command *args:
    {{cargo-invocation}} {{command}} --target {{arch}}-pc-windows-msvc {{args}}

cargo-all command *args: *(cargo-arch *archs command args)

build-arch arch *args:
    {{cargo-xwin-invocation}} build --target {{arch}}-pc-windows-msvc {{args}}

build *args: *(build-arch *archs args)

install-arch arch *args:
    {{cargo-xwin-invocation}} build -Z unstable-options --target {{arch}}-pc-windows-msvc --artifact-dir '{{absolute_path(GAME_DIR)}}' {{args}}
    -rm '{{GAME_DIR}}/randomushroom.dll.lib' '{{GAME_DIR}}/randomushroom-{{arch}}.asi' '{{GAME_DIR}}/randomushroom-{{arch}}.pdb'
    mv '{{GAME_DIR}}/randomushroom.dll' '{{GAME_DIR}}/randomushroom-{{arch}}.asi'
    mv '{{GAME_DIR}}/randomushroom.pdb' '{{GAME_DIR}}/randomushroom-{{arch}}.pdb'

install *args: *(install-arch *archs args)

[working-directory: GAME_DIR]
run *cargo-args: (install cargo-args)
    {{exe-runner}} '{{ absolute_path(join(GAME_DIR, GAME_EXE)) }}'

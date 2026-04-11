#!/bin/bash

HOOK_DESC="Docker compose CLI plugin symlink"
HOOK_ROLES="all"

docker_compose_plugin_source() {
  printf '%s\n' "/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose"
}

docker_compose_plugin_target() {
  printf '%s\n' "$HOME/.docker/cli-plugins/docker-compose"
}

hook_detect() {
  local source_path target_path
  source_path="$(docker_compose_plugin_source)"
  target_path="$(docker_compose_plugin_target)"
  [ -L "$target_path" ] && [ "$(readlink "$target_path")" = "$source_path" ]
}

hook_install() {
  local source_path target_path
  source_path="$(docker_compose_plugin_source)"
  target_path="$(docker_compose_plugin_target)"

  if [ ! -x "$source_path" ]; then
    warn "Docker compose plugin was not found at $source_path; skipping symlink setup."
    return 0
  fi

  mkdir -p "$(dirname "$target_path")"
  ln -sfn "$source_path" "$target_path"

  hook_detect
}

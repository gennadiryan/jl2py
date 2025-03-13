#!/bin/bash

function symbolic_links_to_hard_links {
  local dir="$1"

  if [[ ! -d "$dir" ]]; then
    echo "Error: '$dir' is not a directory."
    return 1
  fi

  find "$dir" -type l -print0 | while IFS= read -r -d $'\0' link_path; do
    local target="$(readlink "$link_path")"
    local target_abs="$(realpath "$(dirname "$link_path")/$target")" #Get absolute path

    if [[ -e "$target_abs" ]]; then
      rm "$link_path" # Remove the symbolic link
      ln "$target_abs" "$link_path" # Create the hard link
      echo "Symbolic link '$link_path' converted to hard link."
    else
      echo "Warning: Target '$target_abs' not found. Symbolic link '$link_path' was not converted."
    fi

  done
}

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

root_dir="$1"

symbolic_links_to_hard_links "$root_dir"
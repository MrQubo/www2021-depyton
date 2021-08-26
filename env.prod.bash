declare SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"


[[ -r "$SOURCE_DIR"/env.bash ]] || return 1
. "$SOURCE_DIR"/env.bash

declare -x CTF_PROD=1
declare -x CTF_LOGLEVEL=WARNING

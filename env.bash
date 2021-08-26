declare SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"


main() (

set -o errexit -o pipefail -o nounset -o noclobber

unset CDPATH


cd -- "$SOURCE_DIR"

if [[ ! -e venv/ ]]; then
	echo >&2 "Creating python's venv..."
	declare -r PYTHON="${PYTHON-python3}"
	"$PYTHON" -m venv venv --prompt www-py
	[[ -e venv/bin/activate ]] || return 1
	. venv/bin/activate
	pip install -U pip setuptools
	pip install -U -r requirements.txt

fi

if [[ ! -e venv/bin/ctf || ! -e venv/bin/ctf-complete.bash ]]; then
	echo >&2 "Adding ctf to venv..."
	ln -s --relative ctf.py venv/bin/ctf
	_CTF_COMPLETE=bash_source ctf >venv/bin/ctf-complete.bash
fi

)


main || return 1

[[ -r "$SOURCE_DIR"/venv/bin/activate ]] || return 1
[[ -r "$SOURCE_DIR"/venv/bin/ctf-complete.bash ]] || return 1

echo >&2 "Activating python's venv..."
. "$SOURCE_DIR"/venv/bin/activate || return 1

echo >&2 "Installing ctf completions..."
. "$SOURCE_DIR"/venv/bin/ctf-complete.bash || return 1

alias docker-compose='ctf docker-compose'

declare -x CTF_PROD=0
declare -x CTF_LOGLEVEL=WARNING

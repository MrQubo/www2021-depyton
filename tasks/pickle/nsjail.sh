#!/bin/bash

set -o errexit -o pipefail -o nounset


declare -a args=(
	-Ml --port 8000
	--user app --group app
	--cwd /app
	-R /bin -R /usr -R /lib -R /lib64
	-R /app
	--time_limit 0
	--verbose
)
if findmnt /sys/fs/cgroup | grep cgroup2; then
	args+=(
		--use_cgroupv2
		--cgroupv2_mount /sys/fs/cgroup
	)
else
	args+=(
		# These currently don't work with cgroups v2.
		--cgroup_cpu_ms_per_sec 20000
		--cgroup_mem_max "$((8 * 1024 * 1024))"
		--cgroup_pids_max 4
	)
	mkdir /sys/fs/cgroup/{cpu,memory,pids,net_cls}/NSJAIL
fi

exec nsjail "${args[@]}" -- "$@"

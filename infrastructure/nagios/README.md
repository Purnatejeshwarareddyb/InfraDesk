# Nagios monitoring for InfraDesk

**Nagios detects and reports. It does not repair anything.** Recovery is a documented, human-run
Ansible procedure (`infrastructure/ansible/playbooks/rollback.yml`, or the same file with
`--tags recover`). There is no automatic self-healing and no event handler.

## Files

| File | Purpose |
|---|---|
| `objects/commands.cfg` | command definitions (custom HTTP check + standard plugins) |
| `objects/hosts.cfg` | host `infradesk-host` (127.0.0.1), contact `infradesk-admin`, group |
| `objects/services.cfg` | 6 services (below) with intervals and retry settings |
| `scripts/check_infradesk_http.sh` | the custom plugin (POSIX sh + curl) |
| `scripts/install_or_validate.sh` | copy into Nagios, run `nagios -v`, reload only if valid |

Services: `/health` (expects `ok`), `/ready` (expects `ready`), TCP port 8080 (`check_tcp`),
disk `/` (`check_disk`), load (`check_load`), `dockerd` process (`check_procs`). The host check uses
`check_ping`; `check_dummy_up` is provided if ICMP is blocked. Change `8080` in `services.cfg` if your
`INFRADESK_PORT` differs.

Timing: `check_interval 1` (minute), `retry_interval 1`, `max_check_attempts 3`: a failure must be seen
3 times in a row before it becomes a HARD CRITICAL (about 3 minutes). Disk, load and process checks run
every 5 minutes.

Notifications: only what Nagios itself does, the log file and the web UI. The contact uses a no-op
command. For e-mail you would uncomment `email` in `hosts.cfg` and configure a mail command yourself.

## Plugin: exit codes and examples

```
check_infradesk_http.sh -H 127.0.0.1 -p 8080 -u /ready -e ready -w 2 -c 5
HTTP OK - http://127.0.0.1:8080/ready returned HTTP 200 in 0.004s | time=0.004s;2;5;0      (exit 0)
```

0 OK; 1 WARNING (slower than `-w`); 2 CRITICAL (refused, timeout, HTTP not 2xx, text missing, slower
than `-c`); 3 UNKNOWN (bad arguments, curl missing).

Tested for real against a fake local HTTP server; results:
OK, WARNING for a 1.5 s answer with `-w 1`, CRITICAL for refused connection / HTTP 500 / missing text /
slow beyond `-c`, UNKNOWN for bad port, bad path, `-w` greater than `-c`, unknown option.
Repeat it yourself:

```bash
cd infrastructure/nagios/scripts
python3 -m http.server 18080 --bind 127.0.0.1 &      # any local server
./check_infradesk_http.sh -p 18080 -u /; echo $?      # 0 (directory listing, HTTP 200)
./check_infradesk_http.sh -p 18080 -u /nope; echo $?  # 2 (HTTP 404)
./check_infradesk_http.sh -p 18081; echo $?           # 2 (connection refused)
./check_infradesk_http.sh -p abc; echo $?             # 3 (bad argument)
kill %1
```

## Install into Nagios Core (NOT RUN where this was written: no Nagios available)

Prerequisites: Nagios Core with the standard plugins; the sample `templates.cfg` (provides
`generic-host`, `generic-service`) and `timeperiods.cfg` (provides `24x7`) loaded.

```bash
# Source install layout (/usr/local/nagios):
sudo ./scripts/install_or_validate.sh -d /usr/local/nagios/etc/objects -p /usr/local/nagios/libexec
# add to /usr/local/nagios/etc/nagios.cfg once:   cfg_dir=/usr/local/nagios/etc/objects/infradesk
sudo ./scripts/install_or_validate.sh -d /usr/local/nagios/etc/objects -p /usr/local/nagios/libexec -r
```

Good result: `VALIDATION PASSED` (from `nagios -v`: "Total Warnings: 0, Total Errors: 0"), then the
reload. On a validation error the script prints `VALIDATION FAILED - not reloading` and exits 1.
Distro packages (`nagios4`) use `/etc/nagios4` and plugin dir `/usr/lib/nagios/plugins`; pass them with
`-d`, `-p`, `-c`. Without the nagios binary the script copies files and says `NOT validated`; it refuses `-r`.
Tested here: copying, backups (`*.cfg.bak-*`), the missing-binary path and refusal to reload.

## Demo: OK -> CRITICAL -> OK

1. Start the app: `make up`; open the Nagios web UI, service `InfraDesk /ready` is OK (green).
2. Stop it: `make down` (or `docker compose stop backend`). Within about 3 minutes the services
   `/health`, `/ready` and `TCP port 8080` go CRITICAL (after 3 retries; soft states first).
3. Recover as a human: `make up`, or `ansible-playbook playbooks/rollback.yml -K --tags recover`
   in `infrastructure/ansible`.
4. The services return to OK and Nagios logs the recovery.
You can force an immediate re-check from the web UI ("Re-schedule the next check").

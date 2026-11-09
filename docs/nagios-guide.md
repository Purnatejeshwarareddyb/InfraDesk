# Nagios guide

Full details: [`infrastructure/nagios/README.md`](../infrastructure/nagios/README.md).

## Role

**Monitoring.** Nagios Core runs checks on a schedule, tracks each service's state and shows it in its web interface and log.
InfraDesk is monitored through `/health` (is the process alive), `/ready` (can it reach the database), the TCP port, disk space, CPU load and the Docker daemon.
The application does not depend on Nagios; it runs fine without it.

## States

| State | Exit code | Meaning |
|---|---|---|
| OK | 0 | working normally |
| WARNING | 1 | working but outside the comfortable range (for the HTTP check: slower than the warning time) |
| CRITICAL | 2 | failed (connection refused, timeout, bad HTTP status, expected text missing, or slower than the critical time) |
| UNKNOWN | 3 | the check itself could not run (bad arguments) |

A failing check is first a *soft* state. After `max_check_attempts` (3) bad results in a row it becomes a *hard* state, which is when notifications would fire.
Checks run every minute, so a stopped application turns CRITICAL after about three minutes.

## Does Nagios repair anything?

**No.** It detects and reports. Recovery is a human decision: `make up`, or `ansible-playbook playbooks/rollback.yml -K --tags recover`.
There is no event handler and no self-healing, and the project does not claim any. Notifications go to the log file and web interface only; e-mail is not configured.

## Demonstration (OK, CRITICAL, OK)

1. Install the configuration: `infrastructure/nagios/scripts/install_or_validate.sh /etc/nagios4` (it copies the files, runs `nagios -v`, and refuses to reload if validation fails).
2. In the Nagios web interface show `InfraDesk /health` and `InfraDesk /ready` as **OK**.
3. Stop the application: `make down`. Watch the services go CRITICAL (soft, then hard after three checks).
4. Start it again: `make up`. The services return to **OK**.
5. Take a screenshot at each step as evidence.

## Status

Verified: the custom plugin `check_infradesk_http.sh` against a local fake HTTP server: OK (exit 0), WARNING for a slow answer (1), CRITICAL for a slow answer past the
critical time, HTTP 500, missing text and refused connection (2), UNKNOWN for bad arguments (3); `shellcheck` clean; the install script copies files and refuses
to reload without a validating Nagios. **Not verified**: `nagios -v` on the object files and the live OK, CRITICAL, OK demonstration (no Nagios in the build environment).
The object files use the sample templates `generic-host`, `generic-service` and `24x7`, which a standard Nagios installation provides.

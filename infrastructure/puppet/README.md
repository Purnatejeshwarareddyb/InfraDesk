# Puppet: InfraDesk host baseline

Puppet configures the Ubuntu **host**. It is used with **`puppet apply`** on the machine itself. This is
**not** a master/agent setup: there is no Puppet server, no certificates, no `puppet agent`.

## What the module `infradesk_host` manages

* packages: `ca-certificates curl git python3 sqlite3 docker.io` (+ `docker-compose-v2` on Ubuntu 24.04)
* group and user `infradesk` (uid/gid 10001, the same as the user inside the backend image, no login shell)
* directories `/opt/infradesk` (0755), `/opt/infradesk/data` and `/opt/infradesk/backups` (0750), `/etc/infradesk` (0750)
* `/etc/infradesk/infradesk.env` (0640 root:infradesk) rendered from an EPP template, contains the secret
* marker file `/etc/infradesk/MANAGED_BY_PUPPET`
* service `docker` running and enabled
* a systemd timer `infradesk-backup.timer` (daily 02:30, `Persistent=true`) running `/usr/local/sbin/infradesk-backup`

### Ownership table (no resource is managed by two tools)

| Layer | Tool | Owns |
|---|---|---|
| Host baseline | **Puppet** | everything listed above |
| Application deployment | Ansible | `/opt/infradesk/app` (Puppet never declares it), Compose project `infradesk` |
| Docker resources `infradesk-tf-*` | Terraform | its own network, volume, containers |

On Ubuntu 22.04 there is no `docker-compose-v2` package; install the Compose plugin from Docker's repository
yourself (`scripts/setup_ubuntu.sh` prints how). Run `sudo apt-get update` before the first apply.

## NOT RUN where this was written

`puppet` could not be installed there (no package available through the allowed network). `puppet parser
validate`, `puppet apply --noop` and real applies were **not run**. The manifests were written carefully but
are untested. Run the steps below on an Ubuntu machine with Puppet (`sudo apt-get install puppet-agent` from
Puppet's repository, or `sudo apt-get install puppet` from Ubuntu universe, version 7 or newer).

## Supplying the secret (never in this repository)

The class has no default for `secret_key`; it stops with an error if none is given. Two ways:

```bash
# 1. Environment variable -> fact (simplest)
read -rs -p "SECRET_KEY: " SECRET_KEY; echo
# 2. Hiera: put "infradesk_host::secret_key: <value>" in a hiera data file OUTSIDE the repo (ideally hiera-eyaml)
#    and run puppet apply with --hiera_config=/path/to/hiera.yaml
```

The value is wrapped in `Sensitive`, `show_diff` is off, and the file is mode 0640, so it does not appear in
Puppet output. (A process list can briefly show environment values on a shared machine; do this on your own laptop.)

## Demonstration

Run from the repository root. `PM` below is the module path.

```bash
PM=infrastructure/puppet/modules
SITE=infrastructure/puppet/manifests/site.pp

# 1. Syntax (no changes). Good result: no output, exit code 0
puppet parser validate $SITE $PM/infradesk_host/manifests/init.pp
puppet epp validate $PM/infradesk_host/templates/*.epp

# 2. Dry run. Good result: lists what WOULD change ("Notice: ... would have been created"), changes nothing
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --noop --modulepath=$PM $SITE

# 3. Real apply. Good result: "Applied catalog in N seconds"
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=$PM $SITE

# 4. Idempotence: apply AGAIN. Good result: no "Notice: /Stage[main]..." lines, i.e. no changes
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=$PM $SITE

# 5. Drift correction (file)
echo "# hand edit" | sudo tee -a /etc/infradesk/infradesk.env
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=$PM $SITE
#    good: the file content is replaced (a "content changed" notice, values hidden because it is Sensitive)

# 6. Drift correction (service)
sudo systemctl stop docker
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=$PM $SITE
systemctl is-active docker      # good: active  (Puppet: "ensure changed 'stopped' to 'running'")
```

Check the timer: `systemctl list-timers infradesk-backup.timer`. Run a backup by hand once the application has been
deployed by Ansible: `sudo systemctl start infradesk-backup.service` and look into `/opt/infradesk/backups`.

Notes for the viva: `puppet apply` is declarative (describes the end state), and idempotent because each resource
is only changed when it differs; the `exec` that reloads systemd is `refreshonly`, so it runs only when a unit
file changed.

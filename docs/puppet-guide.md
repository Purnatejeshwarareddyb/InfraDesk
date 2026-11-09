# Puppet guide

Full details: [`infrastructure/puppet/README.md`](../infrastructure/puppet/README.md).

## Role

Puppet is **configuration management** for the Ubuntu host. You describe the desired state (packages present, user and folders exist, a
file has certain content and mode, the Docker service is running and enabled, a backup timer exists) and Puppet makes the machine match it.
It does **not** deploy the application (Ansible) and does **not** touch the `infradesk-tf-*` Docker resources (Terraform).

Mode used: **`puppet apply`** on the machine itself with a local module. This demonstrates manifests, resources, templates, idempotence and
drift correction. It is **not** a Puppet master/agent architecture, and the project makes no such claim.

## What the module manages

Packages (curl, git, python3, sqlite3, ca-certificates and Docker), the `infradesk` group and user, `/opt/infradesk`, `/opt/infradesk/data`,
`/opt/infradesk/backups`, `/etc/infradesk/infradesk.env` (EPP template, mode 0640, contains the secret passed as a fact or Hiera value, never
stored in the repository), a marker file, the Docker service, and a systemd service and timer that run a daily backup.

## Demonstration

```bash
PM=infrastructure/puppet/modules; SITE=infrastructure/puppet/manifests/site.pp
puppet parser validate $SITE $PM/infradesk_host/manifests/init.pp      # syntax: no output means OK
puppet epp validate $PM/infradesk_host/templates/*.epp
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --noop --modulepath=$PM $SITE   # what WOULD change
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=$PM $SITE          # first run: many changes
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=$PM $SITE          # second run: no changes (idempotence)
# drift: change a managed file or stop Docker, then apply again
echo "# hand edit" | sudo tee -a /etc/infradesk/infradesk.env ; sudo systemctl stop docker
sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=$PM $SITE          # file and service restored
```

Good output: the first apply lists notices such as `Created`, `ensure changed 'stopped' to 'running'`; the second shows only
`Applied catalog in ... seconds` with no resource changes; after the drift Puppet reports the file content and the service state corrected.

## Status

Written, **not executed** (Puppet was not obtainable when the project was built). Run the commands above, keep the output, and fix any
package-name differences on your Ubuntu release.

## Viva one-liners

*Idempotence*: applying the same manifest again changes nothing once the state matches. *Drift*: the real state departs from the declared
state (a hand edit); the next run corrects it. *Declarative*: you state the result, not the steps.

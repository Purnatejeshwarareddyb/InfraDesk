# @summary Host baseline for InfraDesk on Ubuntu (applied with `puppet apply`, no master/agent).
#
# Puppet owns ONLY the host: packages, the infradesk user/group, /opt/infradesk (+ data, backups),
# /etc/infradesk, the docker service, the daily backup timer.
# Puppet does NOT touch /opt/infradesk/app (Ansible) or any Docker container/volume/network
# (Compose via Ansible, or Terraform). Two tools must never manage the same resource.
#
# @param secret_key    Application SECRET_KEY. Sensitive, no default: supplied via Hiera or the
#                      FACTER_infradesk_secret_key environment variable (see manifests/site.pp).
# @param environment   Application ENVIRONMENT value (production blocks the demo seed script).
# @param web_port      Host port of the web interface (INFRADESK_PORT).
# @param cookie_secure Set true only when served over HTTPS.
# @param access_token_minutes Session lifetime in minutes.
# @param base_dir      Root directory for InfraDesk on the host.
# @param backup_time   systemd OnCalendar expression for the daily backup.
# @param retention_days Backups older than this are deleted by the backup job.
# @param manage_docker Install and run docker.io. Set false if Docker Desktop/CE is managed elsewhere.
# @param service_uid   uid/gid of the infradesk account; 10001 matches the user inside the backend image.
class infradesk_host (
  Optional[Sensitive[String[32]]] $secret_key = undef,
  String                          $environment = 'production',
  Integer[1024, 65535]            $web_port = 8080,
  Boolean                         $cookie_secure = false,
  Integer[5, 1440]                $access_token_minutes = 60,
  Pattern[/^\/.+/]              $base_dir = '/opt/infradesk',
  String                          $backup_time = '*-*-* 02:30:00',
  Integer[1]                      $retention_days = 14,
  Boolean                         $manage_docker = true,
  Integer                         $service_uid = 10001,
) {
  # Refuse to continue without a secret; the error names the two safe ways to supply it.
  if $secret_key == undef {
    fail('infradesk_host: no secret_key. Set Hiera key infradesk_host::secret_key or run with FACTER_infradesk_secret_key=... (see README).')
  }

  $app_dir    = "${base_dir}/app"      # owned by Ansible, only referenced here
  $data_dir   = "${base_dir}/data"
  $backup_dir = "${base_dir}/backups"
  $config_dir = '/etc/infradesk'
  $env_file   = "${config_dir}/infradesk.env"

  # --- 1. Packages ---------------------------------------------------------------------------
  # `docker-compose-v2` (the `docker compose` plugin) exists from Ubuntu 24.04; on 22.04 install
  # the Compose plugin from Docker's own repository (see README).
  $base_packages = ['ca-certificates', 'curl', 'git', 'python3', 'sqlite3']
  if $manage_docker {
    if versioncmp($facts['os']['release']['major'], '24.04') >= 0 {
      $docker_packages = ['docker.io', 'docker-compose-v2']
    } else {
      $docker_packages = ['docker.io']
    }
  } else {
    $docker_packages = []
  }
  $all_packages = $base_packages + $docker_packages
  package { $all_packages:
    ensure => installed,
  }

  # --- 2. Service account --------------------------------------------------------------------
  group { 'infradesk':
    ensure => present,
    gid    => $service_uid,
    system => true,
  }
  user { 'infradesk':
    ensure     => present,
    uid        => $service_uid,
    gid        => 'infradesk',
    system     => true,
    shell      => '/usr/sbin/nologin',
    home       => $base_dir,
    managehome => false,
    comment    => 'InfraDesk service account',
    require    => Group['infradesk'],
  }

  # --- 3. Directories ------------------------------------------------------------------------
  file { $base_dir:
    ensure  => directory,
    owner   => 'infradesk',
    group   => 'infradesk',
    mode    => '0755',
    require => User['infradesk'],
  }
  file { [$data_dir, $backup_dir]:
    ensure  => directory,
    owner   => 'infradesk',
    group   => 'infradesk',
    mode    => '0750',   # only the service account and root can read data and backups
    require => File[$base_dir],
  }
  file { $config_dir:
    ensure  => directory,
    owner   => 'root',
    group   => 'infradesk',
    mode    => '0750',
    require => Group['infradesk'],
  }

  # --- 4. Managed configuration file (contains the secret) ------------------------------------
  # Sensitive(...) hides the content from Puppet output and diffs. Mode 0640: root + group only.
  file { $env_file:
    ensure    => file,
    owner     => 'root',
    group     => 'infradesk',
    mode      => '0640',
    content   => Sensitive(epp('infradesk_host/infradesk.env.epp', {
      'secret_key'           => $secret_key,
      'environment'          => $environment,
      'web_port'             => $web_port,
      'cookie_secure'        => $cookie_secure,
      'access_token_minutes' => $access_token_minutes,
      'app_dir'              => $app_dir,
      'backup_dir'           => $backup_dir,
      'retention_days'       => $retention_days,
    })),
    show_diff => false,
    require   => File[$config_dir],
  }

  # Marker showing the host is under Puppet control (static text -> stays idempotent).
  file { "${config_dir}/MANAGED_BY_PUPPET":
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => epp('infradesk_host/managed_marker.epp', { 'env_file' => $env_file }),
    require => File[$config_dir],
  }

  # --- 5. Docker service ---------------------------------------------------------------------
  if $manage_docker {
    service { 'docker':
      ensure  => running,
      enable  => true,
      require => Package['docker.io'],
    }
  }

  # --- 6. Daily backup via a systemd timer ---------------------------------------------------
  file { '/usr/local/sbin/infradesk-backup':
    ensure => file,
    owner  => 'root',
    group  => 'root',
    mode   => '0750',
    source => 'puppet:///modules/infradesk_host/infradesk-backup.sh',
  }
  file { '/etc/systemd/system/infradesk-backup.service':
    ensure => file,
    owner  => 'root',
    group  => 'root',
    mode   => '0644',
    source => 'puppet:///modules/infradesk_host/infradesk-backup.service',
    notify => Exec['infradesk-systemd-reload'],
  }
  file { '/etc/systemd/system/infradesk-backup.timer':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => epp('infradesk_host/infradesk-backup.timer.epp', { 'backup_time' => $backup_time }),
    notify  => Exec['infradesk-systemd-reload'],
  }
  # Runs only when a unit file changed (refreshonly), so a second apply reports nothing.
  exec { 'infradesk-systemd-reload':
    command     => 'systemctl daemon-reload',
    path        => ['/bin', '/usr/bin'],
    refreshonly => true,
  }
  service { 'infradesk-backup.timer':
    ensure  => running,
    enable  => true,
    require => [
      Exec['infradesk-systemd-reload'],
      File['/usr/local/sbin/infradesk-backup', '/etc/systemd/system/infradesk-backup.service'],
    ],
  }
}

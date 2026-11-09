# Entry point for `puppet apply` (there is NO Puppet server in this project).
#
#   sudo env FACTER_infradesk_secret_key="$SECRET_KEY" \
#     puppet apply --modulepath=infrastructure/puppet/modules infrastructure/puppet/manifests/site.pp
#
# Where the secret comes from (never from this repository):
#   1. Hiera key   infradesk_host::secret_key   (use hiera-eyaml or a file outside the repo), or
#   2. the environment variable FACTER_infradesk_secret_key, which Facter turns into the fact
#      $facts['infradesk_secret_key'].
$secret = lookup('infradesk_host::secret_key', Optional[String], 'first', $facts['infradesk_secret_key'])

class { 'infradesk_host':
  # Sensitive[...] keeps the value out of logs and reports. undef -> the class stops with a clear error.
  secret_key => $secret ? {
    undef   => undef,
    default => Sensitive($secret),
  },
  # Override other defaults here, for example:
  # web_port     => 8080,
  # backup_time  => '*-*-* 02:30:00',
}

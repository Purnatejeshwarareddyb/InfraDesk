# Terraform-owned Docker resources for InfraDesk.
# Everything here is prefixed "infradesk-tf-" so it can never clash with the Docker Compose
# stack (infradesk-net, infradesk-data, container names infradesk-backend-1 ...).

locals {
  prefix      = "infradesk-tf"
  volume_name = "${local.prefix}-data"
}

# Dedicated network: the containers see each other by name, nothing else joins it.
resource "docker_network" "net" {
  name   = "${local.prefix}-net"
  driver = "bridge"
}

# Named volume holding the SQLite database (/data in the backend container).
# count = 0 when the volume is managed outside Terraform (manage_data_volume = false).
resource "docker_volume" "data" {
  count = var.manage_data_volume ? 1 : 0
  name  = local.volume_name
}

resource "docker_container" "backend" {
  name         = "${local.prefix}-backend"
  image        = var.backend_image
  restart      = "unless-stopped"
  memory       = var.backend_memory_mb
  must_run     = true
  wait         = true # `terraform apply` returns only when the healthcheck passes
  wait_timeout = 120

  # Same variables as docker-compose.yml.
  env = [
    "SECRET_KEY=${var.secret_key}",
    "DATABASE_URL=sqlite:////data/infradesk.db",
    "ENVIRONMENT=${var.environment}",
    "COOKIE_SECURE=${var.cookie_secure}",
    "ACCESS_TOKEN_MINUTES=${var.access_token_minutes}",
    "CORS_ORIGINS=http://localhost:${var.web_port}",
  ]

  security_opts = ["no-new-privileges:true"]
  capabilities {
    drop = ["ALL"]
  }

  # The nginx config proxies to the host name "backend", so give the container that alias.
  networks_advanced {
    name    = docker_network.net.name
    aliases = ["backend"]
  }

  volumes {
    volume_name    = local.volume_name
    container_path = "/data"
  }

  healthcheck {
    test         = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"]
    interval     = "30s"
    timeout      = "5s"
    retries      = 3
    start_period = "20s"
  }

  # Make sure the volume exists before the container starts (no-op when it is unmanaged).
  depends_on = [docker_volume.data]
}

resource "docker_container" "web" {
  name         = "${local.prefix}-web"
  image        = var.frontend_image
  restart      = "unless-stopped"
  memory       = var.web_memory_mb
  must_run     = true
  wait         = true
  wait_timeout = 60

  security_opts = ["no-new-privileges:true"]
  capabilities {
    drop = ["ALL"]
  }

  ports {
    internal = 8080
    external = var.web_port
    ip       = var.bind_ip
  }

  networks_advanced {
    name = docker_network.net.name
  }

  healthcheck {
    test         = ["CMD", "wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/nginx-health"]
    interval     = "30s"
    timeout      = "3s"
    retries      = 3
    start_period = "5s"
  }

  # Start the web container only after the backend is healthy.
  depends_on = [docker_container.backend]
}

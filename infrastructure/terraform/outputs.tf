output "url" {
  description = "Where to open InfraDesk."
  value       = "http://localhost:${var.web_port}"
}

output "backend_container" {
  description = "Name of the backend container."
  value       = docker_container.backend.name
}

output "web_container" {
  description = "Name of the web container."
  value       = docker_container.web.name
}

output "network_name" {
  description = "Name of the Terraform-owned network."
  value       = docker_network.net.name
}

output "data_volume" {
  description = "Name of the data volume (managed by Terraform only when manage_data_volume = true)."
  value       = local.volume_name
}

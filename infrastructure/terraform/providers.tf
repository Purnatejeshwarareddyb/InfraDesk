# The Docker provider talks to the Docker daemon through its API socket.
provider "docker" {
  host = var.docker_host
}

# Which Terraform and which provider versions this configuration is written for.
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0" # any 3.x release, never 4.x (a major version may break the configuration)
    }
  }
}

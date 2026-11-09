# All inputs of the configuration. Values come from terraform.tfvars (copy the .example file)
# or from environment variables such as TF_VAR_secret_key.

variable "docker_host" {
  description = "Docker daemon endpoint. Linux/WSL: unix:///var/run/docker.sock. Windows Docker Desktop (native Terraform): npipe:////./pipe/docker_engine"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "backend_image" {
  description = "Backend image built with `docker build -f docker/backend.Dockerfile -t infradesk-backend:latest .` (same tag Compose builds)."
  type        = string
  default     = "infradesk-backend:latest"
}

variable "frontend_image" {
  description = "Web image built with `docker build -f docker/frontend.Dockerfile -t infradesk-frontend:latest .`"
  type        = string
  default     = "infradesk-frontend:latest"
}

variable "web_port" {
  description = "Host port for the web interface. Default 8081 so it never collides with Docker Compose (8080)."
  type        = number
  default     = 8081

  validation {
    condition     = var.web_port >= 1024 && var.web_port <= 65535
    error_message = "web_port must be between 1024 and 65535."
  }
}

variable "bind_ip" {
  description = "Host address the port is published on. 127.0.0.1 = this machine only; 0.0.0.0 = whole network."
  type        = string
  default     = "127.0.0.1"
}

variable "secret_key" {
  description = "Application SECRET_KEY (at least 32 characters). No default on purpose: pass it with TF_VAR_secret_key or terraform.tfvars (git-ignored)."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.secret_key) >= 32 && !startswith(lower(var.secret_key), "change-me")
    error_message = "secret_key must be at least 32 characters and must not start with 'change-me'."
  }
}

variable "environment" {
  description = "Application ENVIRONMENT value."
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "production", "test"], var.environment)
    error_message = "environment must be development, production or test."
  }
}

variable "cookie_secure" {
  description = "Set to true only when the site is served over HTTPS."
  type        = bool
  default     = false
}

variable "access_token_minutes" {
  description = "Session lifetime in minutes (5 to 1440)."
  type        = number
  default     = 60
}

variable "backend_memory_mb" {
  description = "Memory limit of the backend container in MB."
  type        = number
  default     = 512
}

variable "web_memory_mb" {
  description = "Memory limit of the web container in MB."
  type        = number
  default     = 128
}

variable "manage_data_volume" {
  description = "true: Terraform creates and owns the volume infradesk-tf-data (it is deleted by a full destroy). false: Terraform only USES an existing volume with that name and never deletes it (create it first with `docker volume create infradesk-tf-data`)."
  type        = bool
  default     = true
}

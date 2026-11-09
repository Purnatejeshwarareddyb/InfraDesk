# Terraform guide

Full commands and notes are in [`infrastructure/terraform/README.md`](../infrastructure/terraform/README.md). This page is the
short version for understanding and for the viva.

## Role

Terraform is **Infrastructure as Code** for the *local Docker* layer: it declares a network, a data volume and two containers
(`infradesk-tf-backend`, `infradesk-tf-web`) using the `kreuzwerker/docker` provider. It does not create a cloud server or a
virtual machine. It is its own deployment mode with different names and port **8081**, so it never collides with Compose or
Ansible (port 8080).

## Files

`versions.tf` (Terraform and provider version constraints), `providers.tf` (Docker host), `variables.tf` (image names, tags, ports,
sensitive `secret_key`, `manage_data_volume`), `main.tf` (resources), `outputs.tf` (URL, container names), `terraform.tfvars.example`.

## Workflow

```bash
make build                                         # Terraform uses the images infradesk-backend:latest and infradesk-frontend:latest
make tf-init                                       # downloads the provider once; creates .terraform.lock.hcl (commit it)
make tf-validate                                   # terraform fmt -check and validate
export TF_VAR_secret_key="$SECRET_KEY"
make tf-plan                                       # shows what would be created
make tf-apply                                      # type yes
curl -s localhost:8081/health
make tf-destroy                                    # removes containers and network, KEEPS the data volume
```

`terraform plan` first, `apply` second: the plan is a preview of the difference between the declared and the real state; the state file
(`terraform.tfstate`, git-ignored) records what Terraform manages. Run `apply` twice: the second run reports no changes (declarative and idempotent).

## Status of this part

Written and reviewed, **not executed** (no Terraform binary was available when the project was built). Run `terraform fmt`, `init`, `validate`,
`plan`, `apply` yourself, commit the generated `.terraform.lock.hcl`, and capture the output as evidence. If `fmt -check` complains, run `terraform fmt` once.
`terraform init` needs the internet the first time; see [offline-operation.md](offline-operation.md) for the provider mirror.

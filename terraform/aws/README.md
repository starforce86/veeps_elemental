# Overview

This code creates the network, container registry, loadbalancer, and aws's managed k8s, ecs fargate service. 
ECS is configured to use whichever container is pushed that has the "latest" tag

# How to run this code

It will deploy to the account setup for the aws cli called 'default' or 'profile' set it

```bash
clone this repo
terraform init
terraform validate
terraform plan
terraform apply --auto-approve
```

## Quick Destroy

```bash
terraform destroy --auto-approve
```

## Notes

- clone this repo
- use terraform __init__ command prepare your working directory for other commands
- terraform __validate__ command check whether the configuration is valid
- terraform __plan__ command show changes required by the current configuration
- terraform __apply__ create or update infrastructure
- Alternate command : terraform apply -auto-approve
- terraform __destroy__ destroy previously-created infrastructure
- Alternate command : terraform destroy -auto-approve
- terraform __fmt__ reformat your configuration in the standard style
- tfsec : runs standard security checks on terraform code


## Tools install 
```
brew install terraform@1.2
brew install awscli
brew install tfsec
```

## MFA
Script to get session token, needed to use cli with mfa
https://github.com/asagage/aws-mfa-script


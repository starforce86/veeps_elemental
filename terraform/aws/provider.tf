provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      createdby = "terraform"
      source    = "veeps_elemental"
    }
  }
}

terraform {
  backend "s3" {
    bucket = "veeps-stg-tf-state"
    key    = "terraform/veepsapiinfra.tfstate"
    region = "us-east-1"
  }
}

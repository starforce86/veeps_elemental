variable "aws_region" {
  type        = string
  description = "aws region to deploy to"
  default     = "us-east-1"
}

# vpc
variable "vpc_cidr_block" {
  type        = string
  description = "the cidr block to use for the VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "the list of availability zones to use"
  default = [
    "us-east-1a",
    "us-east-1b",
    "us-east-1c",
  ]
}

variable "subnet_tier_cidrs_newbits" {
  type        = number
  description = "the newbits to use when creating the subnets for the subnet tiers"
  default     = 3
}

variable "public_subnets_cidr_newbits" {
  type        = number
  description = "the newbits to use for creating subnets for the public subnets"
  default     = 7
}

variable "app_subnets_cidr_newbits" {
  type        = number
  description = "the newbits to use for creating subnets for the app subnets"
  default     = 2
}

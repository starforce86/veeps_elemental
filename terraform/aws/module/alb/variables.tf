variable "vpc_id" {
  type        = string
  description = "ID of a VPC in which to deploy ALB"

  validation {
    condition     = can(regex("^[0-9a-z\\-]+[0-9a-z]$", var.vpc_id))
    error_message = "\"vpc_id\" can only contain lower case letters, numbers, and hyphens!"
  }
}

variable "public_subnets" {
  type        = list(string)
  description = "List of subnet IDs in which to deploy the ALB which will accept traffic"
  default     = []
}

variable "cidr_blocks" {
  type        = list(string)
  description = "Whitelist of cidr blocks that can access the apis"
  default     = []
}

variable "alb_name" {
  type        = string
  description = "Name of this alb, must be unique."
  default     = "public" # public as in web facing. Still locked down by whitelist
}
variable "aurora_cluster_name" {
  type        = string
  description = "Name of the RDS Cluster"
}

variable "database_name" {
  type        = string
  description = "name of the database"
}

variable "username" {
  type        = string
  description = "name of the admin user created in the database"
}

variable "vpc_id" {
  type        = string
  description = "ID of a VPC in which to deploy the Database cluster"

  validation {
    condition     = can(regex("^[0-9a-z\\-]+[0-9a-z]$", var.vpc_id))
    error_message = "\"vpc_id\" can only contain lower case letters, numbers, and hyphens!"
  }
}

variable "private_subnets" {
  type        = list(string)
  description = "Array of IDs of Subnets to put database cluster on, example [\"subnet-9876543210987\",\"subnet-1234567890123\"]"
}

variable "engine_version" {
  type        = number
  description = "Version of postgres engine to use"
  default     = 14.3
}

variable "min_capacity" {
  type        = number
  description = "Minimum ACUs, Each ACU is a combination of approximately 2 gibibytes (GiB) of memory, corresponding CPU, and networking. Floor is 2"
  default     = 2
}

variable "max_capacity" {
  type        = number
  description = "Maximum ACUs, Each ACU is a combination of approximately 2 gibibytes (GiB) of memory, corresponding CPU, and networking. Max is 128"
  default     = 2
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "CIDR Blocks of resources allowed to access database, if on same subnet"
  default     = ["10.0.0.0/8"]
}


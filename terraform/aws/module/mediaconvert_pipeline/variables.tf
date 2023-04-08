variable "function_name" {
  type        = string
  description = "Name of Lambda Function"
}

variable "description" {
  type        = string
  description = "Description"
  default     = ""
}

variable "runtime" {
  type        = string
  description = "Runtime"
}

variable "handler" {
  type        = string
  description = "Handler Function"
}

variable "memory_size" {
  type        = number
  description = "Memory (MB)"
  default     = 128
}

variable "timeout" {
  type        = number
  description = "Timeout (Seconds)"
  default     = 30
}

variable "envs" {
  type        = map(any)
  description = "Environment Variables"
  default     = {}
}

variable "common_tags" {
  type        = map(any)
  description = "Tags"
  default     = {}
}

variable "input_bucket_name" {
  type        = string
  description = "Name of Input S3 Bucket"
}

variable "output_bucket_name" {
  type        = string
  description = "Name of Output S3 Bucket"
}

variable "lambda_bucket_name" {
  type        = string
  description = "Name of Lambda S3 Bucket"
}

variable "mediapackage_group_name" {
  type        = string
  description = "Name of the mediapackage group to create"
  default     = "VOD"
}

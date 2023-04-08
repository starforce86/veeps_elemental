variable "vpc_id" {
  type        = string
  description = "ID of a VPC in which to deploy the ECS cluster, ALB, etc."

  validation {
    condition     = can(regex("^[0-9a-z\\-]+[0-9a-z]$", var.vpc_id))
    error_message = "\"vpc_id\" can only contain lower case letters, numbers, and hyphens!"
  }
}

variable "private_subnets" {
  type        = list(string)
  description = "List of subnet IDs in which to deploy the ALB which will accept traffic going to the ECS cluster."
  default     = []
}

variable "public_subnets" {
  type        = list(string)
  description = "List of subnet IDs in which to deploy the ALB which will accept traffic going to the ECS cluster."
  default     = []
}
variable "ecs_service_desired_task_count" {
  type        = number
  description = "how many copies of the veepsapi to run"
  default     = 2
}

variable "repository_url" {
  type        = string
  description = "url of the ecr repository"

}

variable "alb_arn" {
  type = string
}

variable "alb_sg_id" {
  type        = string
  description = "ID of the sg used for the alb, to use for ecs."
}

variable "service_name" {
  type        = string
  description = "Name of the cluster, service, and task"
}

variable "database_secret" {
  type        = string
  description = "AWS Secret manager arn that has database credentials"
  default     = ""
}

variable "input_bucket_name" {
  type        = string
  description = "Name of Input S3 Bucket"
}

variable "output_bucket_name" {
  type        = string
  description = "Name of Output S3 Bucket"
}

variable "clip_bucket_name" {
  type        = string
  description = "Name of the S3 Bucket that the livestreams send their clips to"
}

variable "lambda_to_trigger_to_convert" {
  type        = string
  description = "Name of the lambda that kicks off mediaconvert"
  default     = "vod-s3-trigger"
}

variable "callback_sns_arn" {
  type        = string
  description = "Name of the SNS topic to listen to, for updates from eventbridge"
  default     = "Cloudwatch-hook"
}

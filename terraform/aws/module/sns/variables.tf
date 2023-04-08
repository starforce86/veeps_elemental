variable "sns_topic_name" {
  type        = string
  description = "Name of this SNS, must be unique."
}

variable "input_bucket_name" {
  type        = string
  description = "Name of Input S3 Bucket"
}
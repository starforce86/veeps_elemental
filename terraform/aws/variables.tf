variable "env" {
  type        = string
  description = "Short name of AWS environment that is being targeted. Used for naming resources, and environemnt variable to apps. (staging/production)"
  default     = "staging"
}

variable "devops_repo" {
  type        = string
  description = "Devops Github Organization, Repo, and ref (org/repo/*)"
}

variable "max_medialive_playouts" {
  type        = number
  description = "The maximum number of configured playouts. This variable is used for requesting AWS service limit increases"
  default     = 20
}

variable "max_medialive_live_inputs" {
  type        = number
  description = "The maximum number of live inputs for each playout (MediaLive Livestream). This variable is used for requesting AWS service limit increases"
  default     = 10
}

variable "estimated_max_live_viewers" {
  type        = number
  description = "The maximum number of viewers of the biggest live show. This number is used to calculate AWS service limits"
  default     = 50000
}

variable "bitrate_of_uhd" {
  type        = number
  description = "Mbps bitrate of uhd content. This number is used to calculate AWS service limits. Round up to the nearest whole number"
  default     = 23
}

variable "max_static_inputs_per_playout" {
  type        = number
  description = "The maximum number of static assets (mp4 or hls) to be used per liveshow."
  default     = 100
}

variable "max_concurrent_clips_per_liveshow" {
  type        = number
  description = "The maximum number of Mediapackage Harvest jobs that can be ran at the same time, per show"
  default     = 4
}

variable "service_limit_buffer" {
  type        = number
  description = "The number of extra resorouces to ask for when making AWS service limit increase requests, where applicable"
  default     = 5
}

variable "max_number_vod_assets" {
  type        = number
  description = "The Maximum number of VOD assets. Used to request an AWS service limit increase reqeust for Mediapackage-VOD"
  default     = 10000 #10k is the AWS default service limit for mediapackage-vod
}

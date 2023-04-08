##
## Terraform automatically makes a service limit increase request on your behalf if the current limit is less than the desired limit
##
## https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/servicequotas_service_quota


locals {
  #Just for math 
  elastic_ips_per_medialive_channel = 2
  outputs_per_mediaconnect          = 2
  conversion_Mbps_to_Gbps           = 0.001

  #Limits
  max_vpcs                                = var.max_medialive_playouts + var.service_limit_buffer
  max_elastic_ip                          = var.max_medialive_playouts * local.elastic_ips_per_medialive_channel + var.service_limit_buffer
  max_mediaconnect_flows                  = var.max_medialive_playouts * var.max_medialive_live_inputs + var.service_limit_buffer
  max_mediaconnect_outputs                = var.max_medialive_playouts * var.max_medialive_live_inputs * local.outputs_per_mediaconnect + var.service_limit_buffer
  max_medialive_vpc_inputs                = local.max_mediaconnect_outputs + var.service_limit_buffer
  max_medialive_hevc_channels             = var.max_medialive_playouts + var.service_limit_buffer
  max_medialive_pull_inputs               = var.max_medialive_playouts * var.max_static_inputs_per_playout
  max_medialive_uhd_channels              = var.max_medialive_playouts + var.service_limit_buffer
  max_medialive_channels                  = var.max_medialive_playouts * var.max_medialive_live_inputs + var.max_medialive_playouts + var.service_limit_buffer # Normal channel, and preview channel per input
  max_medialive_push_input                = var.max_medialive_playouts * var.max_medialive_live_inputs + var.service_limit_buffer
  max_mediapackage_channels               = var.max_medialive_playouts + var.service_limit_buffer
  max_mediapackage_vod_assets             = var.max_number_vod_assets
  max_mediapackage_con_clipping           = var.max_medialive_playouts * var.max_concurrent_clips_per_liveshow
  max_data_transfer_per_distribution_Gbps = var.estimated_max_live_viewers * var.bitrate_of_uhd * local.conversion_Mbps_to_Gbps * 2 #doubling for burst traffic
}

resource "aws_servicequotas_service_quota" "vpc_per_region" {
  quota_code   = "L-F678F1CE"
  service_code = "vpc"
  value        = local.max_vpcs
}

# The default limit is now "-1", which is infinite. Causes a new request on every apply. No longer needed. 
#resource "aws_servicequotas_service_quota" "elastic_ip_per_region" {
#  quota_code   = "L-CEED54BB"
#  service_code = "ec2"
#  value        = local.max_elastic_ip
#}

resource "aws_servicequotas_service_quota" "mediaconnect_flows" {
  quota_code   = "L-A99016A8"
  service_code = "mediaconnect"
  value        = local.max_mediaconnect_flows
}

### NOT ADJUSTABLE, Have to email aws team for manual override 
#resource "aws_servicequotas_service_quota" "mediaconnect_outputs" {
#  quota_code   = "L-CB77E87E"
#  service_code = "mediaconnect"
#  value        = local.max_mediaconnect_outputs
#}

resource "aws_servicequotas_service_quota" "medialive_vpc_inputs" {
  quota_code   = "L-68E02936"
  service_code = "medialive"
  value        = local.max_medialive_vpc_inputs
}

resource "aws_servicequotas_service_quota" "medialive_hevc_channels" {
  quota_code   = "L-05A796F2"
  service_code = "medialive"
  value        = local.max_medialive_hevc_channels
}

resource "aws_servicequotas_service_quota" "medialive_pull_inputs" {
  quota_code   = "L-4D7207DE"
  service_code = "medialive"
  value        = local.max_medialive_pull_inputs
}

resource "aws_servicequotas_service_quota" "medialive_uhd_channels" {
  quota_code   = "L-DDE858F0"
  service_code = "medialive"
  value        = local.max_medialive_uhd_channels
}

resource "aws_servicequotas_service_quota" "medialive_channels" {
  quota_code   = "L-D1AFAF75"
  service_code = "medialive"
  value        = local.max_medialive_channels
}

resource "aws_servicequotas_service_quota" "medialive_push_inputs" {
  quota_code   = "L-9E233AF7"
  service_code = "medialive"
  value        = local.max_medialive_push_input
}

## Request was lower than default limit, TODO Add conditional to local vars
#resource "aws_servicequotas_service_quota" "mediapackage_channels" {
#  quota_code   = "L-352B8598"
#  service_code = "mediapackage"
#  value        = local.max_mediapackage_channels
#}

resource "aws_servicequotas_service_quota" "mediapackage_vod_assets" {
  quota_code   = "L-563EE697"
  service_code = "mediapackage"
  value        = local.max_mediapackage_vod_assets
}

resource "aws_servicequotas_service_quota" "mediapackage_concurrent_harvest_clipping" {
  quota_code   = "L-B1B90B42"
  service_code = "mediapackage"
  value        = local.max_mediapackage_con_clipping
}

resource "aws_servicequotas_service_quota" "cloudfront_data_transfer_rate_per_distribution" {
  quota_code   = "L-0F1E9017"
  service_code = "cloudfront"
  value        = local.max_data_transfer_per_distribution_Gbps
}


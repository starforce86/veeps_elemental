##### VPC ######
# General network 
################
module "vpc_veepsapi" {
  source             = "./module/vpc"
  aws_region         = "us-east-1"
  vpc_cidr_block     = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c", ]
}

##### ALB #####
# To route traffic to private app subnet 
###############
module "alb_public" {
  source         = "./module/alb"
  vpc_id         = module.vpc_veepsapi.vpc_id
  public_subnets = module.vpc_veepsapi.public_subnets_ids
  cidr_blocks    = ["0.0.0.0/0"] # Open to the web 
  alb_name       = "public"
}

##### ECR ######
# Docker Container registry for veeps api app  
################
module "ecr_veeps_api" {
  source              = "./module/ecr"
  ecr_repository_name = "veeps_api"
}

#### Aurora #####
# Postgres database server
#################
module "postgres_aurora" {
  source              = "./module/aurora_postgres_serverless_v2"
  aurora_cluster_name = "veepsapi"
  database_name       = "postgres"
  username            = "app"
  vpc_id              = module.vpc_veepsapi.vpc_id
  private_subnets     = module.vpc_veepsapi.app_subnets_ids
}

##### SNS ######
# SNS Topic for Veeps API to push alerts to
################
module "sns_veeps_api" {
  source            = "./module/sns"
  sns_topic_name    = "Cloudwatch-hook"
  input_bucket_name = "veeps-vod-input-${var.env}"
}

#### S3 #####
# Buckets where livestream puts clips 
#############
resource "aws_s3_bucket" "clip_bucket" {
  bucket = "veeps-vod-clip-${var.env}"
}


##### ECS ######
# AWS managed K8s to run Veeps app 
################
module "ecs_veeps_api" {
  source       = "./module/ecs"
  service_name = "veeps"

  vpc_id          = module.vpc_veepsapi.vpc_id
  public_subnets  = module.vpc_veepsapi.public_subnets_ids
  private_subnets = module.vpc_veepsapi.app_subnets_ids

  alb_arn   = module.alb_public.alb_arn
  alb_sg_id = module.alb_public.alb_sg_id

  repository_url = module.ecr_veeps_api.ecr_url

  database_secret = module.postgres_aurora.db_connect_secret

  input_bucket_name  = "veeps-vod-input-${var.env}"
  output_bucket_name = "veeps-vod-output-${var.env}"
  clip_bucket_name   = aws_s3_bucket.clip_bucket.id

  callback_sns_arn = module.sns_veeps_api.sns_callback_arn
}

module "mediaconvert_pipeline" {
  source             = "./module/mediaconvert_pipeline"
  function_name      = "vod-s3-trigger"
  description        = "function triggered after file upload to s3"
  runtime            = "python3.8"
  handler            = "app.handler"
  input_bucket_name  = "veeps-vod-input-${var.env}"
  output_bucket_name = "veeps-vod-output-${var.env}"
  lambda_bucket_name = "veeps-lambda-${var.env}"
}

module "github-integration" {
  source     = "./module/github-integration"
  thumbprint = "6938fd4d98bab03faadb97b34396831e3780aea1"
  repos = {
    devops = var.devops_repo
  }
}

resource "aws_iam_role_policy_attachment" "devops" {
  role       = module.github-integration.roles["devops"].name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_sns_topic_subscription" "veeps_api_subscription" {
  topic_arn            = module.sns_veeps_api.sns_callback_arn
  protocol             = "http"
  raw_message_delivery = "false"
  endpoint             = module.alb_public.alb_aws_url
}

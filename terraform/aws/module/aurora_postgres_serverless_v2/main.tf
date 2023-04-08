resource "random_password" "master" {
  length  = 16
  special = false
}

data "aws_subnet" "emptycheck" {
  id = var.private_subnets[0] #Private Subnet list cannot be empty! Catching during plan phase. 
}

module "aurora" {
  source = "terraform-aws-modules/rds-aurora/aws"

  name                = var.aurora_cluster_name
  engine              = "aurora-postgresql"
  engine_version      = var.engine_version
  engine_mode         = "provisioned" #provisioned + serverless instance = serverless v2
  storage_encrypted   = true
  monitoring_interval = 60

  vpc_id                 = var.vpc_id
  db_subnet_group_name   = var.aurora_cluster_name
  create_db_subnet_group = true
  subnets                = var.private_subnets
  create_security_group  = true
  allowed_cidr_blocks    = var.allowed_cidr_blocks
  enable_http_endpoint   = false

  database_name          = var.database_name
  master_username        = var.username
  master_password        = random_password.master.result
  create_random_password = false

  apply_immediately   = true
  skip_final_snapshot = true

  db_parameter_group_name         = aws_db_parameter_group.dbparams.id
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.dbparams.id
  serverlessv2_scaling_configuration = {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }

  instance_class = "db.serverless"
  instances = {
    one = {}
  }
}

resource "aws_db_parameter_group" "dbparams" {
  name        = "${var.aurora_cluster_name}-aurora-db-postgres14-parameter-group"
  family      = "aurora-postgresql14"
  description = "${var.aurora_cluster_name}-aurora-db-postgres14-parameter-group"
}

resource "aws_rds_cluster_parameter_group" "dbparams" {
  name        = "${var.aurora_cluster_name}-aurora-postgres14-cluster-parameter-group"
  family      = "aurora-postgresql14"
  description = "${var.aurora_cluster_name}-aurora-postgres14-cluster-parameter-group"
}


### Save admin creds to aws secret manager ###
resource "aws_secretsmanager_secret" "rds_credentials" {
  name = "${var.aurora_cluster_name}-database-credentials-admin"
}

resource "aws_secretsmanager_secret_version" "rds_credentials" {
  secret_id     = aws_secretsmanager_secret.rds_credentials.id
  secret_string = <<EOF
{
  "username": "${var.username}",
  "password": "${random_password.master.result}",
  "engine": "postgres",
  "host": "${module.aurora.cluster_endpoint}",
  "port": ${module.aurora.cluster_port},
  "dbClusterIdentifier": "${module.aurora.cluster_id}",
  "databaseName": "${var.database_name}"
}
EOF
}

#Random password for app to use for auth
resource "random_password" "api_key" {
  length  = 32
  special = false
}

### Save api_key to aws secret manager ###
resource "aws_secretsmanager_secret" "api_key" {
  name = "${var.service_name}-api_key"
}

resource "aws_secretsmanager_secret_version" "api_key" {
  secret_id     = aws_secretsmanager_secret.api_key.id
  secret_string = <<EOF
{
  "api_key": "${random_password.api_key.result}"
}
EOF
}


# Create an AWS ECS Cluster where the ECS/Fargate Tasks will run
resource "aws_ecs_cluster" "cluster" {
  name = var.service_name
}

resource "aws_security_group" "ecs_service_sg" {
  description = "Only allow incoming traffic from the ALB in front of the ECS Service, All outgoing"

  vpc_id = var.vpc_id

  ingress {
    # Assume port 8000 for the containers/Tasks
    from_port = 8000
    to_port   = 8000
    protocol  = "tcp"
    # Only allow incoming traffic from the ALB in front of the ECS Service
    security_groups = [var.alb_sg_id]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    #tfsec:ignore:AWS009
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb_target_group" "alb_target_group" {
  name        = "alb-target-group"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    matcher = "200,301,302"
    path    = "/"
  }
}


resource "aws_lb_listener" "alb_listener_http" {
  load_balancer_arn = var.alb_arn
  port              = 80
  #tfsec:ignore:AWS004
  protocol = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alb_target_group.arn
  }
}


# The ECS/Fargate Task(s) will use the following IAM Role for any interactions with other AWS resources.
# This is analogous to an EC2 Instance's Instance Profile.
resource "aws_iam_role" "ecs_fargate_task_role" {
  name_prefix        = "ecs_fargate"
  assume_role_policy = data.aws_iam_policy_document.ecs_fargate_task_role_policy_document.json
}

data "aws_iam_policy_document" "ecs_fargate_task_role_policy_document" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["ecs-tasks.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_policy" "veep_api_access" {
  name = "veep_api_access"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "mediaconnect:*",
          "medialive:*",
          "cloudfront:*",
          "mediapackage:*",
          "mediapackage-vod:*",
          "mediastore:*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "s3:GetBucketTagging",
          "s3:GetBucketRequestPayment",
          "s3:GetBucketLogging",
          "s3:GetBucketCORS",
          "s3:GetAnalyticsConfiguration",
          "s3:GetBucketVersioning",
          "s3:GetBucketAcl",
          "s3:GetBucketNotification",
          "s3:GetBucketLocation"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "s3:*"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:s3:::${var.input_bucket_name}/*"
      },
      {
        Action = [
          "s3:*"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:s3:::${var.output_bucket_name}/*"
      },
      {
        Action = [
          "s3:*"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:s3:::${var.clip_bucket_name}/*"
      },
      {
        Action = [
          "sns:*"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "lambda:InvokeFunction"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:lambda:::function:${var.lambda_to_trigger_to_convert}"
      },
      {
        Action = [
          "iam:PassRole"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:iam::*:role/MediaLiveAccessRole"
      },
      {
        Action = [
          "iam:PassRole"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:iam::*:role/MediaStoreAccessLogs"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "veep_api_access_custom" {
  policy_arn = aws_iam_policy.veep_api_access.arn
  role       = aws_iam_role.ecs_fargate_task_role.name
}

resource "aws_iam_role_policy_attachment" "veep_api_access_cloudformationfull" {
  policy_arn = "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess"
  role       = aws_iam_role.ecs_fargate_task_role.name
}

#Creates VPCs, attatches EIPs
resource "aws_iam_role_policy_attachment" "veep_api_access_networking" {
  policy_arn = "arn:aws:iam::aws:policy/job-function/NetworkAdministrator"
  role       = aws_iam_role.ecs_fargate_task_role.name
}

# Boilerplate code to set up the AWS Service Role "ecsTaskExecutionRole" and its related Policies
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html
resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = "ecsTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.ecsTaskExecutionRole_assume_role_policy_document.json
}

data "aws_iam_policy_document" "ecsTaskExecutionRole_assume_role_policy_document" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

#### Database Secret ####

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_secret_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = aws_iam_policy.database_secret_policy.arn
}

resource "aws_iam_policy" "database_secret_policy" {
  name = "database_secret"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = "${var.database_secret}"
      },
    ]
  })
}

#### API_KEY Secret ####

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_apikey_secret_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = aws_iam_policy.apikey_secret_policy.arn
}

resource "aws_iam_policy" "apikey_secret_policy" {
  name = "apikey_secret"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = "${aws_secretsmanager_secret.api_key.arn}"
      },
    ]
  })
}

#### App to Cloudformation permission ####

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_cloudformation_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = aws_iam_policy.app_cloudformation_policy.arn
}

resource "aws_iam_policy" "app_cloudformation_policy" {
  name = "veepsapi_cloudformation_access"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "cloudformation:*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

#### Task ####

resource "aws_ecs_task_definition" "ecs_fargate_task" {
  family                   = "ecs_fargate_task"
  container_definitions    = <<DEFINITION
  [
    {
      "name": "ecs_fargate_task",
      "image": "${var.repository_url}:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "veeps-api-task",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "streaming"
        }
      },
      "memory": 512,
      "cpu": 256,
      "command": ["/start.sh"],
      "entryPoint": ["/entrypoint.sh"],
      "environment": [
        {"name": "AWS_S3_VOD_INPUT_BUCKET_NAME", "value": "${var.input_bucket_name}"},
        {"name": "AWS_S3_VOD_CLIP_BUCKET_NAME", "value": "${var.clip_bucket_name}"},
        {"name": "AWS_VOD_S3_TRIGGER_LAMBDA_FUNCTION_NAME", "value": "${var.lambda_to_trigger_to_convert}"}
      ],
      "secrets": [
            {
                "valueFrom": "${var.database_secret}:databaseName::",
                "name": "POSTGRES_DB"
            },
            {
                "valueFrom": "${var.database_secret}:username::",
                "name": "POSTGRES_USER"
            },
            {
                "valueFrom": "${var.database_secret}:password::",
                "name": "POSTGRES_PASSWORD"
            },
            {
                "valueFrom": "${var.database_secret}:host::",
                "name": "POSTGRES_HOST"
            },
            {
                "valueFrom": "${var.database_secret}:port::",
                "name": "POSTGRES_PORT"
            },
            {
                "valueFrom": "${aws_secretsmanager_secret.api_key.arn}:api_key::",
                "name": "API_AUTH_KEY"
            }
        ]
    }
  ]

  DEFINITION
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"                               # Required for Fargate!
  memory                   = 512                                    # This must match the "memory" value from the `container_definitions` block above!
  cpu                      = 256                                    # This must match the "cpu" value from the `container_definitions` block above!
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn  # ECS Service uses this Role
  task_role_arn            = aws_iam_role.ecs_fargate_task_role.arn # The Tasks themselves use this Role (similar to EC2 Instance Profile)
}

# The ECS Service definition ties all of the above resources together
resource "aws_ecs_service" "ecs_service" {
  name            = var.service_name
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.ecs_fargate_task.arn
  launch_type     = "FARGATE"
  desired_count   = var.ecs_service_desired_task_count

  network_configuration {
    subnets          = var.public_subnets
    assign_public_ip = true # Required for Fargate + ECR: https://aws.amazon.com/premiumsupport/knowledge-center/ecs-pull-container-api-error-ecr/
    security_groups  = [aws_security_group.ecs_service_sg.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.alb_target_group.arn
    container_name   = aws_ecs_task_definition.ecs_fargate_task.family
    container_port   = 8000
  }
}

### Callback to Veeps api when mediaconvert job finishes
resource "aws_cloudwatch_event_rule" "mediaconvert_finish_api" {
  name        = "mediaconvert_finish_api"
  description = "Transcoding finished, send to VeepsApi"

  event_pattern = <<EOF
{
  "source": [ "aws.mediaconvert" ],
  "detail": {
    "detail-type": [ "MediaConvert Job State Change" ]
  }
}
EOF
}

resource "aws_cloudwatch_event_target" "s3_object_created" {
  rule      = aws_cloudwatch_event_rule.mediaconvert_finish_api.name
  target_id = "veeps_api_mediaconvert_finished"
  arn       = var.callback_sns_arn
}

### Callback to Veeps api when s3 file completes its upload
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.input_bucket_name

  topic {
    topic_arn     = var.callback_sns_arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".log"
  }
}
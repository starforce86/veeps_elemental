resource "aws_iam_role" "lambda" {
  name = "lambda-${var.function_name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role" "mediapackage_runner" {
  name = "mediapackage-vod-runner"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "mediapackage.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role" "mediapackage_lambda" {
  name = "mediapackage-lambda-${var.function_name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role" "mediaconvert" {
  name = "mediaconvert-${var.function_name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "mediaconvert.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

data "archive_file" "dummy" {
  output_path = "${path.module}/dist.zip"
  type        = "zip"
  source {
    content  = "dummy dummy"
    filename = "dummy.txt"
  }
}

resource "aws_lambda_layer_version" "lambda-layer" {
  layer_name = "${var.function_name}-layer"
  filename   = data.archive_file.dummy.output_path
  lifecycle {
    ignore_changes = [s3_key, s3_bucket, filename]
  }
}

resource "aws_lambda_function" "lambda" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn

  runtime = var.runtime
  handler = var.handler

  memory_size = var.memory_size
  timeout     = var.timeout

  layers = [aws_lambda_layer_version.lambda-layer.arn]

  filename = data.archive_file.dummy.output_path

  environment {
    variables = merge(
      var.envs,
      tomap({
        "DestinationBucket" = aws_s3_bucket.output_bucket.id
        "Application"       = "Veeps-VOD"
        "MediaConvertRole"  = aws_iam_role.mediaconvert.arn
      })
    )
  }

  tags = merge(
    var.common_tags,
    tomap({
      "description" = var.description
    })
  )
  lifecycle {
    ignore_changes = [s3_key, s3_bucket, layers, filename]
  }
}

#### Lambda that listens for mediaconvert to be completed, then adds to MediaPackage(CDN) ####
resource "aws_lambda_function" "mediaconvert_finished_lambda" {
  function_name = "mediaconvert_finished_actions"
  role          = aws_iam_role.mediapackage_lambda.arn

  runtime = var.runtime
  handler = var.handler

  memory_size = var.memory_size
  timeout     = var.timeout

  filename = data.archive_file.dummy.output_path

  environment {
    variables = merge(
      var.envs,
      tomap({
        "DestinationBucket" = aws_s3_bucket.output_bucket.id
        "Application"       = "Veeps-VOD"
        "MediaConvertRole"  = aws_iam_role.mediaconvert.arn
        "PACKAGE_GROUP_ID"  = var.mediapackage_group_name
        "SOURCE_ROLE_ARN"   = aws_iam_role.mediapackage_runner.arn
      })
    )
  }

  tags = merge(
    var.common_tags,
    tomap({
      "description" = var.description
    })
  )
  lifecycle {
    ignore_changes = [s3_key, s3_bucket, layers, filename]
  }
}

#### Listen for MediaConvert to finish, trigger lambda ####

resource "aws_cloudwatch_event_rule" "mediaconvert_finish" {
  name        = "mediaconvert_finish"
  description = "Transcoding finished, send to CDN"

  event_pattern = <<EOF
{
  "source": [ "aws.mediaconvert" ],
  "detail": {
    "status": [ "COMPLETE" ]
  }
}
EOF
}

resource "aws_cloudwatch_event_target" "mediaconvert_finish" {
  rule      = aws_cloudwatch_event_rule.mediaconvert_finish.name
  target_id = "mediaconvert_finished_lambda"
  arn       = aws_lambda_function.mediaconvert_finished_lambda.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_mediaconvert_finish" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mediaconvert_finished_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.mediaconvert_finish.arn
}

resource "aws_iam_policy" "s3_download" {
  name = "lambda-s3-download-${var.input_bucket_name}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
        ]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.input_bucket.arn}/*"
      },
    ]
  })
}

resource "aws_iam_policy" "s3_output" {
  name = "mediapackage-s3-download-${var.output_bucket_name}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:GetBucketLocation",
        ]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.output_bucket.arn}/*"
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
    ]
  })
}

resource "aws_iam_policy" "mediapackage_create" {
  name = "lambda-mediapackage-create-${var.input_bucket_name}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "mediapackage:*",
          "mediapackage-vod:*",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_policy" "mediapackage_passrole" {
  name = "lambda-mediapackage-passrole-${var.input_bucket_name}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "iam:PassRole",
        ]
        Effect   = "Allow"
        Resource = "${aws_iam_role.mediapackage_runner.arn}"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_download_lambda" {
  policy_arn = aws_iam_policy.s3_download.arn
  role       = aws_iam_role.lambda.name
}

resource "aws_iam_role_policy_attachment" "s3_download_lambda_runner" {
  policy_arn = aws_iam_policy.s3_download.arn
  role       = aws_iam_role.mediapackage_runner.name
}

resource "aws_iam_role_policy_attachment" "mediapackage_s3_download" {
  policy_arn = aws_iam_policy.s3_output.arn
  role       = aws_iam_role.mediapackage_runner.name
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda.name
}

resource "aws_iam_role_policy_attachment" "mediapackage_lambda_cloudwatch" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.mediapackage_lambda.name
}

resource "aws_iam_role_policy_attachment" "mediapackage_lambda_mediapackage" {
  policy_arn = aws_iam_policy.mediapackage_create.arn
  role       = aws_iam_role.mediapackage_lambda.name
}

resource "aws_iam_role_policy_attachment" "mediapackage_lambda_mediapackagepassrole" {
  policy_arn = aws_iam_policy.mediapackage_passrole.arn
  role       = aws_iam_role.mediapackage_lambda.name
}

resource "aws_iam_role_policy_attachment" "lambda_mediaconvert" {
  policy_arn = "arn:aws:iam::aws:policy/AWSElementalMediaConvertFullAccess"
  role       = aws_iam_role.lambda.name
}

resource "aws_iam_policy" "mediaconvert_s3" {
  name = "mediaconvert-s3"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
        ]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.input_bucket.arn}/*"
      },
      {
        Action = [
          "s3:GetObject*",
          "s3:PutObject*",
        ]
        Effect   = "Allow"
        Resource = ["${aws_s3_bucket.output_bucket.arn}/*", aws_s3_bucket.output_bucket.arn]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "mediaconvert_s3" {
  policy_arn = aws_iam_policy.mediaconvert_s3.arn
  role       = aws_iam_role.mediaconvert.name
}

resource "aws_lambda_permission" "allow_input_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.input_bucket.arn
}

resource "aws_s3_bucket" "input_bucket" {
  bucket = var.input_bucket_name
}

resource "aws_s3_bucket_public_access_block" "input_bucket" {
  bucket = aws_s3_bucket.input_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Veeps api is triggering
# resource "aws_s3_bucket_notification" "bucket_notification" {
#   bucket = aws_s3_bucket.input_bucket.id

#   lambda_function {
#     lambda_function_arn = aws_lambda_function.lambda.arn
#     events              = ["s3:ObjectCreated:CompleteMultipartUpload"]
#   }

#   depends_on = [aws_lambda_permission.allow_input_bucket]
# }

resource "aws_s3_bucket_server_side_encryption_configuration" "input_bucket" {
  bucket = aws_s3_bucket.input_bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket" "output_bucket" {
  bucket = var.output_bucket_name
}

resource "aws_s3_bucket_public_access_block" "output_bucket" {
  bucket = aws_s3_bucket.output_bucket.id

  block_public_acls       = false
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "output_bucket" {
  bucket = aws_s3_bucket.output_bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = var.lambda_bucket_name
}

resource "aws_s3_bucket_public_access_block" "lambda_bucket" {
  bucket = aws_s3_bucket.lambda_bucket.id

  block_public_acls       = false
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_bucket" {
  bucket = aws_s3_bucket.lambda_bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}


## Mediapackage vod package group is not supported in terraform yet, create one via aws cli
resource "null_resource" "mediapackage_group" {
  provisioner "local-exec" {
    command = "/bin/bash aws mediapackage-vod create-packaging-group --id ${var.mediapackage_group_name}"
  }
}
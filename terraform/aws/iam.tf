### Iam role that medialive uses. Created automatically when in web console.
## If this was already made via the web console, run this to import into terraform state
## terraform import aws_iam_role.MediaLiveAccessRole MediaLiveAccessRole
resource "aws_iam_role" "MediaLiveAccessRole" {
  name = "MediaLiveAccessRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "medialive.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "MediaLiveAccessRole" {
  role       = aws_iam_role.MediaLiveAccessRole.name
  policy_arn = aws_iam_policy.MediaLiveCustomPolicy.arn
}

resource "aws_iam_role_policy_attachment" "AmazonSSMReadOnlyAccess" {
  role       = aws_iam_role.MediaLiveAccessRole.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
}

resource "aws_iam_policy" "MediaLiveCustomPolicy" {
  name = "MediaLiveCustomPolicy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
        Resource = "*"
      },

      {
        Effect   = "Allow"
        Action   = ["mediastore:ListContainers", "mediastore:PutObject", "mediastore:GetObject", "mediastore:DeleteObject", "mediastore:DescribeObject"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams", "logs:DescribeLogGroups"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams", "logs:DescribeLogGroups"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect   = "Allow"
        Action   = ["mediaconnect:ManagedDescribeFlow", "mediaconnect:ManagedAddOutput", "mediaconnect:ManagedRemoveOutput"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:describeSubnets",
          "ec2:describeNetworkInterfaces",
          "ec2:createNetworkInterface",
          "ec2:createNetworkInterfacePermission",
          "ec2:deleteNetworkInterface",
          "ec2:deleteNetworkInterfacePermission",
          "ec2:describeSecurityGroups",
          "ec2:describeAddresses",
          "ec2:associateAddress"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["mediapackage:DescribeChannel"]
        Resource = "*"
      },
    ]
  })
}
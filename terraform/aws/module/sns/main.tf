data "aws_caller_identity" "current" {}

resource "aws_sns_topic" "sns_topic" {
  name = var.sns_topic_name
}

resource "aws_sns_topic_policy" "default" {
  arn = aws_sns_topic.sns_topic.arn

  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

# Any resource in this account can publish/subscribe to the sns topic
data "aws_iam_policy_document" "sns_topic_policy" {
  policy_id = "__default_policy_ID"

  statement {
    actions = [
      "SNS:Subscribe",
      "SNS:SetTopicAttributes",
      "SNS:RemovePermission",
      "SNS:Receive",
      "SNS:Publish",
      "SNS:ListSubscriptionsByTopic",
      "SNS:GetTopicAttributes",
      "SNS:DeleteTopic",
      "SNS:AddPermission",
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceOwner"

      values = [
        data.aws_caller_identity.current.account_id,
      ]
    }

    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    resources = [
      aws_sns_topic.sns_topic.arn,
    ]

    sid = "__default_statement_ID"
  }
  statement {
    actions = [
      "sns:Publish",
    ]
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [
      aws_sns_topic.sns_topic.arn,
    ]

    sid = "__MedialiveEvent"
  }
  statement {
    actions = [
      "sns:Publish",
    ]
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    resources = [
      aws_sns_topic.sns_topic.arn,
    ]

    condition {
      test     = "ArnLike"
      variable = "AWS:SourceArn"

      values = [
        "arn:aws:s3:::${var.input_bucket_name}",
      ]
    }

    sid = "__s3_upload"
  }
}
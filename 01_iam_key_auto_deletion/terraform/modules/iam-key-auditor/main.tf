resource "aws_sns_topic" "alerts" {
  name = "iam-security-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.email
}

resource "aws_iam_role" "lambda_role" {
  name = "iam-auditor-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iam:ListUsers",
          "iam:ListAccessKeys",
          "iam:UpdateAccessKey",
          "sns:Publish",
          "logs:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "auditor" {
  function_name = var.lambda_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "iam_key_auditor.lambda_handler"
  runtime       = "python3.12"
  timeout       = 15
  filename      = "${path.module}/lambda/auditor.zip"

  environment {
    variables = {
      MAX_AGE_DAYS  = var.max_age_days
      SNS_TOPIC_ARN = aws_sns_topic.alerts.arn
    }
  }
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "iam-key-audit-schedule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule = aws_cloudwatch_event_rule.schedule.name
  arn  = aws_lambda_function.auditor.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auditor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}
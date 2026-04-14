data "archive_file" "zip" {
  type        = "zip"
  source_file = "${path.module}/lambda.py"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_iam_role" "role" {
  name = "dr-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "this" {
  filename         = data.archive_file.zip.output_path
  function_name    = "dr-failover-orchestrator"
  role             = aws_iam_role.role.arn
  handler          = "lambda.lambda_handler"
  runtime          = "python3.12"

  environment {
    variables = {
      HOSTED_ZONE_ID = var.hosted_zone_id
      RECORD_NAME    = var.record_name
      DR_LB_DNS      = var.dr_lb_dns
      DR_LB_ZONE_ID  = var.dr_lb_zone_id
    }
  }
}

resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.sns_topic_arn
}
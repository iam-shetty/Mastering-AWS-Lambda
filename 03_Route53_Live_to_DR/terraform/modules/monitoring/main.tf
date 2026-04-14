resource "aws_route53_health_check" "hc" {
  fqdn          = var.record_name
  port          = 80
  type          = "HTTP"
  resource_path = "/"
}

resource "aws_sns_topic" "dr" {
  name = "dr-failover-topic"
}

resource "aws_cloudwatch_metric_alarm" "alarm" {
  alarm_name          = "primary-down"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  statistic           = "Minimum"
  period              = 60
  threshold           = 1
  alarm_actions       = [aws_sns_topic.dr.arn]
}

output "sns_arn" {
  value = aws_sns_topic.dr.arn
}
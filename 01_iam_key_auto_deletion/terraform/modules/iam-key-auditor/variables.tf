variable "lambda_name" {
  default = "iam-key-auditor"
}

variable "max_age_days" {
  default = 90
}

variable "schedule_expression" {
  default = "rate(1 day)"
}

variable "email" {
  description = "Email for SNS alerts"
}
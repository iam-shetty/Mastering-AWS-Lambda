
module "primary_alb" {
  source   = "./modules/alb"
  providers = { aws = aws.primary }
  name     = "primary"
  message  = "PRIMARY REGION"
}

module "dr_alb" {
  source   = "./modules/alb"
  providers = { aws = aws.dr }
  name     = "dr"
  message  = "DR REGION"
}

module "route53" {
  source      = "./modules/route53"
  domain_name = var.domain_name
  record_name = var.record_name
  primary_dns = module.primary_alb.alb_dns
  primary_zone_id = module.primary_alb.zone_id
}

module "monitoring" {
  source        = "./modules/monitoring"
  record_name   = "${var.record_name}.${var.domain_name}"
}

module "lambda" {
  source           = "./modules/lambda"
  providers        = { aws = aws.neutral }
  hosted_zone_id   = module.route53.zone_id
  record_name      = "${var.record_name}.${var.domain_name}"
  dr_lb_dns        = module.dr_alb.alb_dns
  dr_lb_zone_id    = module.dr_alb.zone_id
  sns_topic_arn    = module.monitoring.sns_arn
}
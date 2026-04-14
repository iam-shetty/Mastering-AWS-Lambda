resource "aws_route53_zone" "this" {
  name = var.domain_name
}

resource "aws_route53_record" "primary" {
  zone_id = aws_route53_zone.this.zone_id
  name    = var.record_name
  type    = "A"

  alias {
    name                   = var.primary_dns
    zone_id                = var.primary_zone_id
    evaluate_target_health = false
  }
}

output "zone_id" {
  value = aws_route53_zone.this.zone_id
}
#!/bin/bash
yum install -y httpd
systemctl start httpd
echo "PRIMARY REGION" > /var/www/html/index.html
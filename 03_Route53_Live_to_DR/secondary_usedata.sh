#!/bin/bash
yum install -y httpd
systemctl start httpd
echo "DR REGION" > /var/www/html/index.html
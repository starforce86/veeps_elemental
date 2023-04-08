output "db_connect_secret" {
  value = aws_secretsmanager_secret.rds_credentials.arn
}

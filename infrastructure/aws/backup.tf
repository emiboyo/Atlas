resource "aws_kms_key" "backup" {
  description             = "Atlas ${var.environment} backup encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_backup_vault" "primary" {
  name        = "${local.name}-primary"
  kms_key_arn = aws_kms_key.backup.arn
}

resource "aws_backup_vault_lock_configuration" "primary" {
  count               = var.environment == "production" ? 1 : 0
  backup_vault_name   = aws_backup_vault.primary.name
  min_retention_days  = var.backup_retention_days
  max_retention_days  = 3650
  changeable_for_days = 7
}

resource "aws_kms_key" "backup_dr" {
  provider                = aws.dr
  description             = "Atlas ${var.environment} disaster recovery backup encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_backup_vault" "dr" {
  provider    = aws.dr
  name        = "${local.name}-dr"
  kms_key_arn = aws_kms_key.backup_dr.arn
}

resource "aws_backup_vault_lock_configuration" "dr" {
  provider            = aws.dr
  count               = var.environment == "production" ? 1 : 0
  backup_vault_name   = aws_backup_vault.dr.name
  min_retention_days  = var.dr_backup_retention_days
  max_retention_days  = 3650
  changeable_for_days = 7
}

resource "aws_iam_role" "backup" {
  name = "${local.name}-backup"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "backup.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "backup_restore" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

resource "aws_iam_role_policy" "backup_snapshot_cleanup" {
  name = "rds-snapshot-cleanup"
  role = aws_iam_role.backup.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["rds:DeleteDBSnapshot"]
      Resource = "*"
    }]
  })
}

resource "aws_backup_plan" "main" {
  name = local.name

  rule {
    rule_name                = "continuous-rds"
    target_vault_name        = aws_backup_vault.primary.name
    schedule                 = "cron(0 1 * * ? *)"
    start_window             = 60
    completion_window        = 360
    enable_continuous_backup = true

    lifecycle {
      delete_after = var.backup_retention_days
    }

    copy_action {
      destination_vault_arn = aws_backup_vault.dr.arn
      lifecycle {
        delete_after = var.dr_backup_retention_days
      }
    }
  }
}

resource "aws_backup_selection" "rds" {
  name         = "${local.name}-rds"
  plan_id      = aws_backup_plan.main.id
  iam_role_arn = aws_iam_role.backup.arn
  resources    = [aws_db_instance.postgres.arn]
}

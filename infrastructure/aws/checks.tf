check "api_capacity_bounds" {
  assert {
    condition = (
      var.api_min_capacity <= var.api_desired_count &&
      var.api_desired_count <= var.api_max_capacity
    )
    error_message = "API desired count must be within the configured autoscaling bounds."
  }
}

check "database_storage_bounds" {
  assert {
    condition     = var.db_allocated_storage_gib <= var.db_max_allocated_storage_gib
    error_message = "Initial database storage cannot exceed its autoscaling maximum."
  }
}

check "disaster_recovery_region" {
  assert {
    condition     = var.aws_region != var.dr_region
    error_message = "The disaster recovery region must differ from the primary region."
  }
}

check "backup_retention" {
  assert {
    condition = (
      var.backup_retention_days >= 35 &&
      var.dr_backup_retention_days >= var.backup_retention_days
    )
    error_message = "Primary backups require at least 35 days and DR copies cannot retain less."
  }
}

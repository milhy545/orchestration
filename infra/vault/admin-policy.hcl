path "secret/data/orchestration/*" {
  capabilities = ["create", "update", "read", "delete", "list"]
}

path "secret/metadata/orchestration/*" {
  capabilities = ["list", "read", "delete"]
}

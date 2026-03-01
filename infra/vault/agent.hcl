exit_after_auth = false
pid_file = "/vault/runtime/vault-agent.pid"

auto_auth {
  method "token_file" {
    config = {
      token_file_path = "/vault/runtime/read.token"
    }
  }
}

vault {
  address = "http://vault:8200"
}

template_config {
  static_secret_render_interval = "30s"
}

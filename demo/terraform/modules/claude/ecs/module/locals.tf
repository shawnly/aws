locals {
  environment_variables = {
    Environment                         = var.environment
    EventID                            = var.event_id
    SPRING_PROFILES_ACTIVE             = var.spring_profiles
    ClientID                           = var.client_id
    KafkaServer                        = var.kafka_server
    DatabaseNamePrefix                  = var.database_name_prefix
    DataBaseServer                     = var.database_server
    DBUserName                         = var.db_username
    DBPassword                         = var.db_password
    DSSAud                             = var.dss_aud
    DSSUrl                             = var.dss_url
    SDSSUrl                            = var.sdss_url
    TokenManagerUrl                    = var.token_manager_url
    FIMSUrl                            = var.fims_url
    InterOpUrl                         = var.interop_url
    BOOTSTRAP_SERVERS                  = var.bootstrap_servers
    SCHEMA_REGISTRY_URL                = var.schema_registry_url
    SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO = var.schema_registry_auth_info
    CC_USER_PASSWORD                   = var.cc_user_password
    CC_USER_NAME                       = var.cc_username
  }
}
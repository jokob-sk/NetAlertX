## Authelia support

> [!NOTE]
> This is community-contributed. Due to environment, setup, or networking differences, results may vary. Please open a PR to improve it instead of creating an issue, as the maintainer is not actively maintaining it.


```yaml
theme: dark

default_2fa_method: "totp"

server:
  address: 0.0.0.0:9091
  endpoints:
    enable_expvars: false
    enable_pprof: false
    authz:
      forward-auth:
        implementation: 'ForwardAuth'
        authn_strategies:
          - name: 'HeaderAuthorization'
            schemes:
              - 'Basic'
          - name: 'CookieSession'
      ext-authz:
        implementation: 'ExtAuthz'
        authn_strategies:
          - name: 'HeaderAuthorization'
            schemes:
              - 'Basic'
          - name: 'CookieSession'
      auth-request:
        implementation: 'AuthRequest'
        authn_strategies:
          - name: 'HeaderAuthRequestProxyAuthorization'
            schemes:
              - 'Basic'
          - name: 'CookieSession'
      legacy:
        implementation: 'Legacy'
        authn_strategies:
          - name: 'HeaderLegacy'
          - name: 'CookieSession'
  disable_healthcheck: false
  tls:
    key: ""
    certificate: ""
    client_certificates: []
  headers:
    csp_template: ""

log:
  ## Level of verbosity for logs: info, debug, trace.
  level: info

###############################################################
# The most important section
###############################################################
access_control:
  ## Default policy can either be 'bypass', 'one_factor', 'two_factor' or 'deny'.
  default_policy: deny
  networks:
    - name: internal
      networks:
        - '192.168.0.0/18'
        - '10.10.10.0/8' # Zerotier
    - name: private
      networks:
        - '172.16.0.0/12'
  rules:
    - networks:
        - private
      domain:
        - '*'
      policy: bypass
    - networks:
        - internal
      domain:
        - '*'
      policy: bypass
    - domain:
        # exclude itself from auth, should not happen as we use Traefik middleware on a case-by-case screnario
        - 'auth.MYDOMAIN1.TLD'
        - 'authelia.MYDOMAIN1.TLD'
        - 'auth.MYDOMAIN2.TLD'
        - 'authelia.MYDOMAIN2.TLD'
      policy: bypass
    - domain:
        #All subdomains match
        - 'MYDOMAIN1.TLD'
        - '*.MYDOMAIN1.TLD'
      policy: two_factor
    - domain:
        # This will not work yet as Authelio does not support multi-domain authentication
        - 'MYDOMAIN2.TLD'
        - '*.MYDOMAIN2.TLD'
      policy: two_factor


############################################################
identity_validation:
  reset_password:
    jwt_secret: "[REDACTED]"

identity_providers:
  oidc:
    enable_client_debug_messages: true
    enforce_pkce: public_clients_only
    hmac_secret: [REDACTED]
    lifespans:
      authorize_code: 1m
      id_token: 1h
      refresh_token: 90m
      access_token: 1h
    cors:
      endpoints:
        - authorization
        - token
        - revocation
        - introspection
        - userinfo
      allowed_origins:
        - "*"
      allowed_origins_from_client_redirect_uris: false
    jwks:
      - key: [REDACTED]
        certificate_chain:
    clients:
      - client_id: portainer
        client_name: Portainer
        # generate secret with "authelia crypto hash generate pbkdf2 --random --random.length 32 --random.charset alphanumeric"
        # Random Password: [REDACTED]
        # Digest: [REDACTED]
        client_secret: [REDACTED]
        token_endpoint_auth_method: 'client_secret_post'
        public: false
        authorization_policy: two_factor
        consent_mode: pre-configured #explicit
        pre_configured_consent_duration: '6M' #Must be re-authorised every 6 Months
        scopes:
          - openid
          #- groups #Currently not supported in Authelia V
          - email
          - profile
        redirect_uris:
          - https://portainer.MYDOMAIN1.LTD
        userinfo_signed_response_alg: none

      - client_id: openproject
        client_name: OpenProject
        # generate secret with "authelia crypto hash generate pbkdf2 --random --random.length 32 --random.charset alphanumeric"
        # Random Password: [REDACTED]
        # Digest: [REDACTED]
        client_secret: [REDACTED]
        token_endpoint_auth_method: 'client_secret_basic'
        public: false
        authorization_policy: two_factor
        consent_mode: pre-configured #explicit
        pre_configured_consent_duration: '6M' #Must be re-authorised every 6 Months
        scopes:
          - openid
          #- groups #Currently not supported in Authelia V
          - email
          - profile
        redirect_uris:
          - https://op.MYDOMAIN.TLD
        #grant_types:
        #  - refresh_token
        #  - authorization_code
        #response_types:
        #  - code
        #response_modes:
        #  - form_post
        #  - query
        #  - fragment
        userinfo_signed_response_alg: none
##################################################################


telemetry:
  metrics:
    enabled: false
    address: tcp://0.0.0.0:9959

totp:
  disable: false
  issuer: authelia.com
  algorithm: sha1
  digits: 6
  period: 30 ## The period in seconds a one-time password is valid for.
  skew: 1
  secret_size: 32

webauthn:
  disable: false
  timeout: 60s ## Adjust the interaction timeout for Webauthn dialogues.
  display_name: Authelia
  attestation_conveyance_preference: indirect
  user_verification: preferred

ntp:
  address: "pool.ntp.org"
  version: 4
  max_desync: 5s
  disable_startup_check: false
  disable_failure: false

authentication_backend:
  password_reset:
    disable: false
    custom_url: ""
  refresh_interval: 5m
  file:
    path: /config/users_database.yml
    watch: true
    password:
      algorithm: argon2
      argon2:
        variant: argon2id
        iterations: 3
        memory: 65536
        parallelism: 4
        key_length: 32
        salt_length: 16

password_policy:
  standard:
    enabled: false
    min_length: 8
    max_length: 0
    require_uppercase: true
    require_lowercase: true
    require_number: true
    require_special: true
  ## zxcvbn is a well known and used password strength algorithm. It does not have tunable settings.
  zxcvbn:
    enabled: false
    min_score: 3

regulation:
  max_retries: 3
  find_time: 2m
  ban_time: 5m

session:
  name: authelia_session
  secret: [REDACTED]
  expiration: 60m
  inactivity: 15m
  cookies:
    - domain: 'MYDOMAIN1.LTD'
      authelia_url: 'https://auth.MYDOMAIN1.LTD'
      name: 'authelia_session'
      default_redirection_url: 'https://MYDOMAIN1.LTD'
    - domain: 'MYDOMAIN2.LTD'
      authelia_url: 'https://auth.MYDOMAIN2.LTD'
      name: 'authelia_session_other'
      default_redirection_url: 'https://MYDOMAIN2.LTD'

storage:
  encryption_key: [REDACTED]
  local:
    path: /config/db.sqlite3

notifier:
  disable_startup_check: true
  smtp:
    address: MYOTHERDOMAIN.LTD:465
    timeout: 5s
    username: "USER@DOMAIN"
    password: "[REDACTED]"
    sender: "Authelia <postmaster@MYOTHERDOMAIN.LTD>"
    identifier: NAME@MYOTHERDOMAIN.LTD
    subject: "[Authelia] {title}"
    startup_check_address: postmaster@MYOTHERDOMAIN.LTD

```

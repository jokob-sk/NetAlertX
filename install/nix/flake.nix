{
  description = "NixOS module for NetAlertX network monitoring";

  outputs = { self }: {
    nixosModules.default = { config, lib, ... }:
      with lib;
      let
        cfg = config.services.netalertx;
      in {
        options.services.netalertx = {
          enable = mkEnableOption "netalertx";
          port = mkOption {
            type = types.port;
            default = 20211;
            description = "Port to listen on for web gui";
          };
          graphqlPort = mkOption {
            type = types.port;
            default = 20212;
            description = "Port to listen on for GraphQL requests";
          };
          puid = mkOption {
            type = types.int;
            default = 20211;
            description = "PUID to run the app";
          };
          pgid = mkOption {
            type = types.int;
            default = 20211;
            description = "PGID to run the app";
          };
          imageTag = mkOption {
            type = types.str;
            default = "26.1.17";
            description = "Image tag to run";
          };
          backendApiUrl = mkOption {
            type = types.str;
            default = "http://localhost:${toString cfg.graphqlPort}";
            description = "URL to use when accessing GraphQL server";
          };
        };
        config = mkIf cfg.enable {
          users.users.netalertx = {
            isSystemUser = true;
            group = "netalertx";
            uid = cfg.puid;
          };
          users.groups.netalertx = {
            gid = cfg.pgid;
          };
          systemd.tmpfiles.rules = [
            "d /var/lib/netalertx 0755 ${toString cfg.puid} ${toString cfg.pgid} -"
            "d /var/lib/netalertx/db 0755 ${toString cfg.puid} ${toString cfg.pgid} -"
            "d /var/lib/netalertx/config 0755 ${toString cfg.puid} ${toString cfg.pgid} -"
          ];
          virtualisation.oci-containers = {
            containers = {
              netalertx = {
                image = "ghcr.io/jokob-sk/netalertx:${cfg.imageTag}";
                autoStart = true;
                extraOptions = [
                  "--network=host"
                  "--cap-drop=ALL"
                  "--cap-add=NET_ADMIN"
                  "--cap-add=NET_RAW"
                  "--cap-add=NET_BIND_SERVICE"
                  "--cap-add=CHOWN"
                  "--cap-add=SETUID"
                  "--cap-add=SETGID"
                  "--read-only"
                  "--tmpfs=/tmp"
                ];
                volumes = [
                  "/var/lib/netalertx:/data"
                  "/etc/localtime:/etc/localtime:ro"
                ];
                environment = {
                  PUID = toString cfg.puid;
                  PGID = toString cfg.pgid;
                  LISTEN_ADDR = "0.0.0.0";
                  PORT = "${toString cfg.port}";
                  GRAPHQL_PORT = "${toString cfg.graphqlPort}";
                  APP_CONF_OVERRIDE = builtins.toJSON { BACKEND_API_URL = cfg.backendApiUrl; };
                  ALWAYS_FRESH_INSTALL = "false";
                  NETALERTX_DEBUG = "0";
                };
              };
            };
          };
        };
      };
  };
}

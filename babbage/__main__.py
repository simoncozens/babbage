import argparse
import asyncio
import yaml

from babbage.server import Server


def main(args=None):
    parser = argparse.ArgumentParser(description="Babbage Server")
    parser.add_argument("--host", type=str, help="Host to bind the server to")
    parser.add_argument("--port", type=int, help="Port to run the server on")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--dev", type=int, help="Just render a dashboard to HTML and stop"
    )

    args = parser.parse_args(args)

    config = yaml.safe_load(open(args.config, "r"))

    assert "ha_url" in config, "Configuration must contain 'ha_url'"
    assert "access_token" in config, "Configuration must contain 'access_token'"
    assert "dashboard_name" in config, "Configuration must contain 'dashboard_name'"

    if args.dev is not None:
        from babbage.hass import HassDashboard

        dashboard = HassDashboard(
            ha_url=config["ha_url"],
            access_token=config["access_token"],
            url_path=config["dashboard_name"],
        )
        asyncio.run(dashboard.fetch())
        open("dashboard.html", "w").write(dashboard.render(args.dev))
        return

    server = Server(
        config,
        host=args.host or config.get("host") or "0.0.0.0",
        httpPort=args.port or config.get("port") or 2300,
        debug=args.debug,
    )
    server.run()


if __name__ == "__main__":
    main()

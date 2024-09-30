# What is this?

A [Grafana](https://grafana.com/oss/) setup to analyse logs from docker services with

- [Loki](https://grafana.com/oss/loki/) for sending the logs
- [Prometheus](https://prometheus.io/) (with [cadvisor](https://github.com/google/cadvisor)) for docker container metrics  
- [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) for sending emails  
- [Mailpit](https://mailpit.axllent.org/) as SMTP host  

Link to my Blog post:
[https://andreas-mausch.de/blog/2021-05-14-monitoring-grafana/](https://andreas-mausch.de/blog/2021-05-14-monitoring-grafana/)

# Install Loki Docker Driver

```bash
docker plugin install grafana/loki-docker-driver:3.2.0 --alias loki --grant-all-permissions
```

# Run

```bash
docker compose up
```

Grafana is accessible at [http://localhost:3000](http://localhost:3000)  
The first time login credentials are **admin/admin**.

# Grafana dashboard

I've set up a custom Grafana dashboard which shows the memory usage of all
docker services and the latest log entries with *warning* or *error*.

You can find it's configuration in the [grafana/](grafana/) folder.

To see all the logs, you can select the *Explore* menu item,
make sure *Code* is selected from Builder/Code and enter the query string
`{host=~".+"}`.

This should give you all the logs, including info level logging.

# Links

After starting the services, these URLs become available:

- Grafana: [http://localhost:3000](http://localhost:3000)
- Prometheus: [http://localhost:9090/alerts](http://localhost:9090/alerts)
- Alertmanager: [http://localhost:9093/#/alerts](http://localhost:9093/#/alerts)
- Mailpit: [http://localhost:8025](http://localhost:8025)

# Start example logging service

```bash
docker run -it --rm --name my-service --log-driver=loki --log-opt loki-url="http://localhost:3100/loki/api/v1/push" --log-opt loki-pipeline-stages="- multiline:
           firstline: '^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2},\\d{3}'
       " -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:3 python my-service.py
```

After starting the service, you should see logs in grafana.

Stop the service, wait a few minutes, and you should see an alert email in mailpit.

# Multiline

We tell Loki how to split multiline logs into the right chunks, but telling how a new line starts.
In our case, it is the regex above for a date.

Check the [Grafana docs](https://grafana.com/docs/loki/latest/clients/promtail/stages/multiline/) on this topic to see allowed values.

# Check alerts

There are two types of alerts:

- Prometheus checks our services run at [prometheus/alerts.yml](prometheus/alerts.yml).
- Loki checks for any warnings or errors in the log files at [loki/loki_alerts.yml](loki/loki_alerts.yml).

Alerts are sent:
- When the *my-service* is down for more than 1 minute
- Any message is logged with the content error, failure or exception.

See the links for Alertmanager and mailhog above.

# Clean up

To stop all services and the according volumes run this:

```bash
docker compose down --volumes
```

To remove the loki plugin:

```bash
docker plugin disable loki
docker plugin rm loki
```

# Source link in alert e-mails is broken for loki alerts

Right, I don't know how to solve it.
I think the link displayed is the generatorURL sent to alertmanager.

And [somebody requested](https://github.com/grafana/loki/issues/3119#issuecomment-776453889)
to support the field in order to allow customized source links.

Maybe this will be fixed soon.

# Thoughts on loki

There is a huge problem with loki and I would not recommend to use it any longer:

[if loki is not reachable and loki-docker-driver is activated, containers apps stops and cannot be stopped/killed](https://github.com/grafana/loki/issues/2361)

Open for more than four years.

> Hit this today. You need to stop publishing this driver immediately until this problem is solved. This is unacceptable.
> -- https://github.com/grafana/loki/issues/2361#issuecomment-1279757220

The alternative is promtail, which reads logs from the file system.
I always thought it would be nice if this disk usage could be skipped, however if loki is that unreliable I'll take it.

Also: The docker image tag `grafana/loki-docker-driver:latest` is outdated:
[https://github.com/grafana/loki/issues/10112](https://github.com/grafana/loki/issues/10112)

If you specify a tag like `3.2.0` explicitly you will use a recent version,
but the `latest` tag lags three years behind.
Looks sloppy.

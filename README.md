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
docker plugin install grafana/loki-docker-driver:3.4.2-amd64 --alias loki --grant-all-permissions
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

# Advanced queries

You can write more advanced log queries, for example:

```logql
{host=~".+"} | detected_level=`info` | pattern "<date> <time> <level> <_>"
```

- `detected_level`:
  > Explore Logs adds a special detected_level label to all log lines where Loki assigns a level of the log line, including debug, info, warn, error, fatal, critical, trace, or unknown if no level could be determined.
  > -- https://grafana.com/docs/grafana/latest/explore/simplified-exploration/logs/labels-and-fields/
  
  See also [here](https://github.com/grafana/grafana/issues/87564)
- `pattern`:
  See [here](https://grafana.com/blog/2021/08/09/new-in-loki-2.3-logql-pattern-parser-makes-it-easier-to-extract-data-from-unstructured-logs/)

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

We tell Loki how to split multiline logs into the right chunks by telling how a new line starts.
In our case, it is the regex above for a date.

Check the [Grafana docs](https://grafana.com/docs/loki/latest/clients/promtail/stages/multiline/) on this topic to see allowed values.

# Check alerts

There are two types of alerts:

- Prometheus checks our services run at [prometheus/alerts.yml](prometheus/alerts.yml).
- Loki checks for any warnings or errors in the log files at [loki/loki_alerts.yml](loki/loki_alerts.yml).

Alerts are sent:
- When the *my-service* is down for more than 1 minute
- Any message is logged with the content error, failure or exception.

The target recipient is `developer@test.com`.
You can find the e-mails in the Mailpit.
Note: It might take some minutes, until Alertmanager decides to fire them.

Especially when a container does not exist anymore, `cadvisor` seems to continue sending
metrics for it. Only after a few minutes a service is marked as *not running*, so be patient please.
And only after that the one-minute timer in Prometheus will start to tick and
eventually will switch from *Pending* to *Firing*.

You are of course free to set up your own alerting rules
and other services which can send alerts to Alertmanager.
I've just set this up to show an example alert.

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

## Deadlocked Docker Daemon

There is a huge problem with loki and I would not recommend to use it any longer:

[Known Issue: Deadlocked Docker Daemon](https://grafana.com/docs/loki/latest/send-data/docker-driver/#known-issue-deadlocked-docker-daemon)

[if loki is not reachable and loki-docker-driver is activated, containers apps stops and cannot be stopped/killed](https://github.com/grafana/loki/issues/2361)

Open for more than four years.

> Hit this today. You need to stop publishing this driver immediately until this problem is solved. This is unacceptable.
> -- https://github.com/grafana/loki/issues/2361#issuecomment-1279757220

If you decide to keep using Loki I recommend to set `loki-retries=2`, `loki-max-backoff=800ms` and `loki-timeout=1s`,
as the official docs suggest.
I further recommend to change the settings globally in your `daemon.json`:
[Change the default logging driver](https://grafana.com/docs/loki/latest/send-data/docker-driver/configuration/#change-the-default-logging-driver)

I am not so sure about `keep-file=true`, I would rather keep it disabled,
even though *this means you won’t be able to use docker logs once the container is stopped*.

The alternative to Loki is [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/configuration/#docker),
which reads logs from the file system.
I always thought it would be nice if this disk usage could be skipped, however if loki is that unreliable I'll take it.

## Outdated latest tag

Also: The docker image tag `grafana/loki-docker-driver:latest` is outdated:
[https://github.com/grafana/loki/issues/10112](https://github.com/grafana/loki/issues/10112)

If you specify a tag like `3.2.0` explicitly you will use a recent version,
but the `latest` tag lags three years behind.
Looks sloppy.

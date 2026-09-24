## Jadawel is an open source no-code database tool and Airtable alternative.

Create your own online database without technical experience. Our user-friendly no-code
tool gives you the powers of a developer without leaving your browser.

* A spreadsheet database hybrid combining ease of use and powerful data organization.
* Easily self-hosted with no storage restrictions.
* Alternative to Airtable.
* Open-core with all non-premium and non-enterprise features under
  the [MIT License](https://choosealicense.com/licenses/mit/) allowing commercial and
  private use.
* Headless and API first.
* Uses popular frameworks and tools like [Django](https://www.djangoproject.com/),
  [Vue.js](https://vuejs.org/) and [PostgreSQL](https://www.postgresql.org/).

```bash
docker run -v jadawel_data:/jadawel/data -p 80:80 -p 443:443 jadawel/jadawel:2.2.2
```

## Quick Reference

* **Source Code Available At**: [github.com/Azizahmed/Jadawel](https://github.com/Azizahmed/Jadawel)
* **Docs At**: [`docs/CONFIGURATION.md`](../../docs/CONFIGURATION.md)
* **License**: Open-Core with all non-premium and non-enterprise code under the MIT
  license.

## Supported tags and Dockerfile Links

* [`X.Y.Z`](./Dockerfile) Tagged by Jadawel version.
* [`latest`](./Dockerfile)

## Quick Start

Run the command below to start a Jadawel server running locally listening on port `80`.
You will only be able to connect to Jadawel from the machine running the server via
`http://localhost`.

```bash
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=http://localhost \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

* Change `JADAWEL_PUBLIC_URL` to `https://YOUR_DOMAIN` or `http://YOUR_IP` to enable
  external access. Ensure that this address matches the one you enter in your browser's
  URL bar. Any different address will be considered a published application.
* Add `-e JADAWEL_CADDY_ADDRESSES=:443` to enable
  [automatic Caddy HTTPS](https://caddyserver.com/docs/automatic-https).
* Optionally add `-e DATABASE_URL=postgresql://user:pwd@host:port/db` to use an external
  Postgresql.
* Optionally add `-e REDIS_URL=redis://user:pwd@host:port` to use an external Redis.
* MCP protected fields need no extra setup: mask tokens are kept in the same
  PostgreSQL and the fingerprint key is derived from `SECRET_KEY`. Optionally set
  `JADAWEL_MCP_PROTECTION_REDIS_URL` for a dedicated Redis vault, or an explicit
  `JADAWEL_MCP_PROTECTION_FINGERPRINT_KEYS` keyring with
  `JADAWEL_MCP_PROTECTION_ACTIVE_KEY_ID` to rotate keys independently of
  `SECRET_KEY`. Protection is on by default (`FEATURE_FLAGS=mcp-protected-fields-staff`
  restricts it to staff). `GET /api/arabase/mcp/protection/readiness/` reports the state.

> There is a security flaw with docker and the ufw firewall.
> By default docker when exposing ports on 0.0.0.0 will bypass any ufw firewall rules
> and expose the above container publicly from your machine on its network. If this
> is not intended then run with the following ports instead:
> `-p 127.0.0.1:80:80 -p 127.0.0.1:443:443` which makes your Jadawel only accessible
> from the machine it is running on.
> Please see https://github.com/chaifeng/ufw-docker for more information and how to
> setup ufw to work securely with docker.

## Image Feature Overview

The `jadawel/jadawel:2.2.2` image by default runs all of Jadawel's various services in
a single container for maximum ease of use.

> This image is designed for simple single server deployments or simple container
> deployment services such as Google Cloud Run.
>
> If you are instead looking for images which are better suited for horizontal
> scaling (e.g. when using Kubernetes) then please instead use the separate
> `jadawel/backend` and `jadawel/web-frontend` images, which deploy each Jadawel
> service in its own container independently.

A quick summary of its features are:

* Runs a Postgres database and Redis server by default internally and stores all data in
  the `/jadawel/data` folder inside the container.
* Set `DATABASE_URL` or the `DATABASE_...` variables to disable the internal postgres
  and instead connect to an external Postgres. This is highly recommended for any
  production deployments of this image, so you can easily connect to the Postgres
  database from any other services or processes you might have.
* Set `REDIS_URL` or the `REDIS_...` variables to disable the internal redis and instead
  connect to an external Postgres.
* Runs all services behind a pre-configured Caddy reverse proxy. Set
  `JADAWEL_CADDY_ADDRESSES` to `https://YOUR_DOMAIN.com` and it will
  [automatically enable https](https://caddyserver.com/docs/automatic-https#overview)
  for
  you and store the keys and certs in `/jadawel/data/caddy`.
* Provides a CLI for execing admin commands against a running Jadawel container or
  running one off commands against just a Jadawel data volume.

## Upgrading from a previous version

1. It is recommended that you backup your data before upgrading, see the Backup sections
   below for more details on how to do this.
2. Stop your existing Jadawel container:

```bash
docker stop jadawel
```

3. Bump the image version in the `docker run` command you usually use to run your
   Jadawel and start up a brand-new container:

```bash
# We haven't yet deleted the old Jadawel container so you need to start this new one
# with a different name to prevent an error like:
# `response from daemon: Conflict. The container name "/jadawel" is already in use by
# container`

docker run \
  -d \
  --name jadawel_version_REPLACE_WITH_NEW_VERSION \
  # YOUR STANDARD ARGS HERE
  jadawel/jadawel:REPLACE_WITH_LATEST_VERSION
```

5. Jadawel will automatically upgrade itself on startup, follow the logs to monitor it:

```bash
docker logs -f jadawel_version_REPLACE_WITH_NEW_VERSION
```

6. Once you see the following log line your Jadawel upgraded and is now available again:

```
[JADAWEL-WATCHER][2022-05-10 08:44:46] Jadawel is now available at ...
```

7. Make sure your Jadawel has been successfully upgraded by visiting it and checking
   everything is working as expected and your data is still present.
8. If everything works you can now remove the old Jadawel container.

> WARNING: If you have not been using a volume to persist the `/jadawel/data` folder
> inside the container this will delete all of your Jadawel data stored in this
> container permanently.

```bash
docker rm jadawel
```

## Upgrading PostgreSQL database from a previous version

> NOTE: this section only applies if your data directory was originally created by
> an old upstream Jadawel release running PostgreSQL 11. The
> `baserow/baserow-pgautoupgrade` and `baserow/baserow-pg11` images referenced below
> are published by upstream Jadawel and have no Jadawel equivalent, so those image
> names are deliberately left unchanged.

On November 2023 [PostgreSQL released](https://www.postgresql.org/about/news/postgresql-161-155-1410-1313-1217-and-1122-released-2749/) a final update for version 11 of the database together with an end-of-life notice for this version. This means, that PostgreSQL 11 will no longer receive security and bug fixes.

If you are using an embedded PostgreSQL database (an embedded one is when you do _not_ provide `POSTGRESQL_*` environment variables when launching Jadawel, as opposed to an external one, where you provide connection details to your external PostgreSQL instance), and if you restart or try to run a new Jadawel instance, if your data was initialized with PostgreSQL version 11, you'll notice that it doesn't start up anymore and raises an error because you need to upgrade your data directory to be compatible with PostgreSQL version 15. Upstream Jadawel provides an image to automatically upgrade your data directory to PostgreSQL version 15, which is now the version officially supported by Jadawel.

If you don't want to upgrade at this point in time, jump to [Legacy PostgreSQL version](#legacy-postgresql-version) section below. Although, be aware, that we will only support PostgreSQL 11 for a limited amount of time and that this version won't receive official updates from PostgreSQL anymore.

### Upgrade process

To upgrade your data directory to be compatible with PostgreSQL 15, follow these steps:

**CAUTION:** before doing this, make sure to [Back up your Jadawel instance](#backing-up-and-restoring-jadawel) to avoid potential data loss.

1. Make sure there are no Jadawel instances running with `docker ps`. If Jadawel is running, stop the container with `docker stop jadawel`.
2. Run this command to run a Docker image which will automatically update your data directory to be compatible with PostgreSQL version 15:

```
docker run \
  --name jadawel-pgautoupgrade \
  # ALL THE ARGUMENTS YOU NORMALLY ADD TO YOUR JADAWEL INSTANCE
  --restart no \
  baserow/baserow-pgautoupgrade:1.30.1
```

3. If the upgrade was successful, the container should exit with a success message, you can now start Jadawel as you did before.
4. If the upgrade wasn't successful, the upgrade image should output verbose logs of where exactly it failed. In that case, copy all of the log output and open an issue on the project repository for further assistance.

### Legacy PostgreSQL version

Starting from January 1, 2025, we will no longer create new images with PostgreSQL 11. If you are using the embedded PostgreSQL version in a Jadawel version before 1.30 and want to upgrade to the latest version, you must first use the latest `pgautoupgrade` image to upgrade PostgreSQL to version 15, and then upgrade to the latest version of Jadawel. If you do not wish to upgrade PostgreSQL, version 1.30.1 is the last image we provide with PostgreSQL 11, but it will not receive any updates.

To run the latest upstream Jadawel image that uses the legacy PostgreSQL 11 version, use the following command:

```
docker run \
  --name jadawel-pg11 \
  # ALL THE ARGUMENTS YOU NORMALLY ADD TO YOUR JADAWEL INSTANCE
  --restart unless-stopped \
  baserow/baserow-pg11:1.30.1
```

## Example Commands

See [Configuring Jadawel](../../docs/CONFIGURATION.md) for more detailed information on all the
other environment variables you can configure.

### Using a Domain with automatic https

If you have a domain name and have correctly configured DNS then you can run the
following command to make Jadawel available at the domain with
[automatic https](https://caddyserver.com/docs/automatic-https#overview) provided by
Caddy.

> Append `,http://localhost` to JADAWEL_CADDY_ADDRESSES if you still want to be able to
> access your server from the machine it is running on using http://localhost. See
> [Caddy's Address Docs](https://caddyserver.com/docs/caddyfile/concepts#addresses)
> for all supported values for JADAWEL_CADDY_ADDRESSES.

```bash
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=https://www.REPLACE_WITH_YOUR_DOMAIN.com \
  -e JADAWEL_CADDY_ADDRESSES=:443 \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

### Behind a reverse proxy already handling ssl

```bash
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=https://www.yourdomain.com \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

### On a nonstandard HTTP port

```bash
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=https://www.yourdomain.com:3001 \
  -v jadawel_data:/jadawel/data \
  -p 3001:80 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

### With an external PostgresSQL server

```bash
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=https://www.yourdomain.com \
  -e DATABASE_HOST=TODO \
  -e DATABASE_NAME=TODO \
  -e DATABASE_USER=TODO \
  -e DATABASE_PASSWORD=TODO \
  -e DATABASE_PORT=TODO \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

### With an external Redis server

```bash
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=https://www.yourdomain.com \
  -e REDIS_HOST=TODO \
  -e REDIS_USER=TODO \
  -e REDIS_PASSWORD=TODO \
  -e REDIS_PORT=TODO \
  -e REDIS_PROTOCOL=TODO \
  -e REDIS_SSL_CERT_REQS=TODO \
  -e REDIS_SSL_CA_CERTS=TODO \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

### With an external email server

```bash
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=https://www.yourdomain.com \
  -e EMAIL_SMTP=True \
  -e EMAIL_SMTP_HOST=TODO \
  -e EMAIL_SMTP_PORT=TODO \
  -e EMAIL_SMTP_USER=TODO \
  -e EMAIL_SMTP_PASSWORD=TODO \
  -e EMAIL_SMTP_USE_TLS= \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

### With a Postgresql server running on the same host as the Jadawel docker container

This is assuming you are using the postgresql server bundled by ubuntu. If not then you
will have to find the correct locations for the config files for your OS.

1. Find out what version of postgresql is installed by running
   `sudo ls /etc/postgresql/`
2. Open `/etc/postgresql/YOUR_PSQL_VERSION/main/postgresql.conf` for editing as root
3. Find the commented out `# listen_addresses` line.
4. Change it to be:
   `listen_addresses = '*'          # what IP address(es) to listen on;`
5. Open `/etc/postgresql/YOUR_PSQL_VERSION/main/pg_hba.conf` for editing as root
6. Add the following line to the end which will allow docker containers to connect.
   `host    all             all             172.17.0.0/16           md5`
7. Restart postgres to load in the config changes.
   `sudo systemctl restart postgresql`
8. Check the logs do not have errors by running
   `sudo less /var/log/postgresql/postgresql-YOUR_PSQL_VERSION-main.log`
9. Run Jadawel like so:

```bash
docker run \
  -d \
  --name jadawel \
  --add-host host.docker.internal:host-gateway \
  -e JADAWEL_PUBLIC_URL=http://localhost \
  -e DATABASE_HOST=host.docker.internal \
  -e DATABASE_PORT=5432 \
  -e DATABASE_NAME=YOUR_DATABASE_NAME \
  -e DATABASE_USER=YOUR_DATABASE_USERNAME \
  -e DATABASE_PASSWORD=REPLACE_WITH_YOUR_DATABASE_PASSWORD \
  --restart unless-stopped \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  jadawel/jadawel:2.2.2
```

### Supply secrets using files

The `DATABASE_PASSWORD`, `SECRET_KEY` and `REDIS_PASSWORD` environment variables can
instead be loaded using a file by using the `*_FILE` variants:

```bash
echo "your_redis_password" > .your_redis_password
echo "your_secret_key" > .your_secret_key
echo "your_pg_password" > .your_pg_password
docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=http://localhost \
  -e REDIS_PASSWORD_FILE=/jadawel/.your_redis_password \
  -e SECRET_KEY_FILE=/jadawel/.your_secret_key \
  -e DATABASE_PASSWORD_FILE=/jadawel/.your_pg_password \
  -e EMAIL_SMTP_PASSWORD_FILE=/jadawel/.your_smtp_password \
  --restart unless-stopped \
  -v $PWD/.your_redis_password:/jadawel/.your_redis_password \
  -v $PWD/.your_secret_key:/jadawel/.your_secret_key \
  -v $PWD/.your_pg_password:/jadawel/.your_pg_password \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  jadawel/jadawel:2.2.2
```

### Start just the embedded database

If you want to directly access the embedded Postgresql database then you can run:

```bash
docker run -it \
  --rm \
  --name jadawel \
  -p 5432:5432 \
  -v jadawel_data:/jadawel/data \
  jadawel/jadawel:2.2.2 \
  start-only-db
# Now get the password from
docker exec -it jadawel cat /jadawel/data/.pgpass
# Finally connect on your host machine to the Jadawel postgres database at port 5432
# the password above with the username `jadawel`.
```

## Application builder domains

The build in Caddy server is configured to automatically handle additional application
builder domains. Depending on the environment variables, it will also automatically
fetch SSL certificates for those domains. Note that the `JADAWEL_CADDY_ADDRESSES`
environment variable must be `:80` or `:443` to allow multiple domains. If you have set
a URL there, it won't work.

By default, it will accept requests of any domain over the http protocol, which is
perfect if you have a proxy in front of Jadawel. If `JADAWEL_CADDY_ADDRESSES` starts
with `https` protocol or is `:443`, then it will redirect http requests to https, and
will handle the SSL certificate part automatically. This is recommended when the
container is directly exposed to the internet.

### Run a one off command on the database

If you want to run a one off backend command against your Jadawel data volume without
starting Jadawel normally you can do so with the `backend-cmd-with-db` argument like so:

```bash
docker run -it \
  --rm \
  --name jadawel \
  -v jadawel_data:/jadawel/data \
  jadawel/jadawel:2.2.2 \
  backend-cmd-with-db manage dbshell
```

## Stateless Deployment for Horizontal Scaling

This image can also be configured to deploy Jadawel in a horizontally scalable way.
We recommend you first consider using the `jadawel/backend` and `jadawel/web-frontend`
single service per container images on Kubernetes via the
[Helm chart](../helm/jadawel/README.md).
However, if you just want to easily horizontally scale Jadawel on something like
AWS ECS or Google Cloud Run then the `jadawel/jadawel` image can be used.

### Prerequisites

To deploy this image in a horizontally scalable way you need to ensure all state is
stored externally and not inside containers or volumes. To do this you will need a:

1. A PostgreSQL database
2. A Redis server
3. One of the following services to upload and download user files from:
    1. AWS S3 or compatable service
    2. Google Cloud Storage
    3. Azure Cloud Storage bucket
    4. Some sort of a shared volume that can be mounted into every single container

### Recommended Environment Variables

With this image we recommend you set the following environment variables to scale it
horizontally.

> See the [Configuration docs](../../docs/CONFIGURATION.md) for
> more details on the following environment variables.

1. All relevant `DATABASE_*` env vars need to be set to point Jadawel at an external
   postgres
2. All relevant `REDIS_*` env vars need to be set to point Jadawel at an external redis
3. `DISABLE_VOLUME_CHECK=yes` needs to be set as this image has a
   check for less technical users that `/jadawel/data` is mounted to an external
   volume on startup. Instead, you want your containers to be stateless and so this
   check needs to be disabled.
4. `AWS_*/GC_*/AZURE_*` env vars need to be set connecting Jadawel to an external
   file storage service.
    1. **Important** The URLs of files uploaded to these buckets needs to be accessible
       directly from browser of your Jadawel users.
5. Ensure the containers always have CPU time allocated as they have periodic
   background tasks triggered by an internal CRON service.

### Scaling Options

This image has the following "horizontal scaling" environment variables:

1. `JADAWEL_AMOUNT_OF_GUNICORN_WORKERS` this controls the number of REST API
   workers (the things that do most of the API work) per container.
2. `JADAWEL_AMOUNT_OF_WORKERS` controls the number of background task celery
   runners, these run realtime collaboration tasks, cleanup jobs and other slow tasks
   like big file exports/imports.
    1. If you are scaling many of these containers you probably only need one or two
       of these background workers per container as they will all pool together and
       collect background tasks submitted from any other container via Redis.
3. You can make the image launch fewer internal processes and hence reduce memory usage
   by setting `JADAWEL_RUN_MINIMAL=yes` AND `JADAWEL_AMOUNT_OF_WORKERS=1`.
    1. This will cause this image to only launch a single celery task
       process which handles both the fast and slow queues. The consequence of this is
       that there is only one process handling tasks per container and so a slow task
       such as a snapshot of a large Jadawel database might delay a fast queue task
       like sending a realtime row updated signal to all users looking at a table.

## Backing up and Restoring Jadawel

Jadawel stores all of its persistent data in the `/jadawel/data` directory by default.
We strongly recommend you mount a docker volume into this location to persist Jadawels
data so you do not lose it if you accidentally delete your Jadawel container.

> The backup and restore operations discussed below are best done on a Jadawel server
> which is not being used.

### Backup all of Jadawel

Note, that this only works if you're not using an external PostgreSQL server. This will backup:

1. Jadawels postgres database (This will be a raw copy of the PGDATA dir and hence not
   easily portable, see the section below on how to backup just the postgres db in a
   more portable way.)
2. The Caddy config and data, this will include any runtime config changes you might
   have made to the caddy server and any SSL certificates/keys automatically setup by
   Caddy.
3. The Redis servers state. This is not strictly needed.
4. This will backup user-uploaded files as well, but only if you've not configured external file storage.

Otherwise if you remove the Jadawel container you will lose all of your data.

The command below assumes you have been running Jadawel with the
`-v jadawel_data:/jadawel/data` volume. Please change this argument accordingly if you
have mounted the /jadawel/data folder differently.

```bash
# Ensure Jadawel is stopped first before taking a backup.
docker stop jadawel
docker run --rm -v jadawel_data:/jadawel/data -v $PWD:/backup ubuntu tar cvf /backup/backup.tar /jadawel/data
```

### Restore all of Jadawel

```bash
# Ensure Jadawel is stopped first before taking a backup.
docker stop jadawel
docker run --rm -v jadawel_data:/jadawel/data -v $PWD:/backup ubuntu tar cvf /backup/backup.tar /jadawel/data
docker run --rm -v new_jadawel_data_volume:/results -v $PWD:/backup ubuntu bash -c "mkdir -p /results/ && cd /results && tar xvf /backup/backup.tar --strip 2"
# Now launch Jadawel using the new data volume with your normal run command:
docker run -v new_jadawel_data_volume:/jadawel/data .....
```

### Backup only Jadawel's Postgres database

Please ensure you only back-up a Jadawel database which is not actively being used by a
running Jadawel instance or any other process which is making changes to the database.

Jadawel stores all of its own data in Postgres. To backup just this database you can run
the command below.

```bash
# First read the help message for this command
docker run -it --rm -v jadawel_data:/jadawel/data jadawel/jadawel:2.2.2 \
   backend-cmd-with-db backup --help

# Stop Jadawel instance
docker stop jadawel

# The command below backs up Jadawel to the backups folder in the jadawel_data volume:
docker run -it --rm -v jadawel_data:/jadawel/data jadawel/jadawel:2.2.2 \
   backend-cmd-with-db backup -f /jadawel/data/backups/backup.tar.gz

# Or backup to a file on your host instead run something like:
docker run -it --rm -v jadawel_data:/jadawel/data -v $PWD:/jadawel/host \
   jadawel/jadawel:2.2.2 backend-cmd-with-db backup -f /jadawel/host/backup.tar.gz
```

### Restore only Jadawel's Postgres Database

When restoring Jadawel you must ensure you are restoring into a brand new Jadawel data
volume.

```bash
# Stop Jadawel instance
docker stop jadawel

# Restore Jadawel backup from a new volume containing the backup:
docker run -it --rm \
  -v old_jadawel_data_volume_containing_the_backup_tar_gz:/jadawel/old_data \
  -v new_jadawel_data_volume_to_restore_into:/jadawel/data \
  jadawel/jadawel:2.2.2 backend-cmd-with-db restore -f /jadawel/old_data/backup.tar.gz

# Or to restore from a file on your host instead run something like:
docker run -it --rm \
  -v jadawel_data:/jadawel/data -v \
  $(pwd):/jadawel/host \
  jadawel/jadawel:2.2.2 backend-cmd-with-db restore -f /jadawel/host/backup.tar.gz
```

## Running healthchecks on Jadawel

The Dockerfile already defines a HEALTHCHECK command which will be used by software that
supports it. However if you wish to trigger a healthcheck yourself on a running Jadawel
container then you can run:

```bash
docker exec jadawel ./jadawel.sh backend-cmd backend-healthcheck
# Run the below to see all available healthchecks
docker exec jadawel ./jadawel.sh backend-cmd help
```

## Running Jadawel or Django management commands

You can run management commands on an existing Jadawel container called jadawel by
running the following to see the available commands:

```bash
docker exec jadawel ./jadawel.sh backend-cmd manage
# For example you could migrate the database of a running Jadawel using:
docker exec jadawel ./jadawel.sh backend-cmd manage migrate
```

## Customizing Jadawel

### Mounting in a config file

Jadawel will automatically source any `.sh` files found in `/jadawel/supervisor/env/` or
`/jadawel/data/env/` on startup. Use this to create a single config file to configure
your Jadawel like so:

```bash
custom_jadawel_conf.sh << EOF
export JADAWEL_PUBLIC_URL=todo
export JADAWEL_CADDY_ADDRESSES=todo

# You can perform any Bash logic required in here to setup Jadawel conditionally.
EOF

docker run \
  -d \
  --name jadawel \
  -e JADAWEL_PUBLIC_URL=http://localhost \
  -v $PWD/custom_jadawel_conf.sh /jadawel/supervisor/custom_jadawel_conf.sh \
  -v jadawel_data:/jadawel/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  jadawel/jadawel:2.2.2
```

Or you can just store it directly in the volume at `jadawel_data/env` meaning it will be
loaded whenever you mount in this data volume.

### Building your own image from Jadawel

```dockerfile
FROM jadawel/jadawel:2.2.2

# Any .sh files found in /jadawel/supervisor/env/ will be sourced and loaded at startup
# useful for storing your own environment variable overrides.
COPY custom_env.sh /jadawel/supervisor/env/custom_env.sh

# Set the DATA_DIR environment variable to change where Jadawel stores its persistent
# data. At startup Jadawel will attempt to chown and setup this folder correctly.
ENV DATA_DIR=/jadawel/data

# This image bakes in its own default user with UID/GID of 9999:9999 by default. To
# Set this to change the user Jadawel will run its Caddy, backend, Celery and
# web-frontend services as. However be warned, the default entrypoint needs to be run
# as root so using USER may break things.
ENV DOCKER_USER=jadawel_docker_user
```

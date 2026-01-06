### Docker quick notes

Build and run with Docker Compose:

```bash
docker compose up --build
```

The app listens on port `8000` by default (http://localhost:8000).

Environment variables you may want to set in your compose file:
- `TONERTRACK_DATA_DIR` — path for `printers.json` and audit log
- `TONERTRACK_PRINT_SERVERS` — comma-separated Windows print servers
- `TONERTRACK_PRINT_SERVER_VIEWS` — mapping of server→view (e.g. `\\dc3=B2,\\dc4=B1`)
- `TONERTRACK_PRINT_SYNC_INTERVAL` — automatic sync interval (seconds)

If you must target a specific platform for cloud builds:

```bash
docker build --platform=linux/amd64 -t tonertrack:v2 .
```

Push to your registry as usual and consult Docker docs for registry auth.

Reference: https://docs.docker.com/language/python/
### Building and running your application

When you're ready, start your application by running:
`docker compose up --build`.

Your application will be available at http://localhost:8000.

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)
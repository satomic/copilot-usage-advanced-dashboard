
# Special Notes
Everything described in this article is based on the all-in-one architecture. In a production environment, it can be split into a distributed architecture based on actual needs.

## Architecture diagram

![](/image/image_oZJ-KGOxa5.png)

## Technology stack

Dependent technology stack:

- VM
- docker
- Elasticsearch&#x20;
- Grafana
- Python3

***

# Deployment

> All operations are performed in the VM

## Prerequisites

> everything is on-premises and free (except VM)

The only thing you need is:

- a VM
  - Memory: 16G is recommended
  - Operating system: Ubuntu 22.04 (recommended, other operating systems have no difference except Docker installation)
  - Port: `3000` port needs to be released for Grafana to use, and `22` port can be determined by yourself.

Everything else is based on existing stuff, or based on open source software, no extra cost, for example:

- GitHub Organzations with Copilot enabled (I believe, you already have it)
- Docker (Community Version is enough)
- Elasticsearch (Community Version is enough)
- Grafana (Community Version is enough, do not need Grafana Cloud Account)
- CPUAD-Updater build from this project (MIT license)

## Docker

For installation instructions, refer to [Install Docker Engine](https://docs.docker.com/engine/install/). For Ubuntu 22.04, you can use the following command

```bash
apt install docker.io
```

verify

```bash
docker version
```

The following content is obtained, indicating ok

```markdown
Client:
 Version:           24.0.7
 API version:       1.43
 Go version:        go1.21.1
 Git commit:        24.0.7-0ubuntu2~22.04.1
 Built:             Wed Mar 13 20:23:54 2024
 OS/Arch:           linux/amd64
 Context:           default

Server:
 Engine:
  Version:          24.0.7
  API version:      1.43 (minimum version 1.12)
  Go version:       go1.21.1
  Git commit:       24.0.7-0ubuntu2~22.04.1
  Built:            Wed Mar 13 20:23:54 2024
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          1.7.12
  GitCommit:
 runc:
  Version:          1.1.12-0ubuntu2~22.04.1
  GitCommit:
 docker-init:
  Version:          0.19.0
  GitCommit:

```

## Using existing images

Docker images for all app components are available in [GitHub container registry](https://github.com/satomic?tab=packages&repo_name=copilot-usage-advanced-dashboard):

- **Elastic Search** - `docker pull ghcr.io/satomic/copilot-usage-advanced-dashboard/elastic-search:main`
- **grafana** - `docker pull ghcr.io/satomic/copilot-usage-advanced-dashboard/grafana:main`
- **grafana-updater** - `docker pull ghcr.io/satomic/copilot-usage-advanced-dashboard/grafana-updater:main`
- **cpuad-updater** - `docker pull ghcr.io/satomic/copilot-usage-advanced-dashboard/cpuad-updater:main`

## Download source code

Put all the work in the `/srv` directory, click [download zip archive](https://github.com/satomic/copilot-usage-advanced-dashboard/archive/refs/heads/main.zip), unzip and rename the folder to `copilot-usage-advanced-dashboard`, or directly `git clone`

```bash
cd /srv
git clone https://github.com/satomic/copilot-usage-advanced-dashboard.git
cd copilot-usage-advanced-dashboard/src/cpuad-updater

```

verify

```bash
ls -ltr
```

The following content is obtained, indicating ok

```bash
total 84
-rw-r--r-- 1 root root   100 May 13 08:33 fetch.sh
-rw-r--r-- 1 root root    56 May 13 08:33 docker_build.sh
-rw-r--r-- 1 root root   754 May 13 08:33 create_es_indexes.sh
-rw-r--r-- 1 root root  1198 May 13 08:33 Dockerfile
-rw-r--r-- 1 root root  1195 May 13 08:33 log_utils.py
-rw-r--r-- 1 root root    68 May 13 08:33 requirements.txt
-rw-r--r-- 1 root root   193 May 13 08:33 push.sh
-rw-r--r-- 1 root root  5868 May 13 08:33 metrics_2_usage_convertor.py
-rw-r--r-- 1 root root     8 May 13 09:55 version
drwxr-xr-x 2 root root  4096 May 13 09:55 mapping
-rw-r--r-- 1 root root 33351 May 13 09:55 main.py
drwxr-xr-x 2 root root  4096 May 13 10:00 grafana
```

## Elasticsearch

### Installation

> If you already have ES, you can skip this step and go directly to the next step.

> ES will not be exposed to the outside of the VM, so there is no need to enable `xpack.security.enabled`

1. Create a data persistence directory and a configuration file directory for Elasticsearch:
   ```bash
   mkdir -p /srv/elasticsearch/data /srv/elasticsearch/config
   ```
2. Grant read and write permissions.
   ```bash
   chmod -R a+rw /srv/elasticsearch/
   ```
3. Create the `elasticsearch.yml` configuration file in the `/srv/elasticsearch/config/`directory:
   ```bash
   cat >> /srv/elasticsearch/config/elasticsearch.yml << EOF
   network.host: 0.0.0.0
   node.name: single-node
   cluster.name: es-docker-cluster
   path.data: /usr/share/elasticsearch/data
   path.logs: /usr/share/elasticsearch/logs
   discovery.type: single-node
   bootstrap.memory_lock: true
   EOF
   ```
4. Use the following command to start Elasticsearch and bind the data directory and configuration file:
   ```bash
   docker run -itd --restart always --name es \
     -p 9200:9200 \
     -e "xpack.security.enabled=false" \
     -e "ES_JAVA_OPTS=-Xms4g -Xmx4g" \
     -v /srv/elasticsearch/data:/usr/share/elasticsearch/data \
     -v /srv/elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro \
     docker.elastic.co/elasticsearch/elasticsearch:8.17.0

   ```
5. verify
   ```bash
   curl http://localhost:9200
   ```
   The following content is obtained, indicating ok
   ```bash
   {
       "name": "single-node",
       "cluster_name": "es-docker-cluster",
       "cluster_uuid": "oO3mfjYWTZ6VZFSClDiSLA",
       "version": {
           "number": "8.17.0",
           "build_flavor": "default",
           "build_type": "docker",
           "build_hash": "2b6a7fed44faa321997703718f07ee0420804b41",
           "build_date": "2024-12-11T12:08:05.663969764Z",
           "build_snapshot": false,
           "lucene_version": "9.12.0",
           "minimum_wire_compatibility_version": "7.17.0",
           "minimum_index_compatibility_version": "7.0.0"
       },
       "tagline": "You Know, for Search"
   }
   ```

### Create index

1. Confirm that you are in the correct path
   ```bash
   cd /srv/copilot-usage-advanced-dashboard/src/cpuad-updater
   ```
2. Execute the script and create an index
   ```bash
   export ELASTICSEARCH_URL="http://localhost:9200"
   bash create_es_indexes.sh
   ```
   The following content is obtained, indicating ok
   ```json
   {"acknowledged":true,"shards_acknowledged":true,"index":"copilot_usage_total"}
   {"acknowledged":true,"shards_acknowledged":true,"index":"copilot_usage_breakdown"}
   {"acknowledged":true,"shards_acknowledged":true,"index":"copilot_usage_breakdown_chat"}
   {"acknowledged":true,"shards_acknowledged":true,"index":"copilot_seat_info_settings"}
   {"acknowledged":true,"shards_acknowledged":true,"index":"copilot_seat_assignments"}
   ```
3. verify
   ```bash
   curl -X GET http://localhost:9200/_cat/indices?v
   ```
   The following content is obtained, indicating ok
   ```markdown
   health status index                        uuid                   pri rep docs.count docs.deleted store.size pri.store.size dataset.size
   yellow open   copilot_usage_total          XrOEfAngTS60VsuUz3Lbrw   1   1          0            0       227b           227b         227b
   yellow open   copilot_seat_info_settings   WtOBdBNUQRqua7wi7VANeQ   1   1          0            0       227b           227b         227b
   yellow open   copilot_seat_assignments     lK5t4SwASZizPQ_W4NX4KQ   1   1          0            0       227b           227b         227b
   yellow open   copilot_usage_breakdown      xE6tkg5GQEOP-EP8pwAkYg   1   1          0            0       227b           227b         227b
   yellow open   copilot_usage_breakdown_chat 6R_1cdlIQQOCv4BoHPqXCw   1   1          0            0       227b           227b         227b

   ```

## Grafana

### Installation

> If you already have Grafana, you can skip this step and go directly to the next step.

1. Creating a Data Path
   ```bash
   mkdir -p /srv/grafana/data
   chmod -R a+rw /srv/grafana/data
   ```
2. run
   ```bash
   docker run  -itd --restart always --name=grafana \
     --net=host \
     -p 3000:3000 \
     -v /srv/grafana/data:/var/lib/grafana \
     -e "GF_LOG_LEVEL=debug" \
     grafana/grafana:11.4.0
   ```
3. Access Grafana
   - Access address: `http://<PUBLIC_IP_OF_YOUR_VM>:3000`
   - The default username and password are `admin`/ `admin`, please change the password

### Create Admin Token

1. admin visit **Administration** → **Users and access** → **Service accounts**

   ![](/image/image_KY8b0hv5g1.png)
2. input **Display name**，**Role** select `Admin`, **Create**

   ![](/image/image_wjIjr2vLYJ.png)
3. click **Add service account token**

   ![](/image/image_tXLYRaldHa.png)
4. click **Generate token**

   ![](/image/image_B1twE5g-hS.png)
5. **Copy to clipboard and close**

   ![](/image/image_Ahoe1eqPzS.png)
6. Now, you have obtained your Grafana Token `"<your_grafana_token>"`, please save it and set it as an environment variable in the VM, which will be used in the next steps.
   ```bash
   export GRAFANA_TOKEN="<your_grafana_token>"
   ```

### Adding Data sources via API

1. Confirm that you are in the correct path
   ```bash
   cd /srv/copilot-usage-advanced-dashboard/src/cpuad-updater
   ```
2. run script, add data sources
   ```bash
   export GRAFANA_URL="http://localhost:3000"
   bash grafana/add_grafana_data_sources.sh
   ```
3. Visit the Grafana UI to confirm that the addition was successful

   ![](/image/image_data_source.png)

### Generate Dashboard Json Model

1. Confirm that you are in the correct path
   ```bash
   cd /srv/copilot-usage-advanced-dashboard/src/cpuad-updater
   ```
2. Execute the script to generate a Grafana json model. Execute one of the following two commands
   ```python
   # Generate Copilot Usage Advanced Dashboard
   python3 grafana/gen_grafana_model.py
   ```
   Get the output
   ```markdown
   Please import grafana/import-this-to-grafana-2025-05-13.json to Grafana
   Model saved to grafana/dashboard-model-2025-05-13.json, please import it to Grafana
   ``` 

### Import the generated Json to create a Dashboard

1. Download the generated file to your local computer
   ```bash
   scp root@<PUBLIC_IP_OF_YOUR_VM>:/srv/copilot-usage-advanced-dashboard/src/cpuad-updater/grafana/import-this-to-grafana-*.json .
   import-this-to-grafana-2024-12-17.json                                                                                                                                                  100%  157KB 243.8KB/s   00:00
   ```
2. Copy the generated json file and import it into Grafana

   ![](/image/image_AYrtVirvr1.png)

   Select the file to import, or paste the content directly

   ![](/image/image_w_wlgST2uO.png)
3. **Import**

   ![](/image/image_ojvK2wCe7i.png)
4. Congratulations, you now have a complete dashboard, but there should be no data yet. Next, run the core program.

## cpuad-updater

> is the abbreviation of the first characters of **Copilot Usage Advanced Dashboard Updater**

### Option 1. Run in docker mode (recommended)

Parameter description

- `GITHUB_PAT`:
  - Your GitHub account needs to have Owner permissions for Organizations.
  - [Create a personal access token (classic)](https://docs.github.com/en/enterprise-cloud@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) of your account with the `manage_billing:copilot`, `read:enterprise`, `read:org` scope. Then please replace `<YOUR_GITHUB_PAT>` with the actual PAT.
  - If you encounter PAT permission error, please **Allow access via fine-grained personal access tokens** in Organization's **Settings** - **Personal access tokens**.
- `ORGANIZATION_SLUGS`: The Slugs of all Organizations that you want to monitor, which can be one or multiple separated by `,` (English symbol). **If you are using Copilot Standalone, use your Standalone Slug here, prefixed with `standalone:`, for example `standalone:YOUR_STANDALONE_SLUG`**. Please replace `<YOUR_ORGANIZATION_SLUGS>` with the actual value. For example, the following types of values are supported:
  - `myOrg1`
  - `myOrg1,myOrg2`
  - `standalone:myStandaloneSlug`
  - `myOrg1,standalone:myStandaloneSlug`
- `LOG_PATH`: Log storage location, not recommended to modify. If modified, you need to modify the `-v` data volume mapping simultaneously.
- `EXECUTION_INTERVAL`: Update interval, the default is to update the program every `1` hours.
- `ELASTICSEARCH_URL`: The URL of your Elasticsearch, the default is `http://localhost:9200`, if you have modified the port, please modify it here.
- `TZ`: Timezone, the default is `GMT`, if you want to change it to your local timezone, please refer to [tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). For example, if you are in Toronto, please change it to `America/Toronto`.

```bash
docker run -itd \
--net=host \
--restart=always \
--name cpuad \
-e GITHUB_PAT="<YOUR_GITHUB_PAT>" \
-e ORGANIZATION_SLUGS="<YOUR_ORGANIZATION_SLUGS>" \
-e LOG_PATH="logs" \
-e EXECUTION_INTERVAL=1 \
-e ELASTICSEARCH_URL="http://localhost:9200" \
-e TZ="GMT" \  # change to your local timezone if needed
-v /srv/cpuad-updater-logs:/app/logs \
satomic/cpuad-updater
```

If your Elasticsearch instance requires authentication, pass include the `ELASTICSEARCH_USER` and `ELASTICSEARCH_PASS` environment variables.

```bash
-e ELASTICSEARCH_USER="elastic"
-e ELASTICSEARCH_PASS="mypassword"
```

### Option 2. Run in source code mode

1. Confirm that you are in the correct path
   ```bash
   cd /srv/copilot-usage-advanced-dashboard/src/cpuad-updater
   ```
2. Install Dependencies
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Setting Environment Variables. **If you are using Copilot Standalone, use your Standalone Slug here, prefixed with `standalone:`, for example `standalone:YOUR_STANDALONE_SLUG`**.
   ```bash
   export GITHUB_PAT="<YOUR_GITHUB_PAT>"
   export ORGANIZATION_SLUGS="<YOUR_ORGANIZATION_SLUGS>"
   export ELASTICSEARCH_URL="http://localhost:9200"
   export GRAFANA_URL="http://localhost:3000"
   ```
4. run
   ```bash
   python3 main.py
   ```
5. output logs
   ```text
   2024-12-17 05:32:22,292 - [INFO] - Data saved to logs/2024-12-17/nekoaru_level3-team1_copilot_usage_2024-12-17.json
   2024-12-17 05:32:22,292 - [INFO] - Fetched Copilot usage for team: level3-team1
   2024-12-17 05:32:22,293 - [INFO] - Data saved to logs/2024-12-17/nekoaru_all_teams_copilot_usage_2024-12-17.json
   2024-12-17 05:32:22,293 - [INFO] - Processing Copilot usage data for organization: nekoaru
   2024-12-17 05:32:22,293 - [INFO] - Processing Copilot usage data for team: level1-team1
   2024-12-17 05:32:22,293 - [WARNING] - No Copilot usage data found for team: level1-team1
   2024-12-17 05:32:22,293 - [INFO] - Processing Copilot usage data for team: level2-team1
   2024-12-17 05:32:22,293 - [WARNING] - No Copilot usage data found for team: level2-team1
   2024-12-17 05:32:22,293 - [INFO] - Processing Copilot usage data for team: level2-team2
   2024-12-17 05:32:22,293 - [WARNING] - No Copilot usage data found for team: level2-team2
   2024-12-17 05:32:22,293 - [INFO] - Processing Copilot usage data for team: level3-team1
   2024-12-17 05:32:22,293 - [WARNING] - No Copilot usage data found for team: level3-team1
   2024-12-17 05:32:22,293 - [INFO] - Sleeping for 6 hours before next execution...
   2024-12-17 05:32:22,293 - [INFO] - Heartbeat: still running...

   ```

***

# Congratulations

## Current application running status in the VM

At this moment, in the VM, you should be able to see 3 containers running (if you have deployed them from scratch based on docker), as follows:

```bash
docker ps

CONTAINER ID   IMAGE                                                  COMMAND                  CREATED        STATUS        PORTS                                                 NAMES
1edffd12a522   satomic/cpuad-updater:20241221                         "python3 main.py"        23 hours ago   Up 10 hours                                                         cpuad
b19e467d48f1   grafana/grafana:11.4.0                                 "/run.sh"                25 hours ago   Up 10 hours                                                         grafana
ee35b2a340f1   docker.elastic.co/elasticsearch/elasticsearch:8.17.0   "/bin/tini -- /usr/l…"   3 days ago     Up 10 hours   0.0.0.0:9200->9200/tcp, :::9200->9200/tcp, 9300/tcp   es
```

## View Dashboard

At this point, return to the Grafana page and refresh. You should be able to see the data.

![](/image/image_lf08iyNeUt.png)

or

![](/image/image_wjdhYnlwOZ.png)
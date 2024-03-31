# SIEM Query Utils


<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## Install

[![GitHub Actions Workflow
Status](https://img.shields.io/github/actions/workflow/status/wagov/nbdev-squ/deploy.yaml.svg?logo=github)](https://github.com/wagov/nbdev-squ/actions/workflows/deploy.yaml)
[![Python Packaging Index -
Version](https://img.shields.io/pypi/v/nbdev-squ.svg?logo=pypi)](https://pypi.org/project/nbdev-squ/)
[![OpenSSF
Scorecard](https://img.shields.io/ossf-scorecard/github.com/wagov/nbdev-squ.svg?label=openssf%20scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/wagov/nbdev-squ)

Below is how to install in a plain python 3.11+ environment

``` sh
pip install nbdev-squ
```

The installation can also be run in a notebook (we tend to use
[JupyterLab Desktop](https://github.com/jupyterlab/jupyterlab-desktop)
for local dev). The `SQU_CONFIG` env var indicates to nbdev_squ it
should load the json secret *squconfig-`my_keyvault_tenantid`* from the
`my_kevault_name` keyvault.

``` python
%pip install nbdev-squ
import os; os.environ["SQU_CONFIG"] = "{{ my_keyvault_name }}/{{ my_keyvault_tenantid }}" 

from nbdev_squ import api
# do cool notebook stuff with api
```

### Security considerations

The contents of the keyvault secret are loaded into memory and cached in
the
[user_cache_dir](https://platformdirs.readthedocs.io/en/latest/api.html#cache-directory)
which should be a temporary secure directory restricted to the single
user. Please ensure that the system this library is used on disallows
access and/or logging of the user cache directory to external locations,
and is on an encrypted disk (a common approach is to use isolated VMs
and workstations for sensitive activities).

## How to use

*Note: If you create/use a Github Codespace on any of the wagov repos,
SQU_CONFIG should be configured automatically.*

Before using, config needs to be loaded into `squ.core.cache`, which can
be done automatically from json in a keyvault by setting the env var
`SQU_CONFIG` to `"keyvault/tenantid"`.

``` bash
export SQU_CONFIG="{{ keyvault }}/{{ tenantid }}"
```

Can be done in python before import from nbdev_squ as well:

``` python
import os; os.environ["SQU_CONFIG"] = "{{ keyvault }}/{{ tenantid }}"
```

``` python
from nbdev_squ import api
import io, pandas

# Load workspace info from datalake blob storage
df = api.list_workspaces(fmt="df"); print(df.shape)

# Load workspace info from introspection of azure graph
df = api.list_securityinsights(); print(df.shape)

# Kusto query to Sentinel workspaces via Azure Lighthouse
df = api.query_all("SecurityIncident | take 20", fmt="df"); print(df.shape)

# Kusto queries to Sentinel workspaces via Azure Lighthouse (batches up to 100 queries at a time)
df = api.query_all(["SecurityAlert | take 20" for a in range(10)]); print(df.shape)

# Kusto query to ADX
#df = api.adxtable2df(api.adx_query("kusto query | take 20"))

# General azure cli cmd
api.azcli(["config", "set", "extension.use_dynamic_install=yes_without_prompt"])
print(len(api.azcli(["account", "list"])))

# Various pre-configured api clients

# RunZero
response = api.clients.runzero.get("/export/org/assets.csv", params={"search": "has_public:t AND alive:t AND (protocol:rdp OR protocol:vnc OR protocol:teamviewer OR protocol:telnet OR protocol:ftp)"})
pandas.read_csv(io.StringIO(response.text)).head(10)

# Jira
pandas.json_normalize(api.clients.jira.jql("updated > -1d")["issues"]).head(10)

# AbuseIPDB
api.clients.abuseipdb.check_ip("1.1.1.1")

# TenableIO
pandas.DataFrame(api.clients.tio.scans.list()).head(10)
```

``` python
badips_df = api.query_all("""
SecurityIncident
| where Classification == "TruePositive"
| mv-expand AlertIds
| project tostring(AlertIds)
| join SecurityAlert on $left.AlertIds == $right.SystemAlertId
| mv-expand todynamic(Entities)
| project Entities.Address
| where isnotempty(Entities_Address)
| distinct tostring(Entities_Address)
""", timespan=pandas.Timedelta("45d"))
```

``` python
df = api.query_all("find where ClientIP startswith '172.16.' | evaluate bag_unpack(pack_) | take 40000")
```

``` python
df = api.query_all("""union withsource="_table" *
| extend _ingestion_time_bin = bin(ingestion_time(), 1h)
| summarize take_any(*) by _table, _ingestion_time_bin
| project pack=pack_all(true)""")
```

``` python
import json
pandas.DataFrame(list(df["pack"].apply(json.loads)))
```

## Secrets template

The below json can be used as a template for saving your own json into
*`my_keyvault_name`/squconfig-`my_keyvault_tenantid`* to use with this
library:

``` json
{
  "config_version": "20240101 - added ??? access details",
  "datalake_blob_prefix": "https://???/???",
  "datalake_subscription": "???",
  "datalake_account": "???.blob.core.windows.net",
  "datalake_container": "???",
  "kql_baseurl": "https://raw.githubusercontent.com/???",
  "azure_dataexplorer": "https://???.???.kusto.windows.net/???",
  "tenant_id": "???",
  "jira_url": "https://???.atlassian.net",
  "jira_username": "???@???",
  "jira_password": "???",
  "runzero_apitoken": "???",
  "abuseipdb_api_key": "???",
  "tenable_access_key": "???",
  "tenable_secret_key": "???",
}
```

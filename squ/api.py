# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_api.ipynb.

# %% auto 0
__all__ = ['logger', 'list_workspaces', 'list_subscriptions', 'list_securityinsights', 'loganalytics_query']

# %% ../nbs/01_api.ipynb 3
from .core import *
from diskcache import memoize_stampede
from concurrent.futures import ThreadPoolExecutor
import pandas, json, logging

# %% ../nbs/01_api.ipynb 4
logger = logging.basicConfig(level=logging.INFO)

# %% ../nbs/01_api.ipynb 6
@memoize_stampede(cache, expire=60 * 60 * 3) # cache for 3 hours
def list_workspaces(fmt: str = "df", # df, csv, json, list
                    agency: str = "ALL"): # Agency alias or ALL
    path = datalake_path()
    df = pandas.read_csv((path / "notebooks/lists/SentinelWorkspaces.csv").open())
    df = df.join(pandas.read_csv((path / "notebooks/lists/SecOps Groups.csv").open()).set_index("Alias"), on="SecOps Group", rsuffix="_secops")
    df = df.rename(columns={"SecOps Group": "alias", "Domains and IPs": "domains"})
    df = df.dropna(subset=["customerId"]).sort_values(by="alias")
    if agency != "ALL":
        df = df[df["alias"] == agency]
    if fmt == "df":
        return df
    elif fmt == "csv":
        return df.to_csv()
    elif fmt == "json":
        return df.fillna("").to_dict("records")
    elif fmt == "list":
        return list(df["customerId"].unique())
    else:
        raise ValueError("Invalid format")

# %% ../nbs/01_api.ipynb 9
@memoize_stampede(cache, expire=60 * 60 * 3) # cache for 3 hours
def list_subscriptions():
    return pandas.DataFrame(azcli(["account", "list"]))["id"].unique()

@memoize_stampede(cache, expire=60 * 60 * 3) # cache for 3 hours
def list_securityinsights():
    return pandas.DataFrame(azcli([
        "graph", "query", "--first", "1000", "-q", 
        """
        resources
        | where type =~ 'microsoft.operationsmanagement/solutions'
        | where name startswith 'SecurityInsights'
        | project wlid = tolower(tostring(properties.workspaceResourceId))
        | join kind=leftouter (
            resources | where type =~ 'microsoft.operationalinsights/workspaces' | extend wlid = tolower(id))
            on wlid
        | extend customerId = properties.customerId
        """
    ])["data"])

def loganalytics_query(query):
    dfs = []
    customerids = list_securityinsights()["customerId"]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(azcli, [
            "monitor", "log-analytics", "query",
            "-w", workspace,
            "--analytics-query", query
        ]) for workspace in customerids]
        for future, customerid in zip(futures, customerids):
            try:
                df = pandas.DataFrame(future.result())
            except Exception as e:
                logger.warning(e)
                continue
            else:
                if "TenantId" not in df.columns:
                    df["TenantId"] = customerid
                dfs.append(df)
    return pandas.concat(dfs)

import os
import re
import time

from pymongo import MongoClient
from pymongo.errors import OperationFailure


def set_replicaset(client: MongoClient, host_seeds_ip: dict, rs="rs0") -> None:
    """Set replica set."""
    members = []
    for i, v in zip(range(1, len(host_seeds_ip) + 1), host_seeds_ip.values()):
        members.append({"_id": i, "host": v["ip_port"], "priority": i * 10})
    config = {
        "_id": rs,
        "protocolVersion": 1,
        "version": 1,
        "members": members,
    }
    return client.admin.command("replSetInitiate", config)


def host_to_ip_address_dict(file_path="/etc/hosts") -> dict:
    """Build host to IP address dict for GitLab CI."""
    hosts = {}
    with open(file_path, "r") as f:
        for line in f:
            values = re.split(r"\s+", line.strip())
            if len(values) < 1:
                continue
            for name in values[1:]:
                hosts[name] = values[0]
    return hosts


def host_seeds_dict(host_seeds: str, port="27017") -> dict:
    """Build host seeds dict."""
    hosts = {}
    for value in host_seeds.split(","):
        entry = value.split(":")
        if len(entry) > 1:
            hosts[entry[0]] = {"host": entry[0], "port": entry[1]}
        else:
            hosts[entry[0]] = {"host": entry[0], "port": port}
    return hosts


def host_seeds_ip_dict(host_seeds_dict: dict, host_entries: dict) -> None:
    """Build host_seeds dict with IP."""
    hosts = {}
    for k, v in host_seeds_dict.items():
        entry = dict(v)
        entry["ip"] = host_entries[k]
        entry["ip_port"] = f"{host_entries[k]}:{entry['port']}"
        entry["host_port"] = f"{k}:{entry['port']}"
        hosts[k] = entry
    return hosts


def create_napps_user(client: MongoClient, user: str, pwd=None):
    """Create user"""
    return client.napps.command(
        "createUser", user, pwd=pwd, roles=[{"role": "dbAdmin", "db": "napps"}]
    )


def wait_until_first_node_is_primary(client: MongoClient) -> None:
    """Wait until first node is primary."""
    status = None
    while status != "PRIMARY":
        print(f"Waiting for the first node to be PRIMARY, current: {status}")
        response = client.admin.command("replSetGetStatus")
        status = response["members"][0]["stateStr"]
        time.sleep(3)
    print("First node stateStr is PRIMARY")


def write_host_seeds_file(
    hosts: dict, output_host_seeds_file="/tmp/host_seeds.txt"
) -> str:
    """Write host seeds file to export it as an env var on GitLab."""
    file_content = ",".join([value["ip_port"] for value in hosts.values()])
    with open(output_host_seeds_file, "w") as f:
        f.write(file_content)
    return file_content


def main() -> None:
    """Main."""
    host_seeds = os.environ["MONGO_HOSTS_PORTS"]
    host_entries = host_to_ip_address_dict()
    seeds = host_seeds_dict(host_seeds)
    output_host_seeds_file = "/tmp/host_seeds.txt"

    hosts = host_seeds_ip_dict(seeds, host_entries)
    print(f"Mapped hosts dict: {hosts}")

    first_node = next(iter(hosts.keys()))
    print(f"Running hello cmd on {first_node}")
    client = MongoClient(hosts[first_node]["host_port"], directConnection=True)
    print(client.db.command("hello"))

    print("Configuring replica set")
    response = set_replicaset(client, hosts)
    assert "ok" in response, response

    content = write_host_seeds_file(hosts, output_host_seeds_file)
    print(f"Wrote {content} to {output_host_seeds_file}")

    print(f"Waiting for node {first_node} to become primary")
    wait_until_first_node_is_primary(client)

    try:
        user, pwd = os.environ["MONGO_USERNAME"], os.environ["MONGO_PASSWORD"]
        print(f"Creating 'napps' user {user}")
        response = create_napps_user(client, user, pwd)
        assert "ok" in response, response
    except OperationFailure as exc:
        if "already exists" not in str(exc):
            raise


if __name__ == "__main__":
    main()

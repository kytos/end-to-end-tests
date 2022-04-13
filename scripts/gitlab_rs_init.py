import os
import re

from pymongo import MongoClient


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


def main() -> None:
    """Main."""
    host_seeds = os.environ["MONGO_HOSTS_PORTS"]
    host_entries = host_to_ip_address_dict()
    seeds = host_seeds_dict(host_seeds)
    output_host_seeds_file = "/tmp/host_seeds.txt"

    hosts = host_seeds_ip_dict(seeds, host_entries)
    print(f"Mapped hosts dict: {hosts}")

    first_node = next(iter(hosts.keys()))
    print(f"Trying to run hello cmd on {first_node}")
    client = MongoClient(hosts[first_node]["host_port"], directConnection=True)

    print(client.db.command("hello"))
    print("Trying to config replica set")
    print(set_replicaset(client, hosts))

    file_content = ",".join([value["ip_port"] for value in hosts.values()])
    with open(output_host_seeds_file, "w") as f:
        f.write(file_content)
    print(f"Wrote {file_content} to {output_host_seeds_file}")


if __name__ == "__main__":
    main()

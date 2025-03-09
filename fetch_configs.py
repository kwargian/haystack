from dataclasses import dataclass, field
import logging

from cloudvision.Connector.codec import Wildcard
from cloudvision.Connector.grpc_client import GRPCClient
from cloudvision.Connector.grpc_client import create_query


@dataclass
class DeviceInfo:
    hostname: str
    serial_number: str
    config: str = field(default=None)


def get_devices(client, include_inactive=False):
    """
    Get the list of devices from the analytics dataset at the /DatasetInfo/Devices path.
    A k/v at this path is a k of the device serial and v is a map that looks like this:

    {
      "mac": "de:ad:be:ef:de:ad",
      "status": "inactive",
      "hostname": "notreal",
      "modelName": "cEOSLab",
      "deviceType": "EOS",
      "domainName": "",
      "eosVersion": "4.33.1F",
      "sourceType": "",
      "displayName": "",
      "capabilities": [
        "all",
        "trafficPolicySupported"
      ],
      "isProvisioned": true,
      "softwareVersion": "4.33.1F",
      "terminAttrVersion": "v1.36.0",
      "primaryManagementIP": "192.168.1.1",
      "primaryManagementIPv6": ""
    }

    We want to pull hostname and device SN for any device marked as active.
    """

    # see create_query definition - first list in tuple is the path, second is the keys
    query = [create_query(pathKeys=[(["DatasetInfo", "Devices"], [])], dId="analytics")]

    devices = []
    for batch in client.get(query):
        for notif in batch["notifications"]:
            serial = list(notif["updates"])[0]
            hostname = notif["updates"][serial]["hostname"]
            if notif["updates"][serial]["status"] == "active" or include_inactive:
                devices.append(DeviceInfo(hostname=hostname, serial_number=serial))
    return devices


def get_config(client, device):
    """
    A device config is stored as a doubled-linked list of k/vs at /Config/running/lines in a device dataset.
    For our purposes, we don't care about the list structure, we just want to fetch the config as a string.
    This means we need to fetch all of the linked entries, find the head node, and traverse the list to rebuild the config as a string.

    Every entry has a k of the entry id, and a v of a map with the following keys:

    {
      "next": "6e2a1a0e-c8bb-4c9a-a0ef-f4f1f3ee5908",
      "text": "interface Ethernet2/4",
      "previous": "c3cf581f-2da1-47db-b386-58bb8d1d81d9"
    }

    Unfortunately, we don't store an empty `previous` key for the head node, the key is just ommitted.
    Same goes for the tail node, the `next` key is ommitted.
    """
    query = [create_query(pathKeys=[(["Config", "running", "lines"], [])], dId=device.serial_number)]

    config_lines = {}
    for batch in client.get(query):
        for notif in batch["notifications"]:
            logging.debug(f"Notif: {notif}")
            for entry in notif["updates"]:
                logging.debug(f"Entry: {entry}")
                node_id = entry  # mostly for my own sanity, no real need to rebind to a new var
                next = notif["updates"][node_id].get("next")
                previous = notif["updates"][node_id].get("previous")
                text = notif["updates"][node_id]["text"]
                logging.debug(f"Node ID: {node_id}, Next: {next}, Previous: {previous}, Text: {text}")
                config_lines[node_id] = {"next": next, "previous": previous, "text": text}
    else:
        logging.debug(f"Config lines: {config_lines}")

    # find the head node
    for node_id, node in config_lines.items():
        if config_lines[node_id].get("previous") is None:
            logging.debug(f"Head node: {node_id}")
            head_node = node_id
            break
    else:
        raise Exception("No head node found")

    # traverse the list to rebuild the config
    config = []
    current_node = head_node
    while current_node is not None:
        config.append(config_lines[current_node]["text"])
        current_node = config_lines[current_node].get("next")
    else:
        config = "\n".join(config)

    return config


def get_configs(apiserver, access_token, include_inactive=False):
    with GRPCClient(apiserver, token=access_token) as client:
        devices = get_devices(client, include_inactive)
        for device in devices:
            device.config = get_config(client, device)
            logging.debug(f"{device.hostname} config: {device.config}")

        return devices

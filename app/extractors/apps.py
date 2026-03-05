"""Extract installed apps from iOS backup."""
from app.backup.backup_reader import BackupReader


def extract_installed_apps(reader: BackupReader) -> list[dict]:
    """
    Extract installed apps list from the backup.

    Approach 1: From Manifest.db domains (AppDomain-<bundle_id>)
    Approach 2: From Manifest.plist Applications dict
    Approach 3: From Info.plist Installed Applications list
    """
    apps = {}

    # Approach 1: Manifest.db domains
    if reader._manifest_db:
        try:
            domains = reader.list_domains()
            for domain in domains:
                if domain.startswith("AppDomain-"):
                    bundle_id = domain[len("AppDomain-"):]
                    if bundle_id and bundle_id not in apps:
                        apps[bundle_id] = {
                            "bundle_id": bundle_id,
                            "name": _bundle_id_to_name(bundle_id),
                            "source": "manifest_db",
                        }
                elif domain.startswith("AppDomainGroup-"):
                    # App group containers
                    group_id = domain[len("AppDomainGroup-"):]
                    if group_id.startswith("group."):
                        # Extract likely bundle ID from group
                        parts = group_id.split(".")
                        if len(parts) >= 3:
                            bundle_id = ".".join(parts[1:])
                            if bundle_id not in apps:
                                apps[bundle_id] = {
                                    "bundle_id": bundle_id,
                                    "name": _bundle_id_to_name(bundle_id),
                                    "source": "manifest_db_group",
                                }
        except Exception:
            pass

    # Approach 2: Manifest.plist Applications
    manifest_apps = reader._manifest_plist_data.get("Applications", {})
    for bundle_id, app_data in manifest_apps.items():
        if bundle_id not in apps:
            name = ""
            if isinstance(app_data, dict):
                name = app_data.get(
                    "CFBundleDisplayName",
                    app_data.get("CFBundleName", ""),
                )
            apps[bundle_id] = {
                "bundle_id": bundle_id,
                "name": name or _bundle_id_to_name(bundle_id),
                "version": (
                    app_data.get("CFBundleShortVersionString", "")
                    if isinstance(app_data, dict)
                    else ""
                ),
                "source": "manifest_plist",
            }

    # Approach 3: Info.plist
    installed = reader._device_info.get("Installed Applications", [])
    for bundle_id in installed:
        if bundle_id not in apps:
            apps[bundle_id] = {
                "bundle_id": bundle_id,
                "name": _bundle_id_to_name(bundle_id),
                "source": "info_plist",
            }

    # Sort by display name
    result = sorted(apps.values(), key=lambda a: a.get("name", a["bundle_id"]).lower())
    return result


def _bundle_id_to_name(bundle_id: str) -> str:
    """
    Generate a display-friendly name from a bundle ID.
    e.g. "com.facebook.Messenger" -> "Messenger"
    """
    parts = bundle_id.split(".")
    if len(parts) >= 3:
        return parts[-1]
    return bundle_id

"""Constants for FTP Client tests."""

BACKUP_METADATA = {
    "addons": [],
    "backup_id": "23e64aec",
    "date": "2025-02-10T17:47:22.727189+01:00",
    "database_included": True,
    "extra_metadata": {},
    "folders": [],
    "homeassistant_included": True,
    "homeassistant_version": "2025.2.1",
    "name": "Automatic backup 2025.2.1",
    "protected": False,
    "size": 34519040,
}

MOCK_LIST_FILES = [
    (
        "backup/Automatic_backup_2025.2.1_2025-02-10_18.31_30202686.metadata.json",
        {
            "type": "file",
            "unix.mode": 384,
            "unix.links": "1",
            "unix.owner": "ftp",
            "unix.group": "ftp",
            "size": "359",
            "modify": "20250622142000",
        },
    ),
    (
        "backup/Automatic_backup_2025.2.1_2025-02-10_18.31_30202686.tar",
        {
            "type": "file",
            "unix.mode": 384,
            "unix.links": "1",
            "unix.owner": "ftp",
            "unix.group": "ftp",
            "size": "464332800",
            "modify": "20250622142000",
        },
    ),
]

import winreg
import wmi
import re
import uuid
import platform
import clr
import logging  # ログ設定のために必要
from logging import getLogger
import pythoncom

clr.AddReference("System.Net.NetworkInformation")
from System.Net.NetworkInformation import NetworkInterface

# ログ設定
logging.basicConfig(
    level=logging.INFO,  # ログレベルをINFOに設定
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # ログフォーマット
)
logger = getLogger(__name__)

# 依存ライブラリの確認 (wmi は Windows のみ)
if platform.system() == "Windows":
    try:
        import wmi
    except ImportError:
        logger.error("Error: The 'WMI' package is required.")
        logger.error("Please install it using: pip install WMI")
        exit()  # wmiがない場合は終了


class WirelessNIC:
    def __init__(self, name: str, mac: str, id: str):
        self.name = name
        self.mac = mac
        self.id = id

    def __repr__(self):
        return f"WirelessNIC(name={self.name}, mac={self.mac}, id={self.id})"

    def get_id_without_commas(self):
        """
        IDからカンマを除去した文字列を返す
        """
        return self.id.replace(",", "")


def reverse_guid_bytes(guid_string):
    """
    GUID文字列を受け取り、指定されたルールでバイト順を反転させ、
    レジストリの hex: 形式 (XX,XX,...) の文字列を返す。
    例: {01020304-0506-0708-0910-111213141516} ->
        04,03,02,01,06,05,08,07,09,10,11,12,13,14,15,16
    """
    try:
        # UUIDオブジェクトに変換してバイト列を取得
        guid_obj = uuid.UUID(guid_string)
        b = guid_obj.bytes

        # バイト順を反転 (最初の3ブロック)
        reversed_bytes = bytes(
            [
                b[3],
                b[2],
                b[1],
                b[0],  # 1番目のブロック反転
                b[5],
                b[4],  # 2番目のブロック反転
                b[7],
                b[6],  # 3番目のブロック反転
                b[8],
                b[9],
                b[10],
                b[11],
                b[12],
                b[13],
                b[14],
                b[15],  # 4, 5番目はそのまま
            ]
        )

        # バイト列を "XX,XX,..." 形式の16進数文字列に変換
        hex_string = ",".join(f"{byte:02X}" for byte in reversed_bytes)  # 大文字HEX
        return hex_string

    except (ValueError, AttributeError, TypeError) as e:
        # SettingIDがNoneや不正な形式の場合
        logger.info(f"Error processing GUID '{guid_string}': {e}")
        return None


def sanitize_description(description: str, setting_id: str) -> str:
    """
    アダプタの説明をサニタイズし、適切な名前を生成する。
    """
    sanitized = re.sub(r"[^\w]", "_", description).strip("_")
    return re.sub(r"_+", "_", sanitized) or f"adapter_{setting_id[:8]}"


def get_reversed_guid(setting_id: str) -> str | None:
    """
    GUID のバイト順を反転し、hex:形式の文字列を返す。
    """
    return reverse_guid_bytes(setting_id)


def get_wireless_adapters() -> list[WirelessNIC]:
    """
    Returns a list of wireless network adapters available on the system.
    """
    pythoncom.CoInitialize()
    if platform.system() != "Windows":
        logger.error("This script requires Windows and the WMI module.")
        return []

    try:
        c = wmi.WMI()
        adapter_configs = c.Win32_NetworkAdapterConfiguration()
    except wmi.x_wmi as e:
        logger.error(f"Error connecting to WMI or querying adapters: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during WMI query: {e}")
        return []

    if not adapter_configs:
        logger.error("No network adapters with IP enabled found.")
        return []

    net = NetworkInterface.GetAllNetworkInterfaces()
    wireless_adapters = []

    for adapter in adapter_configs:
        description = getattr(adapter, "Description", None)
        setting_id = getattr(adapter, "SettingID", None)
        mac_address = getattr(adapter, "MACAddress", "N/A")

        if not description or not setting_id or not mac_address:
            logger.info("Skipping adapter due to missing information.")
            continue

        is_wireless_adapter = any(
            setting_id == net[i].Id and net[i].NetworkInterfaceType.ToString() == "Wireless80211"
            for i in range(len(net))
        )

        if not is_wireless_adapter:
            continue

        sanitized_description = sanitize_description(description, setting_id)
        reversed_guid_hex = get_reversed_guid(setting_id)
        if reversed_guid_hex is None:
            logger.info(f"Skipping adapter {description} due to GUID processing error.")
            continue

        wireless_adapters.append(WirelessNIC(name=sanitized_description, mac=mac_address, id=reversed_guid_hex))

    return wireless_adapters


def get_selected_adapter() -> WirelessNIC | None:
    """
    Retrieves the currently selected wireless adapter from the registry.
    """
    try:
        with winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\icssvc\Settings"
        ) as key:
            data, _ = winreg.QueryValueEx(key, "PreferredPublicInterface")
            selected_adapter_id = data.hex().upper()
    except FileNotFoundError:
        logger.error("Registry key for PreferredPublicInterface not found.")
        return None
    except Exception as e:
        logger.error(f"Error reading registry: {e}")
        return None

    wireless_adapters = get_wireless_adapters()
    return next((adapter for adapter in wireless_adapters if adapter.get_id_without_commas() == selected_adapter_id), None)


def set_adapter(adapter: WirelessNIC):
    """
    Sets the given wireless adapter as the preferred public interface in the registry.
    """
    try:
        with winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\icssvc\Settings",
            access=winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(
                key,
                "PreferredPublicInterface",
                0,
                winreg.REG_BINARY,
                bytes.fromhex(adapter.get_id_without_commas()),
            )
    except Exception as e:
        logger.error(f"Error setting registry value: {e}")

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


def get_wireless_adapters() -> list[WirelessNIC] | None:
    pythoncom.CoInitialize()
    # Windows以外では動作しないことを確認
    if platform.system() != "Windows":
        logger.error("This script requires Windows and the WMI module.")
        return None

    # WMI接続を試みる
    try:
        c = wmi.WMI()
        # IPが有効なアダプター設定を取得 (wmic nicconfig get に相当)
        # SettingID が null でないものもフィルタリング
        adapter_configs = c.Win32_NetworkAdapterConfiguration()
    except wmi.x_wmi as e:
        logger.error(f"Error connecting to WMI or querying adapters: {e}")
        logger.error("Ensure the WMI service is running and you have permissions.")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during WMI query: {e}")
        return None

    if not adapter_configs:
        logger.error("No network adapters with IP enabled found or WMI query failed.")
        return None

    # ネットワークインターフェースの取得
    net = NetworkInterface.GetAllNetworkInterfaces()

    wireless_adapters = []

    # 各アダプターを処理
    for adapter in adapter_configs:
        # 必須情報の存在確認
        description = getattr(adapter, "Description", None)
        setting_id = getattr(adapter, "SettingID", None)
        mac_address = getattr(adapter, "MACAddress", "N/A")

        if not description or not setting_id or not mac_address:
            # Description や SettingID、 MACAddress がない場合はスキップ
            logger.info("Skipping adapter due to missing information.")
            continue

        is_wireless_adapter = False

        # Wireless80211 タイプのアダプターかどうかを確認
        for i in range(len(net)):
            if (
                setting_id == net[i].Id
                and net[i].NetworkInterfaceType.ToString() == "Wireless80211"
            ):
                is_wireless_adapter = True
                break

        # Wireless80211 タイプのアダプターのみを対象
        if not is_wireless_adapter:
            continue

        logger.info(f"Processing Adapter: {description} ({setting_id})")

        # サニタイズ (英数字とアンダースコア以外を置換)
        sanitized_description = re.sub(r"[^\w]", "_", description)
        # 連続するアンダースコアを1つにまとめる (任意)
        sanitized_description = re.sub(r"_+", "_", sanitized_description).strip("_")
        if not sanitized_description:  # サニタイズ後が空ならデフォルト名
            sanitized_description = f"adapter_{setting_id.replace('-', '')[:8]}"

        # GUIDのバイト順を反転し、hex:形式の文字列を取得
        reversed_guid_hex = reverse_guid_bytes(setting_id)

        if reversed_guid_hex is None:
            logger.info(
                f"Skipping adapter {description} due to GUID processing error."
            )
            continue

        wireless_adapter = WirelessNIC(name=sanitized_description, mac=mac_address, id=reversed_guid_hex)
        wireless_adapters.append(wireless_adapter)

    return wireless_adapters


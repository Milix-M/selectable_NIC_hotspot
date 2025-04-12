import wmi
import os
import re
import uuid
import platform
import clr
import logging  # ログ設定のために必要
from logging import getLogger

clr.AddReference("System.Net.NetworkInformation")
from System.Net.NetworkInformation import NetworkInterface


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


def main():
    # Windows以外では動作しないことを確認
    if platform.system() != "Windows":
        logger.error("This script requires Windows and the WMI module.")
        return

    # WMI接続を試みる
    try:
        c = wmi.WMI()
        # IPが有効なアダプター設定を取得 (wmic nicconfig get に相当)
        # SettingID が null でないものもフィルタリング
        adapter_configs = c.Win32_NetworkAdapterConfiguration()
    except wmi.x_wmi as e:
        logger.error(f"Error connecting to WMI or querying adapters: {e}")
        logger.error("Ensure the WMI service is running and you have permissions.")
        return
    except Exception as e:
        logger.error(f"An unexpected error occurred during WMI query: {e}")
        return

    if not adapter_configs:
        logger.error("No network adapters with IP enabled found or WMI query failed.")
        return

    # 出力ディレクトリの準備
    current_dir = os.getcwd()
    output_directory = os.path.join(current_dir, "reg")
    os.makedirs(output_directory, exist_ok=True)
    logger.info(f"Output directory: {output_directory}")

    # ネットワークインターフェースの取得
    net = NetworkInterface.GetAllNetworkInterfaces()

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

        logger.info(f"\nProcessing Adapter: {description} ({setting_id})")

        # ファイル名をサニタイズ (英数字とアンダースコア以外を置換)
        sanitized_description = re.sub(r"[^\w]", "_", description)
        # 連続するアンダースコアを1つにまとめる (任意)
        sanitized_description = re.sub(r"_+", "_", sanitized_description).strip("_")
        if not sanitized_description:  # サニタイズ後が空ならデフォルト名
            sanitized_description = f"adapter_{setting_id.replace('-', '')[:8]}"
        filename = os.path.join(output_directory, f"{sanitized_description}.reg")

        # GUIDのバイト順を反転し、hex:形式の文字列を取得
        reversed_guid_hex = reverse_guid_bytes(setting_id)

        if reversed_guid_hex is None:
            logger.info(
                f"Skipping adapter {description} due to GUID processing error."
            )
            continue

        # レジストリファイルの内容を作成
        # .regファイルの標準ヘッダーとWindows改行コード(\r\n)を使用
        reg_content = f"""Windows Registry Editor Version 5.00\r\n
\r\n[HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\icssvc\\Settings]\r\n"PreferredPublicInterface"=hex:{reversed_guid_hex}\r\n"""

        logger.info(
            f"Generating registry content:\n{reg_content.strip()}"
        )  # 確認用に出力

        # ファイルに書き込み (UTF-16 LE with BOM が .reg ファイルで一般的)
        try:
            with open(filename, "w", encoding="utf-16le") as f:
                # UTF-16 LE BOM (Byte Order Mark) を書き込む
                # Python 3.x の 'utf-16le' は自動でBOMを付与しないため手動で追加
                f.write("\ufeff")
                # レジストリ内容を書き込む
                f.write(reg_content)
            logger.info(f"Successfully wrote registry file: {filename}")
        except IOError as e:
            logger.warning(f"Error writing file {filename}: {e}")
        except Exception as e:
            logger.warning(
                f"An unexpected error occurred while writing file {filename}: {e}"
            )


if __name__ == "__main__":
    # ログ設定を追加
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
    main()
    logger.info("Script finished.")

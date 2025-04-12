import winreg

from adapter.nic_manager import WirelessNIC, get_wireless_adapters


def get_selected_adapter() -> WirelessNIC | None:
    """
    Get the selected adapter from the registry.
    """
    selected_adapter_id = None

    # レジストリからPreferredPublicInterfaceの値を取得
    with winreg.OpenKeyEx(
        winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\icssvc\Settings"
    ) as key:
        data, regtype = winreg.QueryValueEx(key, "PreferredPublicInterface")
        selected_adapter_id = data.hex().upper()

    # すべての無線アダプタを取得
    wireless_adapters = get_wireless_adapters()

    # 無線アダプタが取得できなかった場合はNoneで終了
    if wireless_adapters is None:
        return None
    # 取得した無線アダプタの中から、選択されたアダプタを探す
    else:
        for adapter in wireless_adapters:
            if adapter.get_id_without_commas() == selected_adapter_id:
                return adapter

    # 選択されたアダプタが見つからなかった場合はNoneを返す
    return None


def set_adapter(adapter: WirelessNIC):
    """
    Set the selected adapter in the registry.
    """
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


get_selected_adapter()

wireless_adapters = get_wireless_adapters()

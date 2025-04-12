import winreg

from nic_manager import WirelessNIC, get_wireless_adapters

def get_selected_adapter():
    """
    Get the selected adapter from the registry.
    """
    selected_adapter_id = None

    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\icssvc\Settings") as key:

        data, regtype = winreg.QueryValueEx(key, 'PreferredPublicInterface')
        selected_adapter_id = data.hex().upper()
        print(data.hex().upper())

    if selected_adapter_id:
        wireless_adapters = get_wireless_adapters()

        for i in range(len(wireless_adapters)):
            if wireless_adapters[i].get_id_without_commas() == selected_adapter_id:
                print(f"Selected adapter: {wireless_adapters[i].name}")
                break

def set_adapter(adapter: WirelessNIC):
    """
    Set the selected adapter in the registry.
    """
    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\icssvc\Settings", access=winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, 'PreferredPublicInterface', 0, winreg.REG_BINARY, bytes.fromhex(adapter.get_id_without_commas()))

get_selected_adapter()

wireless_adapters = get_wireless_adapters()
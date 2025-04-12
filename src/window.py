import flet as ft

from adapter.nic_manager import get_wireless_adapters, get_selected_adapter, set_adapter


def main(page: ft.Page):
    page.title = "MobileHotSpot NIC Selecter"  # タイトル
    page.window_width = 600  # 幅
    page.window_height = 300  # 高さ

    # 現在のadapterを取得する
    adapter = get_selected_adapter()

    # 現在のadapterが取得できなかった場合はNoneを代入する
    now_selected_adapter = adapter.name if adapter else "No adapter found"
    # 現在のadapterを表示するTextを作成する
    selected_adapter_text = ft.Text(now_selected_adapter)

    def __change_adapter(e):
        selected_option = adapter_dropdown.value
        wireless_adapters = get_wireless_adapters()
        option = next((adapter for adapter in wireless_adapters if adapter.name == selected_option), None)
        if option:
            set_adapter(option)

        adapter = get_selected_adapter()
        selected_adapter_text.value = adapter.name if adapter else "No adapter found"  # 現在のNICを更新
        page.update()  # ページを更新

    def __adapter_choices() -> list[ft.dropdown.Option]:
        """
        Adapter選択DropDownの選択肢を取得しlistで返却する
        """
        wireless_adapters = get_wireless_adapters()

        selectable_adapters = []

        if wireless_adapters:
            for adapter in wireless_adapters:
                selectable_adapters.append(ft.dropdown.Option(text=adapter.name))

        return selectable_adapters

    adapter_dropdown = ft.Dropdown(
        options=__adapter_choices(),
    )

    # 部品を配置する
    page.add(
        ft.Column(
            [
                ft.Text(
                    "MobileHotSpot NIC Selecter",
                    theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                ),
                ft.Divider(),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("現在のNIC: "),
                                selected_adapter_text,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                ft.Text("変更するNIC: "),
                                adapter_dropdown,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "NICを変更", on_click=__change_adapter
                                ),
                                ft.ElevatedButton("終了"),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=20,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


ft.app(target=main)

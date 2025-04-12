import flet as ft

from adapter.nic_manager import get_wireless_adapters, get_selected_adapter, set_adapter


def update_selected_adapter_text(selected_adapter_text, page):
    """
    現在選択されているアダプタのテキストを更新する。
    """
    adapter = get_selected_adapter()
    selected_adapter_text.value = adapter.name if adapter else "No adapter found"
    page.update()


def create_adapter_dropdown() -> ft.Dropdown:
    """
    アダプタ選択用のドロップダウンを作成する。
    """
    wireless_adapters = get_wireless_adapters()
    options = [ft.dropdown.Option(text=adapter.name) for adapter in wireless_adapters]
    return ft.Dropdown(options=options)


def main(page: ft.Page):
    page.title = "MobileHotSpot NIC Selecter"  # タイトル
    page.window_width = 600  # 幅
    page.window_height = 300  # 高さ

    # 現在のadapterを表示するTextを作成する
    selected_adapter_text = ft.Text()

    def __change_adapter(e):
        selected_option = adapter_dropdown.value
        wireless_adapters = get_wireless_adapters()
        option = next((adapter for adapter in wireless_adapters if adapter.name == selected_option), None)
        if option:
            set_adapter(option)
        update_selected_adapter_text(selected_adapter_text, page)

    def __exit_program(e):
        page.window.destroy()

    adapter_dropdown = create_adapter_dropdown()

    update_selected_adapter_text(selected_adapter_text, page)

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
                                ft.ElevatedButton("終了", on_click=__exit_program),
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

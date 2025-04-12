import flet as ft
from adapter.nic_manager import get_wireless_adapters, get_selected_adapter, set_adapter

class NICSelectorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "MobileHotSpot NIC Selecter"  # タイトル
        self.page.window_width = 600  # 幅
        self.page.window_height = 300  # 高さ

        # 現在のadapterを表示するTextを作成する
        self.selected_adapter_text = ft.Text()

        self.adapter_dropdown = self.create_adapter_dropdown()

        self.update_selected_adapter_text()

        # 部品を配置する
        self.page.add(
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
                                    self.selected_adapter_text,
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    ft.Text("変更するNIC: "),
                                    self.adapter_dropdown,
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "NICを変更", on_click=self.__change_adapter
                                    ),
                                    ft.ElevatedButton("終了", on_click=self.__exit_program),
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

    def update_selected_adapter_text(self):
        """
        現在選択されているアダプタのテキストを更新する。
        """
        adapter = get_selected_adapter()
        self.selected_adapter_text.value = adapter.name if adapter else "No adapter found"
        self.page.update()

    def create_adapter_dropdown(self) -> ft.Dropdown:
        """
        アダプタ選択用のドロップダウンを作成する。
        """
        wireless_adapters = get_wireless_adapters()
        options = [ft.dropdown.Option(text=adapter.name) for adapter in wireless_adapters]
        return ft.Dropdown(options=options)

    def __change_adapter(self, e):
        selected_option = self.adapter_dropdown.value
        wireless_adapters = get_wireless_adapters()
        option = next((adapter for adapter in wireless_adapters if adapter.name == selected_option), None)
        if option:
            set_adapter(option)
        self.update_selected_adapter_text()

    def __exit_program(self, e):
        self.page.window.destroy()
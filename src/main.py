from gui.nic_selector_app import NICSelectorApp
import flet as ft

def main(page: ft.Page):
    app = NICSelectorApp(page)

ft.app(target=main)
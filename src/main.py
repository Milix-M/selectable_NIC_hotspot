import flet as ft
from window import NICSelectorApp

def main(page: ft.Page):
    app = NICSelectorApp(page)

ft.app(target=main)
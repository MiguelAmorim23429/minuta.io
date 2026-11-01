// Em release, não abrir uma janela de consola adicional no Windows.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    minuta_io_lib::run()
}

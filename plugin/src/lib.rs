#![feature(extern_types)]
#![allow(clippy::missing_panics_doc)]
#![allow(clippy::unreadable_literal)]

pub mod consts;
pub mod defs;
pub mod hooks;

use std::{
    backtrace::Backtrace,
    panic::{self, PanicHookInfo},
};

use winsafe::{self as w, co, prelude::*};

fn panic_hook(info: &PanicHookInfo) {
    let backtrace = Backtrace::force_capture();
    let _ = w::HWND::NULL.MessageBox(
        &format!(
            "\
Error in the Randomushroom plugin!

{info}

stack backtrace:
{backtrace}"
        ),
        "Error in the Randomushroom plugin!",
        co::MB::ICONERROR,
    );
}

#[dllmain_rs::entry(events(process_attach, process_detach))]
fn on_lifecycle(reason: u32) {
    match reason {
        DLL_PROCESS_ATTACH => {
            panic::set_hook(Box::new(panic_hook));

            hooks::install();

            w::HWND::NULL
                .MessageBox(
                    "Hello from the Randomushroom plugin!",
                    "Hello!",
                    co::MB::ICONINFORMATION,
                )
                .unwrap();
        }
        DLL_PROCESS_DETACH => {
            hooks::uninstall();
        }
        _ => unreachable!(),
    }
}

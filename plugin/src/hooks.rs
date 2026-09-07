use std::{cell::RefCell, mem, sync::OnceLock};

use neohook::{DetourTransaction, Hook};
use winsafe::{self as w, co, prelude::*};

use crate::{
    consts::addr::{ADDRESS_BASE, FIND_OBJECT_OFFSET},
    defs::{CGame, CLevelObject},
};

thread_local! {
    pub static ACTIVE_HOOKS: RefCell<Vec<Hook>> = const { RefCell::new(Vec::new()) };
}

static ORIG_FIND_OBJECT: OnceLock<fn(*mut CGame, *mut CLevelObject)> = OnceLock::new();

extern "C" fn find_object_hook(game: *mut CGame, object: *mut CLevelObject) {
    w::HWND::NULL
        .MessageBox(
            &format!("find_object_hook before! {:#?}", unsafe { &*object }),
            "Hook",
            co::MB::ICONINFORMATION,
        )
        .unwrap();

    let original = ORIG_FIND_OBJECT.get().unwrap();
    original(game, object);

    w::HWND::NULL
        .MessageBox("find_object_hook after!", "Hook", co::MB::ICONINFORMATION)
        .unwrap();
}

#[allow(clippy::missing_transmute_annotations)]
pub fn install() {
    let mut session = DetourTransaction::begin();
    session.update_all_threads();

    let main_module_address = w::HINSTANCE::GetModuleHandle(None).unwrap().ptr();
    let main_module_base = unsafe { main_module_address.byte_sub(ADDRESS_BASE) };

    for (offset, detour, orig) in [
        (
            FIND_OBJECT_OFFSET,
            find_object_hook,
            Some(&ORIG_FIND_OBJECT),
        ),
    ] {
        let orig_fn = unsafe {
            mem::transmute(
                session
                    .attach(main_module_base.byte_add(offset).cast(), detour as _)
                    .unwrap(),
            )
        };
        if let Some(orig) = orig {
            orig.set(orig_fn).unwrap();
        }
    }

    let hooks = session.commit().unwrap();
    ACTIVE_HOOKS.set(hooks);
}

pub fn uninstall() {
    let _ = ACTIVE_HOOKS.try_with(|hooks| {
        let mut hooks = hooks.borrow_mut();
        for hook in hooks.drain(..) {
            hook.unhook().unwrap();
        }
    });
}
